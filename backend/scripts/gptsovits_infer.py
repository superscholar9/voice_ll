#!/usr/bin/env python
"""GPT-SoVITS cover inference wrapper (real runtime integration).

This script keeps the existing CLI contract used by backend/Celery while
switching conversion to GPT-SoVITS official TTS runtime APIs.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np
import soundfile as sf


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)
_FW_MODEL: Any = None


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _build_atempo_chain(rate_factor: float) -> str:
    if rate_factor <= 0:
        raise ValueError("rate_factor must be > 0")
    target = 1.0 / rate_factor
    filters: list[float] = []
    while target > 2.0:
        filters.append(2.0)
        target /= 2.0
    while target < 0.5:
        filters.append(0.5)
        target /= 0.5
    filters.append(target)
    return ",".join(f"atempo={f:.6f}" for f in filters)


def _normalize_language(raw: Optional[str]) -> str:
    if not raw:
        return "auto"
    code = raw.lower().strip()
    mapping = {
        "zh-cn": "zh",
        "zh-tw": "zh",
        "cmn": "zh",
        "yue": "yue",
        "en-us": "en",
        "en-gb": "en",
        "ja-jp": "ja",
    }
    code = mapping.get(code, code)
    allowed = {"auto", "auto_yue", "en", "zh", "ja", "yue", "ko", "all_zh", "all_ja", "all_yue", "all_ko"}
    return code if code in allowed else "auto"


def _fallback_text(lang: str) -> str:
    if lang.startswith("zh") or lang.startswith("yue"):
        return "你好。"
    if lang.startswith("ja"):
        return "こんにちは。"
    if lang.startswith("ko"):
        return "안녕하세요."
    return "Hello."


def _transcribe_with_faster_whisper(audio_path: Path) -> Optional[Tuple[str, str]]:
    global _FW_MODEL
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None

    device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES", "") != "" or os.path.exists("/dev/nvidia0") else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    logger.info("ASR(faster-whisper): %s device=%s", audio_path.name, device)

    if _FW_MODEL is None:
        _FW_MODEL = WhisperModel("small", device=device, compute_type=compute_type)

    segments, info = _FW_MODEL.transcribe(
        audio=str(audio_path),
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 700},
        language=None,
    )
    text = "".join(seg.text for seg in segments).strip()
    if not text:
        return None
    lang = _normalize_language(getattr(info, "language", None))
    return text, lang


def _transcribe_with_openai_whisper(audio_path: Path) -> Optional[Tuple[str, str]]:
    try:
        import whisper
    except Exception:
        return None

    logger.info("ASR(openai-whisper): %s", audio_path.name)
    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), language=None)
    text = (result.get("text") or "").strip()
    if not text:
        return None
    lang = _normalize_language(result.get("language"))
    return text, lang


def _transcribe_audio(audio_path: Path) -> Tuple[str, str]:
    for fn in (_transcribe_with_faster_whisper, _transcribe_with_openai_whisper):
        try:
            got = fn(audio_path)
        except Exception as exc:
            logger.warning("ASR failed via %s: %s", fn.__name__, exc)
            continue
        if got:
            text, lang = got
            logger.info("ASR ok (%s): lang=%s text=%s", fn.__name__, lang, text[:80].replace("\n", " "))
            return text, lang

    logger.warning("ASR unavailable for %s, using fallback text.", audio_path.name)
    return "Hello.", "en"


def _read_weight_json(project_root: Path) -> dict[str, Any]:
    path = project_root / "weight.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_path(project_root: Path, raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (project_root / p).resolve()


def _resolve_model_weights(project_root: Path, model_id: str) -> Tuple[Path, Path]:
    wanted = model_id.strip()
    if not wanted:
        raise RuntimeError("model_id is empty")

    weight_json = _read_weight_json(project_root)
    gpt_map = weight_json.get("GPT", {}) if isinstance(weight_json, dict) else {}
    sovits_map = weight_json.get("SoVITS", {}) if isinstance(weight_json, dict) else {}
    if wanted in gpt_map and wanted in sovits_map:
        gpt = _resolve_path(project_root, str(gpt_map[wanted]))
        sovits = _resolve_path(project_root, str(sovits_map[wanted]))
        if gpt.exists() and sovits.exists():
            return gpt, sovits

    trained_dir = project_root / "trained" / wanted
    if trained_dir.exists():
        gpt_files = sorted(trained_dir.glob("*.ckpt"), key=lambda p: p.stat().st_mtime, reverse=True)
        sovits_files = sorted(trained_dir.glob("*.pth"), key=lambda p: p.stat().st_mtime, reverse=True)
        if gpt_files and sovits_files:
            return gpt_files[0], sovits_files[0]

    gpt_candidates = sorted(
        [p for p in project_root.glob("GPT_weights*/**/*.ckpt") if wanted.lower() in p.name.lower()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    sovits_candidates = sorted(
        [p for p in project_root.glob("SoVITS_weights*/**/*.pth") if wanted.lower() in p.name.lower()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if gpt_candidates and sovits_candidates:
        return gpt_candidates[0].resolve(), sovits_candidates[0].resolve()

    raise RuntimeError(
        f"cannot resolve model_id={model_id!r}; expected key in weight.json, "
        "trained/<model_id>/, or matching files under GPT_weights*/SoVITS_weights*"
    )


def _load_gptsovits_model(project_root: Path, model_id: str) -> Any:
    logger.info("Loading GPT-SoVITS runtime, model_id=%s", model_id)
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "GPT_SoVITS"))

    try:
        from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    except Exception:
        from TTS_infer_pack.TTS import TTS, TTS_Config

    config_candidates = [
        project_root / "GPT_SoVITS" / "configs" / "tts_infer.yaml",
        project_root / "configs" / "tts_infer.yaml",
    ]
    config_path = next((p for p in config_candidates if p.exists()), None)
    tts_cfg = TTS_Config(str(config_path)) if config_path else TTS_Config()
    tts = TTS(tts_cfg)

    if model_id and model_id != "default":
        gpt_weights, sovits_weights = _resolve_model_weights(project_root, model_id)
        logger.info("Switch model weights: gpt=%s", gpt_weights)
        logger.info("Switch model weights: sovits=%s", sovits_weights)
        tts.init_t2s_weights(str(gpt_weights))
        tts.init_vits_weights(str(sovits_weights))
    return tts


def _synthesize_with_gptsovits(
    *,
    tts: Any,
    reference_audio: Path,
    reference_text: str,
    reference_lang: str,
    target_text: str,
    target_lang: str,
    output_path: Path,
) -> None:
    available_langs = set(getattr(getattr(tts, "configs", None), "languages", []) or [])

    def fit_lang(raw: str) -> str:
        lang = _normalize_language(raw)
        if not available_langs:
            return lang
        if lang in available_langs:
            return lang
        for fallback in ("auto", "zh", "en", "ja"):
            if fallback in available_langs:
                return fallback
        return next(iter(available_langs))

    infer_inputs = {
        "text": target_text,
        "text_lang": fit_lang(target_lang),
        "ref_audio_path": str(reference_audio),
        "prompt_text": reference_text,
        "prompt_lang": fit_lang(reference_lang),
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "text_split_method": "cut5",
        "batch_size": 1,
        "batch_threshold": 0.75,
        "split_bucket": False,
        "speed_factor": 1.0,
        "return_fragment": False,
        "parallel_infer": True,
        "repetition_penalty": 1.2,
    }

    last_sr: Optional[int] = None
    last_audio: Optional[np.ndarray] = None
    for sr, audio in tts.run(infer_inputs):
        last_sr = int(sr)
        last_audio = np.asarray(audio)

    if last_sr is None or last_audio is None:
        raise RuntimeError("GPT-SoVITS inference produced no audio output")

    sf.write(str(output_path), last_audio, last_sr, subtype="PCM_16")


def _apply_pitch_shift(input_path: Path, output_path: Path, pitch_semitones: int) -> None:
    if pitch_semitones == 0:
        return

    logger.info("Applying pitch shift: %+d semitones", pitch_semitones)
    rate_factor = math.pow(2.0, float(pitch_semitones) / 12.0)
    atempo = _build_atempo_chain(rate_factor)
    sr = sf.info(str(input_path)).samplerate
    filter_complex = f"asetrate={sr}*{rate_factor:.8f},aresample={sr},{atempo}"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-filter:a",
                filter_complex,
                "-c:a",
                "pcm_s16le",
                str(tmp_path),
            ]
        )
        tmp_path.replace(output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="GPT-SoVITS voice conversion inference")
    parser.add_argument("--project-root", required=True, help="Path to GPT-SoVITS project root")
    parser.add_argument("--reference", required=True, help="Reference audio file (target voice)")
    parser.add_argument("--input", required=True, help="Input vocal file to convert")
    parser.add_argument("--output", required=True, help="Output audio file path")
    parser.add_argument("--model-id", default="default", help="Model ID to use (default: pretrained)")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch shift in semitones")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    reference_audio = Path(args.reference).resolve()
    input_audio = Path(args.input).resolve()
    output_audio = Path(args.output).resolve()

    if not project_root.exists():
        raise RuntimeError(f"Project root not found: {project_root}")
    if not reference_audio.exists():
        raise RuntimeError(f"Reference audio not found: {reference_audio}")
    if not input_audio.exists():
        raise RuntimeError(f"Input audio not found: {input_audio}")

    output_audio.parent.mkdir(parents=True, exist_ok=True)
    os.chdir(project_root)
    logger.info("Using GPT-SoVITS project root: %s", project_root)

    try:
        ref_text, ref_lang = _transcribe_audio(reference_audio)
        tgt_text, tgt_lang = _transcribe_audio(input_audio)
        if not ref_text.strip():
            ref_text = _fallback_text(ref_lang)
        if not tgt_text.strip():
            tgt_text = _fallback_text(tgt_lang)

        logger.info("Reference language=%s", ref_lang)
        logger.info("Target language=%s", tgt_lang)

        tts = _load_gptsovits_model(project_root, args.model_id)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_output = Path(tmp.name)
        try:
            _synthesize_with_gptsovits(
                tts=tts,
                reference_audio=reference_audio,
                reference_text=ref_text,
                reference_lang=ref_lang,
                target_text=tgt_text,
                target_lang=tgt_lang,
                output_path=tmp_output,
            )
            if args.pitch != 0:
                _apply_pitch_shift(tmp_output, output_audio, args.pitch)
            else:
                tmp_output.replace(output_audio)
        finally:
            if tmp_output.exists():
                tmp_output.unlink()

        if not output_audio.exists() or output_audio.stat().st_size <= 44:
            raise RuntimeError(f"Output file missing/empty: {output_audio}")
        logger.info("Voice conversion complete: %s", output_audio)
        return 0
    except Exception as exc:
        logger.exception("Voice conversion failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
