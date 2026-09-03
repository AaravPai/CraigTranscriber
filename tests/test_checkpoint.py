from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from checkpoint import CheckpointStore
from merge import ChunkTranscript


class CheckpointStoreTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        transcript = ChunkTranscript(
            speaker_name="Craig",
            source_audio_file="craig.flac",
            chunk_audio_file="craig_0001.wav",
            start_seconds=12.5,
            end_seconds=20.0,
            text="Roll for initiative.",
        )

        with tempfile.TemporaryDirectory() as temp_directory:
            store = CheckpointStore(Path(temp_directory))
            store.save("chunk-key", transcript)

            self.assertEqual(store.load("chunk-key"), transcript)

    def test_missing_checkpoint_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            store = CheckpointStore(Path(temp_directory))

            self.assertIsNone(store.load("missing"))


if __name__ == "__main__":
    unittest.main()
