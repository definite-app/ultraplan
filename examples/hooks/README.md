# SessionStart Hook

Automatically load the latest ultraplan recording when you start a Claude Code session.

## How It Works

Claude Code supports hooks that run at specific events. The `SessionStart` hook runs when you start a new `claude` session. Our hook:

1. Finds the most recent `~/.ultraplan/sessions/session_*` directory
2. Reads `recording.md` content
3. Lists screenshot files for Claude to read
4. Outputs this context to Claude

## Setup

### 1. Copy the Hook Script

Copy `load-recording.py` to your project's `.claude/hooks/` directory:

```bash
mkdir -p .claude/hooks
cp examples/hooks/load-recording.py .claude/hooks/
```

Or for global use (all projects):
```bash
mkdir -p ~/.claude/hooks
cp examples/hooks/load-recording.py ~/.claude/hooks/
```

### 2. Configure Settings

Add to `.claude/settings.json` (project) or `.claude/settings.local.json` (not committed):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python .claude/hooks/load-recording.py"
          }
        ]
      }
    ]
  }
}
```

For global hooks, use absolute path:
```json
"command": "uv run python ~/.claude/hooks/load-recording.py"
```

### 3. Test It

```bash
# Make sure you have a recording
uv run ultraplan record
# ... record something, then Ctrl+C

# Start Claude - should see recording context loaded
claude
```

## Customization

### Change Recording Directory

Edit `load-recording.py` line 11:
```python
ULTRAPLAN_DIR = Path.home() / ".ultraplan" / "sessions"  # Change this
```

### Adjust Truncation Limit

Large recordings are truncated to leave room for conversation. Edit line 11:
```python
MAX_CONTENT_LENGTH = 15000  # Characters
```

### Disable Auto-Load

Remove or comment out the hook in settings.json, or rename the script.

## Troubleshooting

### Hook Not Running

1. Check the script path is correct
2. Ensure `uv` is in your PATH
3. Test the script directly: `echo '{"hook_event_name":"SessionStart"}' | uv run python .claude/hooks/load-recording.py`

### No Recording Found

The hook silently exits if no recordings exist. Run `uv run ultraplan record` first.

### Permission Denied

```bash
chmod +x .claude/hooks/load-recording.py
```

### Wrong Recording Loaded

Sessions are sorted alphabetically by directory name (which includes timestamp). The most recent `session_YYYYMMDD_HHMMSS` directory is selected.
