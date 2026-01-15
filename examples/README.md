# ultraplan + Claude Code Integration

Use ultraplan recordings as context for Claude Code sessions. Record a meeting, research session, or debugging workflow, then let Claude analyze it.

## What ultraplan Captures

- **Audio transcription** - Real-time Whisper transcription of speech
- **Screenshots** - Triggered by "jj" hotkey
- **Clipboard** - Content copied during session
- **Keystrokes** - What you typed (optional)

## How Claude Code Consumes It

Two integration patterns:

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **SessionStart Hook** | Auto-loads latest recording when you start `claude` | Always want context loaded |
| **Slash Commands** | `/latest` or `/context <session>` on demand | Load specific sessions |

## Quick Start

### 1. Record a Session

```bash
uv run ultraplan record
# Press Ctrl+C to stop
```

This creates:
```
~/.ultraplan/sessions/session_20241229_143052/
├── recording.md      # Human-readable timeline
├── recording.json    # Machine-parseable
├── audio.wav         # Raw audio
└── img_*.png         # Screenshots
```

### 2. Load into Claude Code

**Option A: Slash command (simplest)**
```bash
claude
> /latest
```

**Option B: SessionStart hook (automatic)**

See [hooks/README.md](./hooks/README.md) for setup.

### 3. Ask Claude

Once the context is loaded, Claude can:
- Summarize what happened
- Extract action items
- Answer questions about the session
- Read and describe screenshots

## Setup Guides

- [hooks/](./hooks/) - SessionStart hook for auto-loading recordings
- [commands/](./commands/) - Slash commands (`/record`, `/latest`, `/context`)
- [global-shortcut/](./global-shortcut/) - System-wide keyboard shortcut (macOS)
- [SKILL.md](../SKILL.md) - Skill that teaches Claude how to use ultraplan

## How Screenshots Work

The `recording.md` contains references like:
```markdown
### [00:01:23] Screenshot
![Screenshot](img_001234.png)
```

When Claude reads the markdown and sees these references, it can use the Read tool to view the actual PNG files and describe what's shown.
