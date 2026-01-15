# ultraplan

CLI tool for recording multi-modal context (audio transcription, keystrokes, clipboard, screenshots) to generate detailed prompts for AI agents like Claude Code.

## Features

- **Real-time audio transcription** using Whisper (runs locally)
- **Keystroke logging** with full keystroke sequences
- **Screenshot capture** triggered by "jj" hotkey
- **Clipboard monitoring** for copy/paste events
- **Raw audio saving** for later reference
- **Dual output format**: Markdown (human-readable) + JSON (machine-parseable)

## Privacy Notice

**ultraplan captures sensitive data** including keystrokes, clipboard contents, audio, and screenshots. This data is stored locally in `~/.ultraplan/sessions/` and is never transmitted externally.

- All processing (including Whisper transcription) runs locally on your machine
- Session data may contain passwords, personal messages, or other sensitive information
- Review recordings before sharing them
- Use `--no-keys` and `--no-clipboard` flags to disable sensitive capture

**Only run ultraplan when you intend to record.** The keystroke and clipboard monitoring captures everything while active.

## Installation

```bash
# Clone the repository
git clone https://github.com/definite-app/ultraplan.git
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

## Claude Code Integration

ultraplan includes a skill that teaches Claude Code how to use it. Once installed, Claude will automatically suggest recording when appropriate (e.g., "I want to capture this meeting" or "let me show you my workflow").

### Install as a Personal Skill

Copy the skill to your Claude Code skills directory:

```bash
# Clone ultraplan
git clone https://github.com/definite-app/ultraplan.git

# Copy to your personal skills directory
mkdir -p ~/.claude/skills
cp -r ultraplan ~/.claude/skills/ultraplan
```

That's it! Claude Code automatically discovers skills in `~/.claude/skills/`. No configuration needed.

### Install as a Project Skill (for teams)

To share the skill with your team, add it to your project's `.claude/skills/` directory:

```bash
cd /path/to/your/project
mkdir -p .claude/skills
cp -r /path/to/ultraplan .claude/skills/ultraplan
git add .claude/skills/ultraplan/
git commit -m "Add ultraplan skill"
```

Anyone who clones the project will have access to the skill.

### Slash Commands

Once installed, these slash commands become available in Claude Code:

- `/record` - Start a new recording session
- `/latest` - Load the most recent recording into context
- `/context <session_name>` - Load a specific session

See `examples/commands/` for the command definitions.

### Auto-load Recordings (Optional)

You can configure Claude Code to automatically load the latest recording when starting a session. See `examples/hooks/` for setup instructions.

### Manual Usage

You can also manually reference recordings:

```bash
# Record a session
uv run ultraplan record --device "BlackHole 2ch"

# Then in Claude Code, reference the output
claude "Based on the context in ~/.ultraplan/sessions/session_*/recording.md, help me..."
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
