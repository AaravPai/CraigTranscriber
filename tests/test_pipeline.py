from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from checkpoint import CheckpointStore
from pipeline import TranscriptionJob, transcribe_jobs


def make_job(directory: Path, index: int) -> TranscriptionJob:
    chunk_path = directory / f"speaker_{index}.wav"
    chunk_path.write_bytes(b"test audio")
    return TranscriptionJob(
        speaker_name=f"Speaker {index}",
        source_audio_file=f"speaker_{index}.flac",
        source_size_bytes=1_000 + index,
        chunk_audio_file=chunk_path.name,
        chunk_audio_path=chunk_path,
        start_seconds=float(index),
        end_seconds=float(index + 1),
        transcription_model="test-model",
    )


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_respects_concurrency_limit_and_checkpoints_results(self) -> None:
        active_workers = 0
        maximum_active_workers = 0

        async def fake_transcriber(audio_path: Path) -> str:
            nonlocal active_workers, maximum_active_workers
            active_workers += 1
            maximum_active_workers = max(maximum_active_workers, active_workers)
            await asyncio.sleep(0.01)
            active_workers -= 1
            return f"Transcript for {audio_path.stem}"

        with tempfile.TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            store = CheckpointStore(directory / "checkpoints")
            jobs = [make_job(directory, index) for index in range(6)]

            transcripts = await transcribe_jobs(
                jobs,
                store,
                transcriber=fake_transcriber,
                max_concurrency=2,
            )

            self.assertEqual(len(transcripts), 6)
            self.assertEqual(maximum_active_workers, 2)
            for job in jobs:
                self.assertIsNotNone(store.load(job.checkpoint_key))

    async def test_completed_checkpoints_are_restored_without_api_call(self) -> None:
        calls = 0

        async def fake_transcriber(_: Path) -> str:
            nonlocal calls
            calls += 1
            return "A completed transcription"

        with tempfile.TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            store = CheckpointStore(directory / "checkpoints")
            job = make_job(directory, 1)

            transcripts = await transcribe_jobs(
                [job],
                store,
                transcriber=fake_transcriber,
            )

            restored = await transcribe_jobs(
                [job],
                store,
                transcriber=fake_transcriber,
            )

            self.assertEqual(calls, 1)
            self.assertEqual(restored, transcripts)


if __name__ == "__main__":
    unittest.main()
