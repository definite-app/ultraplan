"""Event types for the recording timeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of events that can be recorded."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    TRANSCRIPT = "transcript"
    KEYSTROKE = "keystroke"
    CLIPBOARD = "clipboard"
    SCREENSHOT = "screenshot"


@dataclass
class Event:
    """Base event class for all recorded events."""

    type: EventType
    timestamp_ms: int  # Milliseconds since session start
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptEvent(Event):
    """Event for transcribed audio segments."""

    def __init__(
        self,
        timestamp_ms: int,
        text: str,
        confidence: float = 0.0,
        is_partial: bool = False,
    ):
        super().__init__(
            type=EventType.TRANSCRIPT,
            timestamp_ms=timestamp_ms,
            data={
                "text": text,
                "confidence": confidence,
                "is_partial": is_partial,
            },
        )

    @property
    def text(self) -> str:
        return self.data["text"]


@dataclass
class KeystrokeEvent(Event):
    """Event for a single keystroke."""

    def __init__(
        self,
        timestamp_ms: int,
        key: str,
        is_special: bool = False,
    ):
        super().__init__(
            type=EventType.KEYSTROKE,
            timestamp_ms=timestamp_ms,
            data={
                "key": key,
                "is_special": is_special,
            },
        )

    @property
    def key(self) -> str:
        return self.data["key"]


@dataclass
class ClipboardEvent(Event):
    """Event for clipboard content changes."""

    def __init__(
        self,
        timestamp_ms: int,
        content: str,
        content_type: str = "text",
    ):
        super().__init__(
            type=EventType.CLIPBOARD,
            timestamp_ms=timestamp_ms,
            data={
                "content": content,
                "content_type": content_type,
            },
        )

    @property
    def content(self) -> str:
        return self.data["content"]


@dataclass
class ScreenshotEvent(Event):
    """Event for a captured screenshot."""

    def __init__(
        self,
        timestamp_ms: int,
        filename: str,
        trigger: str = "hotkey",
    ):
        super().__init__(
            type=EventType.SCREENSHOT,
            timestamp_ms=timestamp_ms,
            data={
                "filename": filename,
                "trigger": trigger,
            },
        )

    @property
    def filename(self) -> str:
        return self.data["filename"]
