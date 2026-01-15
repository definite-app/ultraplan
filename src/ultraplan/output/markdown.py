"""Markdown output generator."""

from pathlib import Path
from typing import Optional

from ultraplan.config import SessionConfig
from ultraplan.core.events import EventType
from ultraplan.core.timeline import Timeline


class MarkdownOutputGenerator:
    """Generates human-readable Markdown output from a recording session."""

    def __init__(
        self,
        timeline: Timeline,
        config: SessionConfig,
        full_transcript: Optional[str] = None,
        session_dir: Optional[Path] = None,
    ):
        self.timeline = timeline
        self.config = config
        self.full_transcript = full_transcript or ""
        self.session_dir = session_dir

    def _format_timestamp(self, ms: int) -> str:
        """Format milliseconds as [HH:MM:SS]."""
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"

    def _reconstruct_keystrokes(self, events: list) -> list[tuple[int, str]]:
        """Reconstruct keystroke sequences from individual keystroke events.

        Groups keystrokes that occur within 2 seconds of each other.
        Returns list of (timestamp_ms, reconstructed_text) tuples.
        """
        keystroke_events = [e for e in events if e.type == EventType.KEYSTROKE]
        if not keystroke_events:
            return []

        sequences = []
        current_seq = []
        current_start = keystroke_events[0].timestamp_ms

        for event in keystroke_events:
            key = event.data["key"]
            is_special = event.data["is_special"]

            # Start new sequence if gap > 2 seconds
            if current_seq and (event.timestamp_ms - current_start > 2000):
                # Save current sequence
                reconstructed = self._keys_to_text(current_seq)
                if reconstructed.strip():
                    sequences.append((current_start, reconstructed))
                current_seq = []
                current_start = event.timestamp_ms

            if not current_seq:
                current_start = event.timestamp_ms

            current_seq.append((key, is_special))

        # Don't forget last sequence
        if current_seq:
            reconstructed = self._keys_to_text(current_seq)
            if reconstructed.strip():
                sequences.append((current_start, reconstructed))

        return sequences

    def _keys_to_text(self, keys: list[tuple[str, bool]]) -> str:
        """Convert list of (key, is_special) to readable text."""
        result = []
        for key, is_special in keys:
            if is_special:
                # Show special keys in brackets
                result.append(key)
            else:
                result.append(key)
        return "".join(result)

    def generate(self) -> str:
        """Generate Markdown content."""
        lines = []

        # Header
        lines.append("# Recording Session")
        lines.append("")

        if self.session_dir:
            lines.append(f"**Session Directory**: `{self.session_dir.resolve()}`")

        if self.timeline.started_at:
            lines.append(f"**Started**: {self.timeline.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        duration_s = self.timeline.duration_ms // 1000
        mins, secs = divmod(duration_s, 60)
        lines.append(f"**Duration**: {mins} minutes {secs} seconds")
        lines.append(f"**Model**: whisper-{self.config.whisper_model}")
        lines.append("")

        # Full transcript section (from second-pass transcription)
        if self.full_transcript:
            lines.append("## Full Transcript")
            lines.append("")
            lines.append(self.full_transcript)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Timeline")
        lines.append("")

        # Process events in chronological order
        events = sorted(self.timeline.events, key=lambda e: e.timestamp_ms)

        # Get keystroke sequences
        keystroke_sequences = self._reconstruct_keystrokes(events)

        for event in events:
            ts = self._format_timestamp(event.timestamp_ms)

            if event.type == EventType.SESSION_START:
                lines.append(f"### {ts} Session Started")
                lines.append("")

            elif event.type == EventType.TRANSCRIPT:
                text = event.data.get("text", "")
                if text and not event.data.get("is_partial", False):
                    lines.append(f"### {ts} Transcript")
                    lines.append(f"> {text}")
                    lines.append("")

            elif event.type == EventType.SCREENSHOT:
                filename = event.data.get("filename", "")
                trigger = event.data.get("trigger", "hotkey")
                lines.append(f"### {ts} Screenshot")
                lines.append(f"![Screenshot]({filename})")
                lines.append(f"*Triggered by: {trigger}*")
                lines.append("")

            elif event.type == EventType.CLIPBOARD:
                content = event.data.get("content", "")
                if content:
                    lines.append(f"### {ts} Clipboard")
                    # Truncate very long clipboard content
                    if len(content) > 500:
                        content = content[:500] + "..."
                    lines.append("```")
                    lines.append(content)
                    lines.append("```")
                    lines.append("")

            elif event.type == EventType.SESSION_END:
                lines.append(f"### {ts} Session Ended")
                lines.append("")

        # Add keystroke sequences section if any
        if keystroke_sequences:
            lines.append("## Keystroke Sequences")
            lines.append("")
            for ts_ms, text in keystroke_sequences:
                ts = self._format_timestamp(ts_ms)
                # Escape backticks in the text
                escaped = text.replace("`", "\\`")
                lines.append(f"- {ts} `{escaped}`")
            lines.append("")

        # Summary statistics
        lines.append("---")
        lines.append("")
        lines.append("## Summary Statistics")
        lines.append("")

        transcript_events = [e for e in events if e.type == EventType.TRANSCRIPT]
        word_count = sum(
            len(e.data.get("text", "").split())
            for e in transcript_events
            if not e.data.get("is_partial", False)
        )

        screenshot_count = len([e for e in events if e.type == EventType.SCREENSHOT])
        clipboard_count = len([e for e in events if e.type == EventType.CLIPBOARD])

        lines.append(f"- Total transcribed words: {word_count}")
        lines.append(f"- Screenshots taken: {screenshot_count}")
        lines.append(f"- Clipboard events: {clipboard_count}")
        lines.append(f"- Keystroke sequences logged: {len(keystroke_sequences)}")
        lines.append("")

        return "\n".join(lines)

    def save(self, path: Path):
        """Save Markdown to file."""
        content = self.generate()
        path.write_text(content, encoding="utf-8")
