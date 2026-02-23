"""End-to-end regression tests for the cover pipeline.

Tests cover the full lifecycle:
1. Module imports & config validation
2. DB CRUD for cover jobs
3. API endpoint smoke tests (via TestClient)
4. Celery task dispatch (eager mode)
5. Cleanup task validation

Run with:
    cd backend
    python -m pytest tests/test_cover_e2e.py -v
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
import wave
import struct
from pathlib import Path

import pytest

# Ensure backend root is on path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Force eager mode so Celery tasks run in-process without Redis broker
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"

# Add ffmpeg to PATH if in conda env
FFMPEG_DIR = Path(r"D:\conda\envs\voice_api\Library\bin")
if FFMPEG_DIR.exists():
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")


def _generate_sine_wav(path: Path, duration_s: float = 2.0, sr: int = 44100) -> None:
    """Generate a short sine wave WAV file for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(sr * duration_s)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(n_frames):
            import math
            sample = int(16000 * math.sin(2 * math.pi * 440 * i / sr))
            wf.writeframes(struct.pack("<h", sample))


# ---------------------------------------------------------------------------
# Level 1: Module import validation
# ---------------------------------------------------------------------------

class TestModuleImports:
    """Verify all cover-related modules import without error."""

    def test_import_config(self):
        from app.core.config import settings
        assert settings.COVER_ASSET_ROOT
        assert settings.COVER_RESULT_TTL_HOURS > 0
        assert settings.COVER_MAX_DURATION_SECONDS > 0

    def test_import_schemas(self):
        from app.models.schemas import (
            CoverJobStatusEnum,
            CoverJobStageEnum,
            CoverCreateResponse,
            CoverJobStatusResponse,
            CoverCancelResponse,
        )
        assert CoverJobStatusEnum.QUEUED == "queued"
        assert CoverJobStageEnum.SEPARATE == "separate"

    def test_import_cover_job_model(self):
        from app.db.models.cover_job import CoverJob
        assert CoverJob.__tablename__ == "cover_jobs"

    def test_import_pipeline(self):
        from app.services.cover_pipeline import CoverPipeline, CoverPipelineResult
        pipeline = CoverPipeline()
        assert pipeline.runner is not None

    def test_import_runner(self):
        from app.services.gpt_sovits_runner import GPTSoVITSRunner, RunnerError
        runner = GPTSoVITSRunner()
        assert runner is not None

    def test_import_cover_tasks(self):
        from app.tasks.cover_tasks import run_cover_job
        assert run_cover_job.name == "cover.run_cover_job"

    def test_import_cleanup_tasks(self):
        from app.tasks.cleanup_tasks import cleanup_expired_assets, cleanup_expired_assets_task
        assert cleanup_expired_assets_task.name == "cover.cleanup_expired_assets"

    def test_import_celery_beat_schedule(self):
        from app.tasks.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule
        assert "cleanup-expired-cover-assets" in schedule
        assert schedule["cleanup-expired-cover-assets"]["task"] == "cover.cleanup_expired_assets"

    def test_import_cover_job_service(self):
        from app.services.cover_job_service import create_cover_job, get_cover_job, update_cover_job
        assert callable(create_cover_job)
        assert callable(get_cover_job)
        assert callable(update_cover_job)


# ---------------------------------------------------------------------------
# Level 2: Database CRUD
# ---------------------------------------------------------------------------

class TestCoverJobDB:
    """Test cover job database operations."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

        # Re-import to pick up new DATABASE_URL
        import importlib
        import app.core.config
        importlib.reload(app.core.config)
        import app.db.session
        importlib.reload(app.db.session)

        from app.db.base import Base
        from app.db.session import engine

        async def _init():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_init())
        yield
        asyncio.run(engine.dispose())

    def test_create_and_get_job(self):
        from app.db.session import async_session_maker
        from app.services.cover_job_service import create_cover_job, get_cover_job

        job_id = uuid.uuid4()

        async def _test():
            async with async_session_maker() as session:
                job = await create_cover_job(
                    session,
                    job_id=job_id,
                    user_id=None,
                    input_voice_path="/tmp/ref.wav",
                    input_song_path="/tmp/song.wav",
                    model_id="default",
                    pitch_shift=0,
                )
                assert job.id == job_id
                assert job.status == "queued"
                assert job.stage == "queued"
                assert job.progress == 0

            async with async_session_maker() as session:
                fetched = await get_cover_job(session, job_id)
                assert fetched is not None
                assert fetched.id == job_id
                assert fetched.input_voice_path == "/tmp/ref.wav"

        asyncio.run(_test())

    def test_update_job_status(self):
        from app.db.session import async_session_maker
        from app.services.cover_job_service import create_cover_job, update_cover_job, get_cover_job

        job_id = uuid.uuid4()

        async def _test():
            async with async_session_maker() as session:
                await create_cover_job(
                    session,
                    job_id=job_id,
                    user_id=None,
                    input_voice_path="/tmp/ref.wav",
                    input_song_path="/tmp/song.wav",
                )

            async with async_session_maker() as session:
                updated = await update_cover_job(
                    session,
                    job_id=job_id,
                    status="running",
                    stage="separate",
                    progress=35,
                )
                assert updated.status == "running"
                assert updated.stage == "separate"
                assert updated.progress == 35

            async with async_session_maker() as session:
                updated = await update_cover_job(
                    session,
                    job_id=job_id,
                    status="succeeded",
                    stage="finalize",
                    progress=100,
                    output_mix_path="/tmp/output.wav",
                )
                assert updated.status == "succeeded"
                assert updated.output_mix_path == "/tmp/output.wav"

        asyncio.run(_test())

    def test_get_nonexistent_job(self):
        from app.db.session import async_session_maker
        from app.services.cover_job_service import get_cover_job

        async def _test():
            async with async_session_maker() as session:
                result = await get_cover_job(session, uuid.uuid4())
                assert result is None

        asyncio.run(_test())


# ---------------------------------------------------------------------------
# Level 3: Runner unit tests (ffmpeg steps)
# ---------------------------------------------------------------------------

class TestGPTSoVITSRunner:
    """Test runner ffmpeg-based steps (preprocess, probe, mix)."""

    def test_preprocess_song(self, tmp_path):
        from app.services.gpt_sovits_runner import GPTSoVITSRunner

        runner = GPTSoVITSRunner()
        input_wav = tmp_path / "input.wav"
        output_wav = tmp_path / "output" / "preprocessed.wav"
        _generate_sine_wav(input_wav, duration_s=1.0)

        runner.preprocess_song(input_wav, output_wav)
        assert output_wav.exists()
        assert output_wav.stat().st_size > 0

    def test_probe_duration(self, tmp_path):
        from app.services.gpt_sovits_runner import GPTSoVITSRunner

        runner = GPTSoVITSRunner()
        input_wav = tmp_path / "probe_test.wav"
        _generate_sine_wav(input_wav, duration_s=2.0)

        duration = runner.probe_duration_seconds(input_wav)
        assert 1.5 < duration < 2.5  # Allow some tolerance

    def test_mix_audio(self, tmp_path):
        from app.services.gpt_sovits_runner import GPTSoVITSRunner

        runner = GPTSoVITSRunner()
        vocal = tmp_path / "vocal.wav"
        inst = tmp_path / "inst.wav"
        output = tmp_path / "mix.wav"
        _generate_sine_wav(vocal, duration_s=1.0)
        _generate_sine_wav(inst, duration_s=1.0)

        runner.mix_audio(converted_vocal=vocal, instrumental=inst, output_mix=output)
        assert output.exists()
        assert output.stat().st_size > 0


# ---------------------------------------------------------------------------
# Level 4: API endpoint smoke tests
# ---------------------------------------------------------------------------

class TestCoverAPI:
    """Test cover API endpoints via FastAPI TestClient."""

    @pytest.fixture(autouse=True)
    def setup_api(self, tmp_path):
        """Setup test database and app."""
        db_path = tmp_path / "api_test.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"

        import importlib
        import app.core.config
        importlib.reload(app.core.config)
        import app.db.session
        importlib.reload(app.db.session)

        from app.db.base import Base
        from app.db.session import engine

        async def _init():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_init())

        from app.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)
        self.api_key = "your-api-key-here"
        self.tmp_path = tmp_path
        yield
        asyncio.run(engine.dispose())

    def test_create_job_requires_auth(self):
        """POST /api/v1/cover/jobs without API key should fail."""
        resp = self.client.post("/api/v1/cover/jobs")
        assert resp.status_code in (401, 403, 422)

    def test_create_job_requires_cmd_templates(self):
        """POST /api/v1/cover/jobs should check cmd templates are configured."""
        from app.core.config import settings

        # If templates are empty, should return 503
        if not settings.COVER_SEPARATE_CMD_TEMPLATE or not settings.COVER_INFER_CMD_TEMPLATE:
            ref_wav = self.tmp_path / "ref.wav"
            song_wav = self.tmp_path / "song.wav"
            _generate_sine_wav(ref_wav)
            _generate_sine_wav(song_wav)

            with open(ref_wav, "rb") as rf, open(song_wav, "rb") as sf:
                resp = self.client.post(
                    "/api/v1/cover/jobs",
                    headers={"X-API-Key": self.api_key},
                    files={
                        "reference_voice": ("ref.wav", rf, "audio/wav"),
                        "song": ("song.wav", sf, "audio/wav"),
                    },
                    data={"pitch_shift": "0"},
                )
            assert resp.status_code == 503

    def test_get_nonexistent_job(self):
        """GET /api/v1/cover/jobs/{bad_id} should return 404."""
        fake_id = str(uuid.uuid4())
        resp = self.client.get(
            f"/api/v1/cover/jobs/{fake_id}",
            headers={"X-API-Key": self.api_key},
        )
        assert resp.status_code == 404

    def test_get_invalid_job_id(self):
        """GET /api/v1/cover/jobs/not-a-uuid should return 400."""
        resp = self.client.get(
            "/api/v1/cover/jobs/not-a-uuid",
            headers={"X-API-Key": self.api_key},
        )
        assert resp.status_code == 400

    def test_cancel_nonexistent_job(self):
        """POST /api/v1/cover/jobs/{bad_id}/cancel should return 404."""
        fake_id = str(uuid.uuid4())
        resp = self.client.post(
            f"/api/v1/cover/jobs/{fake_id}/cancel",
            headers={"X-API-Key": self.api_key},
        )
        assert resp.status_code == 404

    def test_result_nonexistent_job(self):
        """GET /api/v1/cover/jobs/{bad_id}/result should return 404."""
        fake_id = str(uuid.uuid4())
        resp = self.client.get(
            f"/api/v1/cover/jobs/{fake_id}/result",
            headers={"X-API-Key": self.api_key},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Level 5: Cleanup task validation
# ---------------------------------------------------------------------------

class TestCleanupTask:
    """Test the cleanup task logic."""

    def test_cleanup_nonexistent_dir(self, tmp_path):
        """Cleanup should handle missing cover_assets dir gracefully."""
        os.environ["COVER_ASSET_ROOT"] = str(tmp_path / "nonexistent")

        import importlib
        import app.core.config
        importlib.reload(app.core.config)

        from app.tasks.cleanup_tasks import cleanup_expired_assets
        result = cleanup_expired_assets(ttl_hours=1, dry_run=True)
        assert result["deleted_count"] == 0
        assert result["orphaned_count"] == 0

    def test_cleanup_empty_dir(self, tmp_path):
        """Cleanup should handle empty cover_assets dir."""
        cover_dir = tmp_path / "cover_assets"
        cover_dir.mkdir()
        os.environ["COVER_ASSET_ROOT"] = str(cover_dir)

        import importlib
        import app.core.config
        importlib.reload(app.core.config)

        from app.tasks.cleanup_tasks import cleanup_expired_assets
        result = cleanup_expired_assets(ttl_hours=1, dry_run=True)
        assert result["deleted_count"] == 0


# ---------------------------------------------------------------------------
# Level 6: Pipeline stage sequence validation
# ---------------------------------------------------------------------------

class TestPipelineStages:
    """Validate pipeline stage progression logic."""

    def test_stage_enum_order(self):
        from app.models.schemas import CoverJobStageEnum
        stages = list(CoverJobStageEnum)
        stage_names = [s.value for s in stages]
        assert stage_names == ["queued", "preprocess", "separate", "infer", "mix", "finalize"]

    def test_status_enum_values(self):
        from app.models.schemas import CoverJobStatusEnum
        statuses = {s.value for s in CoverJobStatusEnum}
        assert statuses == {"queued", "running", "succeeded", "failed", "canceled"}

    def test_pipeline_result_dataclass(self):
        from app.services.cover_pipeline import CoverPipelineResult
        result = CoverPipelineResult(
            vocal_path=Path("/tmp/v.wav"),
            inst_path=Path("/tmp/i.wav"),
            mix_path=Path("/tmp/m.wav"),
        )
        assert result.vocal_path == Path("/tmp/v.wav")
        assert result.mix_path == Path("/tmp/m.wav")
