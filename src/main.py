from __future__ import annotations

import shutil
import time
from pathlib import Path

from chunk import make_chunks_for_track
from config import EXTRACTED_DIR, INPUT_ZIPS_DIR, OUTPUTS_DIR, TEMP_CHUNKS_DIR
from discover import discover_tracks, find_info_file
from extract import extract_zip
from merge import ChunkTranscript, write_debug_txt, write_json, write_txt
from transcribe import transcribe_file


def choose_latest_zip() -> Path:
    zip_files = sorted(INPUT_ZIPS_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zip_files:
        raise FileNotFoundError(
            f"No ZIP files found in {INPUT_ZIPS_DIR}. Put a Craig download ZIP there first."
        )
    return zip_files[0]


def sanitize_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name.strip())
    return safe or "speaker"


def main() -> None:
    zip_path = choose_latest_zip()
    session_name = zip_path.stem
    extracted_dir = EXTRACTED_DIR / session_name
    output_dir = OUTPUTS_DIR / session_name
    temp_dir = TEMP_CHUNKS_DIR / f"{session_name}_{int(time.time())}"

    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"Using ZIP: {zip_path.name}")
    extract_zip(zip_path, extracted_dir)
    print(f"Extracted to: {extracted_dir}")

    info_file = find_info_file(extracted_dir)
    if info_file:
        print(f"Found info.txt: {info_file}")

    tracks = discover_tracks(extracted_dir)
    if not tracks:
        raise RuntimeError("No supported audio files were found after extraction.")

    print(f"Found {len(tracks)} speaker track(s):")
    for track in tracks:
        print(f" - {track.speaker_name} -> {track.audio_path.name}")

    all_transcripts: list[ChunkTranscript] = []

    for track in tracks:
        print(f"\nChunking track: {track.audio_path.name}")
        chunks = make_chunks_for_track(track.speaker_name, track.audio_path)
        print(f"Found {len(chunks)} speech chunk(s) for {track.speaker_name}")

        speaker_safe = sanitize_name(track.speaker_name)

        for idx, chunk in enumerate(chunks, start=1):
            chunk_filename = (
                f"{speaker_safe}_{idx:04d}_{int(chunk.start_seconds)}s_{int(chunk.end_seconds)}s.wav"
            )
            chunk_path = temp_dir / chunk_filename

            chunk.audio.export(chunk_path, format="wav")

            print(
                f"  [{idx}/{len(chunks)}] "
                f"{track.speaker_name} {chunk.start_seconds:.2f}s -> {chunk.end_seconds:.2f}s"
            )

            text = transcribe_file(chunk_path).strip()
            if not text:
                continue

            all_transcripts.append(
                ChunkTranscript(
                    speaker_name=track.speaker_name,
                    source_audio_file=track.audio_path.name,
                    chunk_audio_file=chunk_filename,
                    start_seconds=chunk.start_seconds,
                    end_seconds=chunk.end_seconds,
                    text=text,
                )
            )

    json_path = output_dir / "transcripts.json"
    txt_path = output_dir / "transcript.txt"
    debug_txt_path = output_dir / "transcript_debug.txt"

    write_json(all_transcripts, json_path)
    write_txt(all_transcripts, txt_path)
    write_debug_txt(all_transcripts, debug_txt_path)

    print(f"\nSaved JSON:      {json_path}")
    print(f"Saved TXT:       {txt_path}")
    print(f"Saved debug TXT: {debug_txt_path}")


if __name__ == "__main__":
    main()