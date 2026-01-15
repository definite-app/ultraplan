# ultraplan

CLI tool for recording multi-modal context (audio transcription, keystrokes, clipboard, screenshots) to generate detailed prompts for AI agents like Claude Code.

## Features

- **Real-time audio transcription** using Whisper (runs locally)
- **Keystroke logging** with full keystroke sequences
- **Screenshot capture** triggered by "jj" hotkey
- **Clipboard monitoring** for copy/paste events
- **Raw audio saving** for later reference
- **Dual output format**: Markdown (human-readable) + JSON (machine-parseable)

## Installation

```bash
# Clone the repository
git clone https://github.com/mritchie712/ultraplan.git
cd ultraplan

# Install with uv
uv sync
```

## macOS Setup (Required for System Audio)

To capture system audio (not just microphone), you need to install BlackHole:

```bash
# Install BlackHole virtual audio driver
brew install blackhole-2ch
```

Then set up a Multi-Output Device:

1. Open `/Applications/Utilities/Audio MIDI Setup.app`
2. Click '+' → Create Multi-Output Device
3. Check both your speakers/headphones AND "BlackHole 2ch"
4. Set the Multi-Output Device as your system output in System Settings

Run the setup command to check your configuration:

```bash
uv run ultraplan setup
```

## Usage

### Basic Recording

```bash
# Start recording (uses default microphone)
uv run ultraplan record

# Record with system audio (requires BlackHole)
uv run ultraplan record --device "BlackHole 2ch"

# Use a different Whisper model (tiny, base, small, medium, large-v3)
uv run ultraplan record -m small

# Custom output directory
uv run ultraplan record -o ./my_session
```

### During Recording

- **Ctrl+C**: Stop recording and generate output files
- **jj** (double-j quickly): Take a screenshot

### Options

```bash
uv run ultraplan record --help

Options:
  -o, --output TEXT     Output directory for recordings
  -m, --model TEXT      Whisper model size (tiny/base/small/medium/large-v3)
  --device TEXT         Audio input device name
  --no-keys             Disable keystroke logging
  --no-clipboard        Disable clipboard monitoring
  --no-audio            Disable saving raw audio WAV file
  --list-devices        List available audio devices
```

### List Audio Devices

```bash
uv run ultraplan record --list-devices
```

## Output

Each recording session creates a timestamped folder in the output directory:

```
ultraplan/session_20241229_143052/
├── recording.md      # Human-readable timeline with transcript
├── recording.json    # Machine-parseable event data
├── audio.wav         # Raw audio recording
├── img_000000.png    # Screenshots (timestamp in ms)
└── img_015234.png
```

### Markdown Format

The markdown file contains a chronological timeline with:
- Transcribed speech segments
- Embedded screenshots
- Clipboard content (in code blocks)
- Keystroke sequences
- Summary statistics

### JSON Format

The JSON file contains structured data with:
- Session metadata (timestamps, configuration)
- Array of typed events (transcript, clipboard, screenshot, keystroke_sequence)
- Statistics (word count, event counts)

## Use with AI Agents

The output files are designed to provide context for AI coding assistants:

```bash
# Record a coding session
uv run ultraplan record --device "BlackHole 2ch"

# Then reference the output in Claude Code
claude "Based on the context in ultraplan/session_*/recording.md, help me implement..."
```

## Dependencies

- Python 3.11+
- faster-whisper (local Whisper inference)
- sounddevice (audio capture)
- pynput (keyboard monitoring)
- pyperclip (clipboard access)
- mss (screenshots)
- click + rich (CLI)

## License

MIT
