#!/usr/bin/env python3
"""
SessionStart hook for Claude Code that loads the latest ultraplan recording.

Install: Copy to .claude/hooks/ and configure in settings.json
"""
import sys
import json
from pathlib import Path

ULTRAPLAN_DIR = Path.home() / ".ultraplan" / "sessions"
MAX_CONTENT_LENGTH = 15000  # Leave room for conversation


def find_latest_session() -> Path | None:
    """Find the most recent ultraplan session directory."""
    if not ULTRAPLAN_DIR.exists():
        return None

    sessions = sorted(ULTRAPLAN_DIR.glob("session_*"))
    return sessions[-1] if sessions else None


def get_screenshot_list(session_dir: Path) -> list[str]:
    """Get list of screenshot filenames in the session."""
    return sorted([f.name for f in session_dir.glob("img_*.png")])


def main():
    # Read hook input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    # Only run on SessionStart
    if input_data.get("hook_event_name") != "SessionStart":
        sys.exit(0)

    # Find latest recording
    session_dir = find_latest_session()
    if not session_dir:
        sys.exit(0)

    recording_file = session_dir / "recording.md"
    if not recording_file.exists():
        sys.exit(0)

    # Read recording content
    content = recording_file.read_text()

    # Truncate if too long
    truncated = False
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]
        truncated = True

    # Get screenshot list
    screenshots = get_screenshot_list(session_dir)

    # Build output
    output_parts = [
        "## ultraplan Recording Context",
        "",
        f"**Session:** `{session_dir.name}`",
        f"**Path:** `{session_dir.resolve()}`",
    ]

    if screenshots:
        output_parts.append(f"**Screenshots:** {len(screenshots)} captured")
        output_parts.append("")
        output_parts.append("To view screenshots, read these files:")
        for img in screenshots:
            output_parts.append(f"- `{session_dir / img}`")

    output_parts.append("")
    output_parts.append("---")
    output_parts.append("")
    output_parts.append(content)

    if truncated:
        output_parts.append("")
        output_parts.append(f"*[Recording truncated at {MAX_CONTENT_LENGTH} chars. Full version at `{recording_file}`]*")

    print("\n".join(output_parts))
    sys.exit(0)


if __name__ == "__main__":
    main()
