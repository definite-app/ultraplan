"""JSON output generator."""

import json
from pathlib import Path
from typing import Optional

from ultraplan.config import SessionConfig
from ultraplan.core.events import EventType
from ultraplan.core.timeline import Timeline


class JSONOutputGenerator:
    """Generates machine-parseable JSON output from a recording session."""

    def __init__(
        self,
        timeline: Timeline,
        config: SessionConfig,
        full_transcript: Optional[str] = None,
    ):
        self.timeline = timeline
        self.config = config
        self.full_transcript = full_transcript or ""

    def _reconstruct_keystroke_sequences(self, events: list) -> list[dict]:
        """Reconstruct keystroke sequences from individual events.

        Groups keystrokes that occur within 2 seconds of each other.
        """
        keystroke_events = [e for e in events if e.type == EventType.KEYSTROKE]
        if not keystroke_events:
            return []

        sequences = []
        current_keys = []
        current_start = keystroke_events[0].timestamp_ms

        for event in keystroke_events:
            key = event.data["key"]

            # Start new sequence if gap > 2 seconds
            if current_keys and (event.timestamp_ms - current_start > 2000):
                # Save current sequence
                sequences.append(
                    {
                        "type": "keystroke_sequence",
                        "timestamp_ms": current_start,
                        "data": {
                            "keys": current_keys.copy(),
                            "reconstructed": "".join(current_keys),
                        },
                    }
                )
                current_keys = []
                current_start = event.timestamp_ms

            if not current_keys:
                current_start = event.timestamp_ms

            current_keys.append(key)

        # Don't forget last sequence
        if current_keys:
            sequences.append(
                {
                    "type": "keystroke_sequence",
                    "timestamp_ms": current_start,
                    "data": {
                        "keys": current_keys.copy(),
                        "reconstructed": "".join(current_keys),
                    },
                }
            )

        return sequences

    def generate(self) -> dict:
        """Generate JSON-serializable dictionary."""
        events = sorted(self.timeline.events, key=lambda e: e.timestamp_ms)

        # Convert events to JSON-serializable format
        json_events = []
        for event in events:
            # Skip individual keystrokes - we'll add sequences instead
            if event.type == EventType.KEYSTROKE:
                continue

            json_events.append(
                {
                    "type": event.type.value,
                    "timestamp_ms": event.timestamp_ms,
                    "data": event.data,
                }
            )

        # Add keystroke sequences
        keystroke_sequences = self._reconstruct_keystroke_sequences(events)
        json_events.extend(keystroke_sequences)

        # Sort by timestamp again after adding sequences
        json_events.sort(key=lambda e: e["timestamp_ms"])

        # Calculate statistics
        transcript_events = [e for e in events if e.type == EventType.TRANSCRIPT]
        word_count = sum(
            len(e.data.get("text", "").split())
            for e in transcript_events
            if not e.data.get("is_partial", False)
        )

        result = {
            "session": {
                "id": self.timeline.session_id,
                "started_at": (
                    self.timeline.started_at.isoformat()
                    if self.timeline.started_at
                    else None
                ),
                "ended_at": (
                    self.timeline.ended_at.isoformat()
                    if self.timeline.ended_at
                    else None
                ),
                "duration_ms": self.timeline.duration_ms,
                "config": {
                    "whisper_model": self.config.whisper_model,
                    "audio_device": self.config.audio_device,
                    "sample_rate": self.config.sample_rate,
                },
            },
            "full_transcript": self.full_transcript,
            "events": json_events,
            "statistics": {
                "total_transcribed_words": word_count,
                "full_transcript_words": len(self.full_transcript.split()) if self.full_transcript else 0,
                "screenshots_count": len(
                    [e for e in events if e.type == EventType.SCREENSHOT]
                ),
                "clipboard_events_count": len(
                    [e for e in events if e.type == EventType.CLIPBOARD]
                ),
                "keystroke_sequences_count": len(keystroke_sequences),
            },
        }

        return result

    def save(self, path: Path):
        """Save JSON to file."""
        content = self.generate()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
