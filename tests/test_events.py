"""Tests for event types."""

from ultraplan.core.events import (
    ClipboardEvent,
    EventType,
    KeystrokeEvent,
    ScreenshotEvent,
    TranscriptEvent,
)


def test_transcript_event():
    event = TranscriptEvent(
        timestamp_ms=1000,
        text="Hello world",
        confidence=0.95,
        is_partial=False,
    )
    assert event.type == EventType.TRANSCRIPT
    assert event.timestamp_ms == 1000
    assert event.text == "Hello world"
    assert event.data["confidence"] == 0.95


def test_keystroke_event():
    event = KeystrokeEvent(
        timestamp_ms=500,
        key="a",
        is_special=False,
    )
    assert event.type == EventType.KEYSTROKE
    assert event.key == "a"
    assert not event.data["is_special"]


def test_clipboard_event():
    event = ClipboardEvent(
        timestamp_ms=2000,
        content="copied text",
    )
    assert event.type == EventType.CLIPBOARD
    assert event.content == "copied text"


def test_screenshot_event():
    event = ScreenshotEvent(
        timestamp_ms=3000,
        filename="img_003000.png",
        trigger="hotkey",
    )
    assert event.type == EventType.SCREENSHOT
    assert event.filename == "img_003000.png"
