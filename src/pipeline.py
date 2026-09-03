from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from checkpoint import CheckpointStore
from config import MAX_CONCURRENT_TRANSCRIPTIONS, TRANSCRIPTION_MODEL
from merge import ChunkTranscript

Transcriber = Callable[[Path], Awaitable[str]]


@dataclass(frozen=True)
class TranscriptionJob:
    speaker_name: str
    source_audio_file: str
    source_size_bytes: int
    chunk_audio_file: str
    chunk_audio_path: Path
    start_seconds: float
    end_seconds: float
    transcription_model: str = TRANSCRIPTION_MODEL

    @property
    def checkpoint_key(self) -> str:
        identity = {
            "speaker_name": self.speaker_name,
            "source_audio_file": self.source_audio_file,
            "source_size_bytes": self.source_size_bytes,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "transcription_model": self.transcription_model,
        }
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_transcript(self, text: str) -> ChunkTranscript:
        return ChunkTranscript(
            speaker_name=self.speaker_name,
            source_audio_file=self.source_audio_file,
            chunk_audio_file=self.chunk_audio_file,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            text=text,
        )


async def transcribe_jobs(
    jobs: list[TranscriptionJob],
    checkpoint_store: CheckpointStore,
    *,
    transcriber: Transcriber | None = None,
    max_concurrency: int = MAX_CONCURRENT_TRANSCRIPTIONS,
) -> list[ChunkTranscript]:
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be at least 1")

    if transcriber is None:
        from transcribe import transcribe_file

        transcriber = transcribe_file

    semaphore = asyncio.Semaphore(max_concurrency)
    progress_lock = asyncio.Lock()
    completed_count = 0

    async def process(job: TranscriptionJob) -> ChunkTranscript:
        nonlocal completed_count

        cached_transcript = checkpoint_store.load(job.checkpoint_key)
        if cached_transcript is not None:
            async with progress_lock:
                completed_count += 1
                print(
                    f"  Restored {completed_count}/{len(jobs)}: "
                    f"{job.speaker_name} {job.start_seconds:.2f}s -> {job.end_seconds:.2f}s"
                )
            return cached_transcript

        async with semaphore:
            text = (await transcriber(job.chunk_audio_path)).strip()

        transcript = job.to_transcript(text)
        checkpoint_store.save(job.checkpoint_key, transcript)

        async with progress_lock:
            completed_count += 1
            print(
                f"  Transcribed {completed_count}/{len(jobs)}: "
                f"{job.speaker_name} {job.start_seconds:.2f}s -> {job.end_seconds:.2f}s"
            )

        return transcript

    results = await asyncio.gather(
        *(process(job) for job in jobs),
        return_exceptions=True,
    )

    transcripts: list[ChunkTranscript] = []
    failures: list[tuple[TranscriptionJob, Exception]] = []
    for job, result in zip(jobs, results):
        if isinstance(result, Exception):
            failures.append((job, result))
        else:
            transcripts.append(result)

    if failures:
        descriptions = "; ".join(
            f"{job.chunk_audio_file}: {error}" for job, error in failures[:5]
        )
        if len(failures) > 5:
            descriptions += f"; and {len(failures) - 5} more"
        raise RuntimeError(
            f"{len(failures)} transcription job(s) failed after other jobs were checkpointed: "
            f"{descriptions}"
        )

    return transcripts
