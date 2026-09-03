# CraigTranscriber

CraigTranscriber is a Python pipeline that turns multitrack Craig Discord recordings into readable, timestamped, speaker-labeled transcripts. It is designed for long-form sessions such as D&D games, where each participant is recorded on a separate audio track.

## Features

- Extracts Craig multitrack recording archives
- Detects nonsilent regions and splits long speech into smaller chunks
- Transcribes chunks concurrently through the OpenAI API
- Limits concurrency to avoid overwhelming the API
- Retries transient failures with exponential backoff
- Checkpoints each completed chunk so interrupted sessions can resume
- Merges speaker tracks into chronological JSON and text transcripts

## Processing flow

1. Select and extract the newest ZIP in `input_zips/`.
2. Discover supported audio tracks and identify each track by speaker name.
3. Detect speech regions and export bounded audio chunks.
4. Restore completed chunks from the session checkpoint directory.
5. Submit remaining chunks through a bounded asynchronous worker pool.
6. Merge completed transcripts by their original recording timestamps.

## Project structure

```text
CraigTranscriber/
├── input_zips/
├── extracted/
├── outputs/
├── temp_chunks/
├── tests/
└── src/
    ├── main.py
    ├── config.py
    ├── extract.py
    ├── discover.py
    ├── chunk.py
    ├── pipeline.py
    ├── checkpoint.py
    ├── transcribe.py
    └── merge.py
```

Runtime directories are created automatically and excluded from Git.

## Setup

Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
TRANSCRIPTION_MODEL=gpt-4o-transcribe
MAX_CONCURRENT_TRANSCRIPTIONS=4
MAX_TRANSCRIPTION_ATTEMPTS=4
RETRY_BASE_DELAY_SECONDS=1.0
```

`MAX_CONCURRENT_TRANSCRIPTIONS` controls how many audio chunks may be submitted at once. Increase it carefully based on the API limits available to your account.

## Usage

1. Record a Discord session using Craig.
2. Download the multitrack audio ZIP.
3. Place the ZIP in `input_zips/`.
4. Run:

```powershell
python .\src\main.py
```

Outputs are written to `outputs/<session-name>/`:

- `transcripts.json`: structured chunk metadata and text
- `transcript.txt`: chronological, speaker-labeled transcript
- `transcript_debug.txt`: transcript with chunk filenames and time ranges
- `.checkpoints/`: durable per-chunk progress used when resuming

If processing is interrupted, run the same input again. Completed chunks are loaded from checkpoints and are not submitted to the transcription API a second time.

## Tests

The automated tests use fake transcription clients and do not require an API key:

```powershell
python -m unittest discover -s tests -v
```

## Current status

The core extraction, chunking, concurrent transcription, checkpointing, and merge pipeline is implemented. Planned improvements include parsing Craig metadata for Discord display names, generating D&D-specific session notes, and benchmarking full-session processing time.
