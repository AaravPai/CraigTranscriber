from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transcribe import transcribe_file


class RetryableError(Exception):
    status_code = 429


class PermanentError(Exception):
    status_code = 400


class FakeTranscriptions:
    def __init__(self, failures: list[Exception]) -> None:
        self.failures = failures
        self.calls = 0

    async def create(self, **_) -> SimpleNamespace:
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return SimpleNamespace(text="  Finished transcript  ")


def fake_client(transcriptions: FakeTranscriptions) -> SimpleNamespace:
    return SimpleNamespace(audio=SimpleNamespace(transcriptions=transcriptions))


async def no_sleep(_: float) -> None:
    return None


class TranscriptionRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_retries_transient_failures(self) -> None:
        transcriptions = FakeTranscriptions([RetryableError(), RetryableError()])

        with tempfile.TemporaryDirectory() as temp_directory:
            audio_path = Path(temp_directory) / "chunk.wav"
            audio_path.write_bytes(b"test audio")

            result = await transcribe_file(
                audio_path,
                client=fake_client(transcriptions),
                max_attempts=3,
                base_delay_seconds=0,
                sleep=no_sleep,
            )

        self.assertEqual(result, "Finished transcript")
        self.assertEqual(transcriptions.calls, 3)

    async def test_does_not_retry_permanent_failure(self) -> None:
        transcriptions = FakeTranscriptions([PermanentError()])

        with tempfile.TemporaryDirectory() as temp_directory:
            audio_path = Path(temp_directory) / "chunk.wav"
            audio_path.write_bytes(b"test audio")

            with self.assertRaises(PermanentError):
                await transcribe_file(
                    audio_path,
                    client=fake_client(transcriptions),
                    max_attempts=3,
                    base_delay_seconds=0,
                    sleep=no_sleep,
                )

        self.assertEqual(transcriptions.calls, 1)


if __name__ == "__main__":
    unittest.main()
