"""High-level AI cover pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from app.core.config import settings
from app.services.gpt_sovits_runner import GPTSoVITSRunner


@dataclass
class CoverPipelineResult:
    """Result artifact paths produced by a cover pipeline run."""

    vocal_path: Path
    inst_path: Path
    mix_path: Path


class CoverPipeline:
    """Runs the end-to-end generation pipeline for one cover job."""

    def __init__(self, runner: Optional[GPTSoVITSRunner] = None):
        self.runner = runner or GPTSoVITSRunner()

    def run(
        self,
        *,
        work_root: Path,
        reference_voice: Path,
        song_input: Path,
        model_id: str,
        pitch_shift: int,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> CoverPipelineResult:
        work_dir = work_root / "work"
        output_dir = work_root / "output"
        work_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        preprocessed_song = work_dir / "song_preprocessed.wav"
        vocal_path = work_dir / "vocal.wav"
        inst_path = work_dir / "instrumental.wav"
        converted_vocal = work_dir / "converted_vocal.wav"
        mix_path = output_dir / "final.wav"

        if progress_callback:
            progress_callback("preprocess", 10)
        self.runner.preprocess_song(song_input, preprocessed_song)

        duration = self.runner.probe_duration_seconds(preprocessed_song)
        if duration > settings.COVER_MAX_DURATION_SECONDS:
            raise RuntimeError(
                f"song duration {duration:.2f}s exceeds limit {settings.COVER_MAX_DURATION_SECONDS}s"
            )

        if progress_callback:
            progress_callback("separate", 35)
        self.runner.separate_vocals(
            song_input=preprocessed_song,
            vocal_output=vocal_path,
            inst_output=inst_path,
        )

        if progress_callback:
            progress_callback("infer", 70)
        self.runner.convert_vocal(
            reference_voice=reference_voice,
            input_vocal=vocal_path,
            output_vocal=converted_vocal,
            model_id=model_id,
            pitch_shift=pitch_shift,
        )

        if progress_callback:
            progress_callback("mix", 90)
        self.runner.mix_audio(
            converted_vocal=converted_vocal,
            instrumental=inst_path,
            output_mix=mix_path,
        )

        if progress_callback:
            progress_callback("finalize", 100)

        return CoverPipelineResult(vocal_path=vocal_path, inst_path=inst_path, mix_path=mix_path)
