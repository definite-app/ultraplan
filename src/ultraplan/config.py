"""Configuration dataclasses for ultraplan."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def get_ultraplan_home() -> Path:
    """Get the ultraplan home directory (~/.ultraplan)."""
    return Path.home() / ".ultraplan"


def get_default_sessions_dir() -> Path:
    """Get the default sessions directory (~/.ultraplan/sessions)."""
    return get_ultraplan_home() / "sessions"


@dataclass
class SessionConfig:
    """Configuration for a recording session."""

    output_dir: Path = field(default_factory=get_default_sessions_dir)
    whisper_model: str = "base"  # tiny, base, small, medium, large-v3
    sample_rate: int = 16000
    audio_device: Optional[str] = None  # None = default/BlackHole
    hotkey_screenshot: str = "jj"
    hotkey_timeout: float = 0.5  # Max time between keys for hotkey detection
    voice_trigger: str = "marco"  # Voice command to trigger screenshot
    voice_stop: str = "finito"  # Voice command to stop recording
    vocabulary_boost: list[str] = None  # Words to boost recognition for
    enable_keylogging: bool = True
    enable_clipboard: bool = True
    save_audio: bool = True
    audio_buffer_duration: float = 3.0  # Seconds to buffer before transcribing
    clipboard_poll_interval: float = 0.5

    def __post_init__(self):
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
