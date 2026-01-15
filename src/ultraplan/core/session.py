"""Main recording session orchestrator."""

import queue
import threading
import time
from pathlib import Path
from typing import Optional

import numpy as np
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from scipy.io import wavfile

from ultraplan.capture.audio import AudioCapture
from ultraplan.capture.clipboard import ClipboardMonitor
from ultraplan.capture.keyboard import KeyboardCapture
from ultraplan.capture.screenshot import ScreenshotCapture
from ultraplan.capture.transcription import TranscriptionWorker
from ultraplan.config import SessionConfig
from ultraplan.core.events import (
    ClipboardEvent,
    Event,
    EventType,
    KeystrokeEvent,
    ScreenshotEvent,
    TranscriptEvent,
)
from ultraplan.core.timeline import Timeline
from ultraplan.output.json_output import JSONOutputGenerator
from ultraplan.output.markdown import MarkdownOutputGenerator

console = Console()


def _sounds_like(text: str, target: str, threshold: int = 2) -> bool:
    """Check if any word in text sounds similar to target using edit distance.

    Whisper often mistranscribes words phonetically, e.g.:
    - "finito" -> "Pinito", "Veneto", "Thinito", "Fenito"

    Args:
        text: The transcribed text to search in
        target: The target word to match (e.g., "finito")
        threshold: Maximum edit distance to consider a match

    Returns:
        True if any word in text is within threshold edits of target
    """

    def edit_distance(s1: str, s2: str) -> int:
        """Compute Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    target_lower = target.lower()
    # Check each word in the text
    for word in text.lower().split():
        # Strip punctuation
        word = word.strip(".,!?;:'\"")
        # Skip words that are very different in length
        if abs(len(word) - len(target_lower)) > threshold:
            continue
        if edit_distance(word, target_lower) <= threshold:
            return True
    return False


class RecordingSession:
    """Orchestrates all capture modules for a recording session."""

    def __init__(self, config: SessionConfig):
        self.config = config
        self.timeline = Timeline()
        self.event_queue: queue.Queue[Event] = queue.Queue()
        self.running = threading.Event()

        # Capture modules
        self.audio_capture: Optional[AudioCapture] = None
        self.transcription_worker: Optional[TranscriptionWorker] = None
        self.keyboard_capture: Optional[KeyboardCapture] = None
        self.clipboard_monitor: Optional[ClipboardMonitor] = None
        self.screenshot_capture: Optional[ScreenshotCapture] = None

        # Threads
        self.consumer_thread: Optional[threading.Thread] = None
        self.audio_thread: Optional[threading.Thread] = None
        self.display_thread: Optional[threading.Thread] = None

        # State
        self.session_dir: Optional[Path] = None
        self.audio_chunks: list[np.ndarray] = []
        self.transcript_lines: list[str] = []  # Real-time transcript chunks
        self.full_transcript: str = ""  # Full second-pass transcript
        self.screenshots: list[str] = []  # List of screenshot filenames
        self.last_screenshot_time: float = 0  # For display flash effect
        self.last_screenshot_trigger: str = ""  # What triggered the screenshot
        self.clipboard_count: int = 0
        self.last_clipboard_time: float = 0
        self._voice_stop_requested: bool = False  # Voice command to stop

    def _setup_session_dir(self) -> Path:
        """Create the session output directory."""
        session_dir = self.config.output_dir / self.timeline.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _on_transcript(self, text: str, confidence: float, is_partial: bool):
        """Callback for transcription results."""
        timestamp_ms = self.timeline.get_timestamp_ms()
        event = TranscriptEvent(
            timestamp_ms=timestamp_ms,
            text=text,
            confidence=confidence,
            is_partial=is_partial,
        )
        self.event_queue.put(event)
        if not is_partial:
            self.transcript_lines.append(text)

            # Check for voice trigger word (screenshot)
            trigger_word = self.config.voice_trigger.lower()
            if trigger_word and trigger_word in text.lower():
                self._capture_screenshot(trigger=f"voice:{trigger_word}")

            # Check for voice stop command (with fuzzy matching for Whisper mistranscriptions)
            stop_phrase = self.config.voice_stop
            if stop_phrase and _sounds_like(text, stop_phrase):
                self._voice_stop_requested = True
                from ultraplan.platform.macos import play_sound

                play_sound("Purr")  # Acknowledgment sound

    def _on_keystroke(self, key: str, timestamp_ms: int, is_special: bool):
        """Callback for keystroke events."""
        event = KeystrokeEvent(
            timestamp_ms=timestamp_ms,
            key=key,
            is_special=is_special,
        )
        self.event_queue.put(event)

    def _capture_screenshot(self, trigger: str = "manual") -> Optional[str]:
        """Capture a screenshot and record the event.

        Args:
            trigger: What triggered the screenshot (hotkey, voice:bingo, manual)

        Returns:
            Filename of captured screenshot, or None if capture failed.
        """
        if not self.screenshot_capture:
            return None

        timestamp_ms = self.timeline.get_timestamp_ms()
        filename = self.screenshot_capture.capture(timestamp_ms)
        event = ScreenshotEvent(
            timestamp_ms=timestamp_ms,
            filename=filename,
            trigger=trigger,
        )
        self.event_queue.put(event)

        # Track screenshot for display
        self.screenshots.append(filename)
        self.last_screenshot_time = time.time()
        self.last_screenshot_trigger = trigger

        # Play sound notification
        from ultraplan.platform.macos import notify_screenshot_taken

        notify_screenshot_taken(filename)

        return filename

    def _on_hotkey(self, hotkey: str):
        """Callback for hotkey triggers."""
        if hotkey == "screenshot":
            self._capture_screenshot(trigger="hotkey")

    def _on_clipboard_change(self, content: str, timestamp_ms: int):
        """Callback for clipboard changes."""
        event = ClipboardEvent(
            timestamp_ms=timestamp_ms,
            content=content,
        )
        self.event_queue.put(event)

        # Track for display
        self.clipboard_count += 1
        self.last_clipboard_time = time.time()

    def _on_clipboard_image(self, image_data: bytes, timestamp_ms: int):
        """Callback for clipboard image changes (e.g., Cmd+Ctrl+Shift+4 screenshots)."""
        if not self.session_dir:
            return

        # Save image to session directory
        filename = f"clip_{timestamp_ms:06d}.png"
        filepath = self.session_dir / filename
        filepath.write_bytes(image_data)

        # Create screenshot event
        event = ScreenshotEvent(
            timestamp_ms=timestamp_ms,
            filename=filename,
            trigger="clipboard",
        )
        self.event_queue.put(event)

        # Track for display
        self.screenshots.append(filename)
        self.last_screenshot_time = time.time()
        self.last_screenshot_trigger = "clipboard"

        # Notify user
        from ultraplan.platform.macos import notify_screenshot_taken

        notify_screenshot_taken(filename)

    def _consume_events(self):
        """Consumer thread that collects events into timeline."""
        while self.running.is_set() or not self.event_queue.empty():
            try:
                event = self.event_queue.get(timeout=0.1)
                self.timeline.add_event(event)
            except queue.Empty:
                continue

    def _audio_loop(self):
        """Audio capture and transcription loop."""
        if not self.audio_capture or not self.transcription_worker:
            return

        while self.running.is_set():
            chunk = self.audio_capture.get_chunk(timeout=0.5)
            if chunk is not None:
                # Store raw audio for WAV file
                if self.config.save_audio:
                    self.audio_chunks.append(chunk.copy())
                # Feed to transcription worker
                self.transcription_worker.add_audio(chunk)

        # Process remaining audio in buffer
        self.transcription_worker.flush()

    def _display_loop(self):
        """Live display update loop."""

        def render_panel() -> Panel:
            duration_s = self.timeline.duration_ms // 1000
            mins, secs = divmod(duration_s, 60)

            transcript_text = (
                "\n".join(self.transcript_lines[-8:])
                if self.transcript_lines
                else "[dim](waiting for speech...)[/dim]"
            )

            hotkey = self.config.hotkey_screenshot
            now = time.time()

            # Event status line
            events_line = ""

            # Screenshot flash (2 seconds)
            if self.screenshots and now - self.last_screenshot_time < 2.0:
                trigger_info = (
                    f" ({self.last_screenshot_trigger})" if self.last_screenshot_trigger else ""
                )
                events_line = (
                    f"[bold green]📸 Screenshot: {self.screenshots[-1]}{trigger_info}[/bold green]"
                )
            # Clipboard flash (2 seconds)
            elif self.clipboard_count > 0 and now - self.last_clipboard_time < 2.0:
                events_line = "[bold yellow]📋 Clipboard copied[/bold yellow]"
            # Show counts if any events
            elif self.screenshots or self.clipboard_count:
                parts = []
                if self.screenshots:
                    parts.append(f"📸 {len(self.screenshots)}")
                if self.clipboard_count:
                    parts.append(f"📋 {self.clipboard_count}")
                events_line = f"[dim]{' | '.join(parts)}[/dim]"

            events_section = f"\n{events_line}" if events_line else ""

            voice_trigger = self.config.voice_trigger
            voice_stop = self.config.voice_stop
            content = f"""[bold]Duration:[/bold] {mins}:{secs:02d}

[bold]Live Transcript:[/bold]
{transcript_text}{events_section}

[dim]📸 '{hotkey}' or "{voice_trigger}" | 🛑 Ctrl+C or "{voice_stop}"[/dim]"""

            return Panel(content, title="ultraplan", border_style="blue")

        with Live(render_panel(), refresh_per_second=4, console=console) as live:
            while self.running.is_set():
                live.update(render_panel())
                time.sleep(0.25)

    def start(self):
        """Start the recording session."""
        self.timeline.start()
        self.session_dir = self._setup_session_dir()
        self.running.set()

        # Add session start event
        self.event_queue.put(Event(type=EventType.SESSION_START, timestamp_ms=0, data={}))

        # Initialize capture modules
        self.screenshot_capture = ScreenshotCapture(self.session_dir)

        # Audio and transcription
        self.audio_capture = AudioCapture(
            device=self.config.audio_device,
            sample_rate=self.config.sample_rate,
        )

        # Build vocabulary boost list (voice commands + custom words)
        vocab_boost = []
        if self.config.voice_trigger:
            vocab_boost.append(self.config.voice_trigger)
        if self.config.voice_stop:
            vocab_boost.extend(self.config.voice_stop.split())  # Add each word
        if self.config.vocabulary_boost:
            vocab_boost.extend(self.config.vocabulary_boost)

        self.transcription_worker = TranscriptionWorker(
            model_size=self.config.whisper_model,
            on_transcript=self._on_transcript,
            buffer_duration=self.config.audio_buffer_duration,
            sample_rate=self.config.sample_rate,
            vocabulary_boost=vocab_boost if vocab_boost else None,
        )

        console.print("[dim]Loading Whisper model...[/dim]")
        self.transcription_worker.load_model()
        console.print("[dim]Model loaded.[/dim]")

        self.audio_capture.start()

        # Keyboard capture
        if self.config.enable_keylogging:
            self.keyboard_capture = KeyboardCapture(
                on_keystroke=self._on_keystroke,
                on_hotkey=self._on_hotkey,
                hotkey_timeout=self.config.hotkey_timeout,
                hotkey_screenshot=self.config.hotkey_screenshot,
            )
            self.keyboard_capture.start(self.timeline.start_time)

        # Clipboard monitoring
        if self.config.enable_clipboard:
            self.clipboard_monitor = ClipboardMonitor(
                on_change=self._on_clipboard_change,
                on_image=self._on_clipboard_image,
                poll_interval=self.config.clipboard_poll_interval,
            )
            self.clipboard_monitor.start(self.timeline.start_time)

        # Start threads
        self.consumer_thread = threading.Thread(target=self._consume_events, daemon=True)
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)

        self.consumer_thread.start()
        self.audio_thread.start()
        self.display_thread.start()

    def wait(self) -> str:
        """Block until interrupted or voice stop command.

        Returns:
            "keyboard" if stopped by Ctrl+C, "voice" if stopped by voice command.
        """
        try:
            while self.running.is_set():
                if self._voice_stop_requested:
                    return "voice"
                time.sleep(0.1)
        except KeyboardInterrupt:
            return "keyboard"
        return "unknown"

    def stop(self):
        """Stop the recording session and generate outputs."""
        self.running.clear()
        self.timeline.stop()

        # Add session end event
        self.event_queue.put(
            Event(
                type=EventType.SESSION_END,
                timestamp_ms=self.timeline.get_timestamp_ms(),
                data={},
            )
        )

        # Stop capture modules
        if self.audio_capture:
            self.audio_capture.stop()

        if self.keyboard_capture:
            self.keyboard_capture.stop()
            if self.keyboard_capture.total_keystrokes == 0:
                console.print(
                    "[yellow]⚠ No keystrokes captured. Check Accessibility permissions.[/yellow]"
                )

        if self.clipboard_monitor:
            self.clipboard_monitor.stop()

        # Wait for threads to finish
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)

        if self.consumer_thread:
            self.consumer_thread.join(timeout=2.0)

        # Save raw audio
        if self.config.save_audio and self.audio_chunks and self.session_dir:
            self._save_audio()

        # Run second-pass transcription on full audio for better quality
        if self.config.save_audio and self.audio_chunks and self.session_dir:
            self._run_full_transcription()

        # Generate outputs
        if self.session_dir:
            self._generate_outputs()

    def _save_audio(self):
        """Save recorded audio as WAV file."""
        if not self.audio_chunks:
            return

        audio_path = self.session_dir / "audio.wav"
        audio_data = np.concatenate(self.audio_chunks, axis=0)
        audio_data = (audio_data * 32767).astype(np.int16)
        wavfile.write(str(audio_path), self.config.sample_rate, audio_data)
        console.print(f"[dim]Audio saved: {audio_path}[/dim]")

    def _run_full_transcription(self):
        """Run a second-pass transcription on the full audio for better quality.

        Real-time transcription uses small chunks and fast settings.
        This second pass processes the entire audio with higher quality settings.
        """
        if not self.transcription_worker or not self.transcription_worker.model:
            return

        console.print("[dim]Running full transcription (second pass)...[/dim]")

        try:
            # Concatenate all audio
            audio = np.concatenate(self.audio_chunks, axis=0)
            audio = audio.flatten().astype(np.float32)

            # Skip if audio is too short or too quiet
            if len(audio) < self.config.sample_rate:  # Less than 1 second
                return
            if np.abs(audio).max() < 0.01:
                return

            # Build vocabulary boost prompt
            vocab_boost = []
            if self.config.voice_trigger:
                vocab_boost.append(self.config.voice_trigger)
            if self.config.voice_stop:
                vocab_boost.extend(self.config.voice_stop.split())
            if self.config.vocabulary_boost:
                vocab_boost.extend(self.config.vocabulary_boost)

            initial_prompt = ""
            if vocab_boost:
                words = ", ".join(vocab_boost)
                initial_prompt = f"Voice commands include: {words}. "

            # Run transcription with higher quality settings
            segments, info = self.transcription_worker.model.transcribe(
                audio,
                beam_size=5,  # Higher beam size for better accuracy (vs 1 for real-time)
                language="en",
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,  # More sensitive than real-time
                ),
                initial_prompt=initial_prompt if initial_prompt else None,
                word_timestamps=True,  # Get word-level timestamps
            )

            # Collect all text
            text_parts = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    text_parts.append(text)

            self.full_transcript = " ".join(text_parts)

            # Filter out voice command words (trigger and stop words)
            self.full_transcript = self._filter_voice_commands(self.full_transcript)
            console.print(
                f"[dim]Full transcription complete ({len(self.full_transcript)} chars)[/dim]"
            )

        except Exception as e:
            console.print(f"[yellow]Full transcription failed: {e}[/yellow]")

    def _filter_voice_commands(self, text: str) -> str:
        """Remove voice command words from transcript.

        Filters out the voice trigger word (e.g., "marco") and stop word (e.g., "finito")
        including common Whisper mistranscriptions using fuzzy matching.
        """
        import re

        words_to_remove = []

        # Add voice trigger word and variations
        if self.config.voice_trigger:
            words_to_remove.append(self.config.voice_trigger)

        # Add voice stop word and variations
        if self.config.voice_stop:
            words_to_remove.append(self.config.voice_stop)

        if not words_to_remove:
            return text

        # Build pattern for each word (case-insensitive, with optional punctuation)
        filtered = text
        for word in words_to_remove:
            # Match the word with optional surrounding punctuation/whitespace
            # Also match common mistranscriptions (within edit distance 2)
            pattern = rf"\b{re.escape(word)}\b[,.\s]*"
            filtered = re.sub(pattern, "", filtered, flags=re.IGNORECASE)

            # Also try to match fuzzy variations by checking each word
            result_words = []
            for w in filtered.split():
                clean_w = w.strip(".,!?;:'\"")
                if _sounds_like(clean_w, word, threshold=2):
                    # Skip this word (it's a voice command)
                    continue
                result_words.append(w)
            filtered = " ".join(result_words)

        # Clean up extra whitespace
        filtered = re.sub(r"\s+", " ", filtered).strip()
        return filtered

    def _generate_outputs(self):
        """Generate markdown and JSON output files."""
        # Markdown output
        md_generator = MarkdownOutputGenerator(
            self.timeline,
            self.config,
            full_transcript=self.full_transcript,
            session_dir=self.session_dir,
        )
        md_path = self.session_dir / "recording.md"
        md_generator.save(md_path)
        console.print(f"[dim]Markdown saved: {md_path}[/dim]")

        # JSON output
        json_generator = JSONOutputGenerator(
            self.timeline, self.config, full_transcript=self.full_transcript
        )
        json_path = self.session_dir / "recording.json"
        json_generator.save(json_path)
        console.print(f"[dim]JSON saved: {json_path}[/dim]")
