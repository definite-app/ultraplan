Start a new ultraplan recording session to capture context.

Run this command in the terminal:

```bash
uv run ultraplan record
```

This will:
- Start capturing audio and transcribing speech in real-time
- Monitor clipboard for copied content
- Log keystrokes (press "jj" quickly to take a screenshot)
- Save everything to `~/.ultraplan/sessions/session_YYYYMMDD_HHMMSS/`

**Press Ctrl+C to stop recording.**

After recording, use `/latest` to load and analyze the captured context.

## Options

Add these flags if needed:
- `--no-keys` - Don't log keystrokes
- `--no-clipboard` - Don't monitor clipboard
- `-m small` - Use larger Whisper model for better accuracy
- `--device "BlackHole 2ch"` - Capture system audio (requires BlackHole setup)

## macOS First-Time Setup

If this is your first time, run setup first:
```bash
uv run ultraplan setup
```

This checks for:
- BlackHole audio driver (for system audio capture)
- Accessibility permissions (for keystroke capture)
