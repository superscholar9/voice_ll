"""Runtime utilities for invoking GPT-SoVITS related commands."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)


class RunnerError(RuntimeError):
    """Raised when an external runtime step fails."""


class GPTSoVITSRunner:
    """Encapsulates shell-level execution for audio pipeline steps."""

    def _run_args(self, args: List[str], step: str) -> subprocess.CompletedProcess:
        """Run a command as a list of arguments (no shell, cross-platform safe)."""
        logger.info("Running step=%s args=%s", step, args)
        completed = subprocess.run(args, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RunnerError(
                f"{step} failed (exit={completed.returncode}). stdout={completed.stdout[-800:]} "
                f"stderr={completed.stderr[-800:]}"
            )
        return completed

    def _run_command(self, cmd: str, step: str) -> None:
        """Run a shell command string (used for template-based commands on Linux)."""
        logger.info("Running step=%s command=%s", step, cmd)
        completed = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RunnerError(
                f"{step} failed (exit={completed.returncode}). stdout={completed.stdout[-800:]} "
                f"stderr={completed.stderr[-800:]}"
            )

    def _run_template(self, template: str, values: Dict[str, str], step: str) -> None:
        if not template.strip():
            raise RunnerError(f"{step} command template is empty")
        command = template.format(**values)
        self._run_command(command, step=step)

    def preprocess_song(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_args(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ac", "2", "-ar", "44100",
                str(output_path),
            ],
            step="preprocess",
        )

    def probe_duration_seconds(self, input_path: Path) -> float:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(input_path),
            ],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RunnerError(f"ffprobe failed: {completed.stderr[-500:]}")
        try:
            return float(completed.stdout.strip())
        except ValueError as exc:
            raise RunnerError(f"unable to parse duration from ffprobe output: {completed.stdout!r}") from exc

    def separate_vocals(self, *, song_input: Path, vocal_output: Path, inst_output: Path) -> None:
        template = settings.COVER_SEPARATE_CMD_TEMPLATE
        values = {
            "python_exec": settings.GPT_SOVITS_PYTHON,
            "project_root": settings.GPT_SOVITS_PROJECT_ROOT,
            "song_input": str(song_input),
            "vocal_output": str(vocal_output),
            "inst_output": str(inst_output),
            "uvr_model": settings.COVER_UVR_MODEL,
        }
        self._run_template(template, values, step="separate")
        if not vocal_output.exists():
            raise RunnerError(f"separate step did not produce vocal output: {vocal_output}")
        if not inst_output.exists():
            raise RunnerError(f"separate step did not produce instrumental output: {inst_output}")

    def convert_vocal(
        self,
        *,
        reference_voice: Path,
        input_vocal: Path,
        output_vocal: Path,
        model_id: str,
        pitch_shift: int,
    ) -> None:
        template = settings.COVER_INFER_CMD_TEMPLATE
        values = {
            "python_exec": settings.GPT_SOVITS_PYTHON,
            "project_root": settings.GPT_SOVITS_PROJECT_ROOT,
            "reference_voice": str(reference_voice),
            "input_vocal": str(input_vocal),
            "output_vocal": str(output_vocal),
            "model_id": model_id,
            "pitch_shift": str(pitch_shift),
        }
        self._run_template(template, values, step="infer")
        if not output_vocal.exists():
            raise RunnerError(f"infer step did not produce output: {output_vocal}")

    def mix_audio(self, *, converted_vocal: Path, instrumental: Path, output_mix: Path) -> None:
        output_mix.parent.mkdir(parents=True, exist_ok=True)
        self._run_args(
            [
                "ffmpeg", "-y",
                "-i", str(converted_vocal),
                "-i", str(instrumental),
                "-filter_complex",
                "[0:a]volume=1.0[v];[1:a]volume=0.9[i];[v][i]amix=inputs=2:normalize=1[m]",
                "-map", "[m]",
                "-c:a", "pcm_s16le",
                str(output_mix),
            ],
            step="mix",
        )
        if not output_mix.exists():
            raise RunnerError(f"mix step did not produce output: {output_mix}")
