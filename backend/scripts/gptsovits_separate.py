#!/usr/bin/env python
"""Separate vocals/instrumental using GPT-SoVITS UVR modules."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def _pick_latest_audio(path: Path) -> Path:
    files = [
        p
        for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}
    ]
    if not files:
        raise RuntimeError(f"no output audio files found under {path}")
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def _prepare_input(src: Path, tmp_dir: Path) -> Path:
    dst = tmp_dir / f"{src.stem}.reformatted.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ac",
        "2",
        "-ar",
        "44100",
        str(dst),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="UVR separation wrapper for cover pipeline")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--vocal", required=True)
    parser.add_argument("--inst", required=True)
    parser.add_argument("--model", default="HP2_all_vocals")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--is-half", default="true")
    parser.add_argument("--agg", type=int, default=10)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    input_audio = Path(args.input).resolve()
    vocal_out = Path(args.vocal).resolve()
    inst_out = Path(args.inst).resolve()
    is_half = str(args.is_half).lower() in {"1", "true", "yes", "y"}

    if not project_root.exists():
        raise RuntimeError(f"project root not found: {project_root}")
    if not input_audio.exists():
        raise RuntimeError(f"input audio not found: {input_audio}")

    os.chdir(project_root)
    import sys

    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "tools" / "uvr5"))

    from tools.uvr5.mdxnet import MDXNetDereverb
    from tools.uvr5.vr import AudioPre, AudioPreDeEcho
    from tools.uvr5.bsroformer import Roformer_Loader

    weight_root = project_root / "tools" / "uvr5" / "uvr5_weights"
    model_name = args.model
    is_hp3 = "HP3" in model_name

    with tempfile.TemporaryDirectory(prefix="uvr_sep_") as td:
        tmp_dir = Path(td)
        vocal_dir = tmp_dir / "vocal"
        inst_dir = tmp_dir / "inst"
        vocal_dir.mkdir(parents=True, exist_ok=True)
        inst_dir.mkdir(parents=True, exist_ok=True)

        prepared = _prepare_input(input_audio, tmp_dir)

        if model_name == "onnx_dereverb_By_FoxJoy":
            pre_fun = MDXNetDereverb(15)
        elif "roformer" in model_name.lower():
            pre_fun = Roformer_Loader(
                model_path=str(weight_root / f"{model_name}.ckpt"),
                config_path=str(weight_root / f"{model_name}.yaml"),
                device=args.device,
                is_half=is_half,
            )
        else:
            klass = AudioPre if "DeEcho" not in model_name else AudioPreDeEcho
            pre_fun = klass(
                agg=int(args.agg),
                model_path=str(weight_root / f"{model_name}.pth"),
                device=args.device,
                is_half=is_half,
            )

        try:
            pre_fun._path_audio_(str(prepared), str(inst_dir), str(vocal_dir), "wav", is_hp3)
        finally:
            try:
                if model_name == "onnx_dereverb_By_FoxJoy":
                    del pre_fun.pred.model
                    del pre_fun.pred.model_
                else:
                    del pre_fun.model
                del pre_fun
            except Exception:
                pass

        produced_vocal = _pick_latest_audio(vocal_dir)
        produced_inst = _pick_latest_audio(inst_dir)

        vocal_out.parent.mkdir(parents=True, exist_ok=True)
        inst_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(produced_vocal, vocal_out)
        shutil.copyfile(produced_inst, inst_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
