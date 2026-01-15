"""Timeline management for recording sessions."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ultraplan.core.events import Event


@dataclass
class Timeline:
    """Manages the timeline of events during a recording session."""

    session_id: str = ""
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    start_time: float = 0.0  # time.time() when session started
    events: list[Event] = field(default_factory=list)

    def start(self) -> None:
        """Start the timeline."""
        self.start_time = time.time()
        self.started_at = datetime.now()
        self.session_id = self.started_at.strftime("session_%Y%m%d_%H%M%S")

    def stop(self) -> None:
        """Stop the timeline."""
        self.ended_at = datetime.now()

    def get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds since session start."""
        return int((time.time() - self.start_time) * 1000)

    def add_event(self, event: Event) -> None:
        """Add an event to the timeline."""
        self.events.append(event)

    @property
    def duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        if self.ended_at and self.started_at:
            return int((self.ended_at - self.started_at).total_seconds() * 1000)
        elif self.started_at:
            return self.get_timestamp_ms()
        return 0

    def get_events_by_type(self, event_type) -> list[Event]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.type == event_type]
