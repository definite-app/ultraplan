# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ultraplan is a CLI tool for recording multi-modal context (audio transcription, keystrokes, clipboard, screenshots) to generate detailed prompts for AI agents like Claude Code.

## Development Commands

```bash
# Install dependencies
uv sync

# Install dev dependencies (pytest, ruff)
uv sync --extra dev

# Install globally (makes `ultraplan` available system-wide)
uv tool install . --python 3.12

# Run the CLI
uv run ultraplan record
uv run ultraplan setup

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_events.py::test_transcript_event

# Lint
uv run ruff check src/
uv run ruff format src/
```

## Architecture

### Package Structure

The codebase is in `src/ultraplan/` with the entry point at `cli.py`:

```
src/ultraplan/
├── cli.py              # Click CLI (record, setup commands)
├── config.py           # SessionConfig dataclass
├── core/
│   ├── session.py      # RecordingSession orchestrator
│   ├── events.py       # Event types (Transcript, Keystroke, Clipboard, Screenshot)
│   └── timeline.py     # Timeline for collecting events
├── capture/            # Input capture modules
│   ├── audio.py        # AudioCapture (sounddevice)
│   ├── transcription.py # TranscriptionWorker (faster-whisper)
│   ├── keyboard.py     # KeyboardCapture (pynput)
│   ├── clipboard.py    # ClipboardMonitor (pyperclip)
│   └── screenshot.py   # ScreenshotCapture (mss)
├── output/             # Output generators
│   ├── markdown.py     # MarkdownOutputGenerator
│   └── json_output.py  # JSONOutputGenerator
└── platform/
    └── macos.py        # macOS-specific utilities (permissions, notifications)
```

### Core Flow

1. `RecordingSession` in `core/session.py` orchestrates all capture modules
2. Each capture module runs in its own thread and pushes events to a shared queue
3. Consumer thread collects events into `Timeline`
4. On stop, `MarkdownOutputGenerator` and `JSONOutputGenerator` write output files

### Event System

Events are defined in `core/events.py`. All events inherit from base `Event` class with `type`, `timestamp_ms`, and `data` fields. Specific event types:
- `TranscriptEvent` - Whisper transcription segments
- `KeystrokeEvent` - Individual keystrokes
- `ClipboardEvent` - Clipboard content changes
- `ScreenshotEvent` - Screenshot captures (triggered by hotkey "jj" or voice command)

### Output Format

Sessions output to `~/.ultraplan/sessions/session_YYYYMMDD_HHMMSS/`:
- `recording.md` - Human-readable timeline with embedded screenshots
- `recording.json` - Machine-parseable event data
- `audio.wav` - Raw audio (optional)
- `img_*.png` - Screenshots (timestamp in filename is ms since session start)

## Claude Code Integration

The `examples/` directory contains:
- `commands/` - Slash commands (`/latest`, `/context`, `/record`) for loading recordings
- `hooks/` - SessionStart hook for auto-loading latest recording
- `global-shortcut/` - macOS shortcut to start recording globally

See `SKILL.md` for the skill definition that describes this tool to Claude Code.
