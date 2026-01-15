# Slash Commands

Load ultraplan recordings on demand with `/context` or `/latest` commands.

## Available Commands

| Command | Description |
|---------|-------------|
| `/record` | Start a new recording session |
| `/latest` | Load the most recent recording |
| `/context <session>` | Load a specific session by name |

## Setup

### 1. Copy Commands

**For this project only:**
```bash
mkdir -p .claude/commands
cp examples/commands/*.md .claude/commands/
```

**For all projects (global):**
```bash
mkdir -p ~/.claude/commands
cp examples/commands/*.md ~/.claude/commands/
```

### 2. Use Them

```bash
claude

# Load most recent recording
> /latest

# Load specific session
> /context session_20241229_143052
```

## How They Work

### `/latest`

Finds the most recent `./ultraplan/session_*` directory and:
1. Reads `recording.md` for the timeline
2. Lists screenshots for Claude to read
3. Summarizes what was captured

### `/context <session>`

Same as `/latest` but for a specific session. The argument is the session directory name:
```
> /context session_20241229_143052
```

## Customization

Edit the `.md` files in `.claude/commands/` to change:
- What Claude analyzes
- Output format
- Additional instructions

Example: Add to `latest.md`:
```markdown
Focus especially on:
- Action items and next steps
- Unresolved questions
- Code snippets mentioned
```

## Tips

### List Available Sessions

```bash
ls -la ./ultraplan/
```

### Tab Completion

Session names can be tab-completed if your shell supports it:
```
> /context session_<TAB>
```

### Screenshots

Both commands instruct Claude to read screenshots referenced in the recording. Claude will describe what it sees in each image.
