"""Keystroke capture with hotkey detection using pynput."""

import time
from typing import Callable, Optional

from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class KeyboardCapture:
    """Captures keystrokes and detects hotkey sequences."""

    def __init__(
        self,
        on_keystroke: Optional[Callable[[str, int, bool], None]] = None,
        on_hotkey: Optional[Callable[[str], None]] = None,
        hotkey_timeout: float = 0.3,  # Max time between keys for hotkey
        hotkey_screenshot: str = "jj",  # Configurable hotkey sequence
    ):
        self.on_keystroke = on_keystroke
        self.on_hotkey = on_hotkey
        self.hotkey_timeout = hotkey_timeout
        self.hotkey_screenshot = hotkey_screenshot

        self.listener: Optional[keyboard.Listener] = None
        self.start_time: float = 0

        # Hotkey detection state - support multi-character sequences
        self.key_buffer: list[tuple[str, float]] = []  # (key, timestamp)

        # Debug counters
        self.total_keystrokes: int = 0
        self.hotkeys_triggered: int = 0

    def _get_key_str(self, key) -> tuple[str, bool]:
        """Convert pynput key to string representation.

        Returns: (key_string, is_special)
        """
        if isinstance(key, KeyCode):
            if key.char:
                return key.char, False
            # Virtual key code without character
            return f"<vk:{key.vk}>", True
        elif isinstance(key, Key):
            return f"<{key.name}>", True
        return str(key), True

    def _check_hotkey(self, current_time: float) -> Optional[str]:
        """Check if the key buffer matches any hotkey sequence.

        Returns the hotkey name if matched, None otherwise.
        """
        # Clean old keys from buffer
        self.key_buffer = [
            (k, t) for k, t in self.key_buffer if current_time - t < self.hotkey_timeout
        ]

        # Check for screenshot hotkey match
        if len(self.key_buffer) >= len(self.hotkey_screenshot):
            recent_keys = "".join(k for k, t in self.key_buffer[-len(self.hotkey_screenshot) :])
            if recent_keys == self.hotkey_screenshot:
                return "screenshot"

        return None

    def _on_press(self, key):
        """Handle key press event."""
        try:
            key_str, is_special = self._get_key_str(key)
        except Exception as e:
            print(f"[keyboard] Error getting key string: {e}")
            return

        self.total_keystrokes += 1
        current_time = time.time()
        timestamp_ms = int((current_time - self.start_time) * 1000)

        # Add to buffer for hotkey detection (only non-special keys)
        if not is_special:
            self.key_buffer.append((key_str, current_time))

            # Check for hotkey match
            matched_hotkey = self._check_hotkey(current_time)
            if matched_hotkey and self.on_hotkey:
                self.hotkeys_triggered += 1
                print(
                    f"[keyboard] Hotkey triggered: {matched_hotkey} (total: {self.hotkeys_triggered})"
                )
                self.on_hotkey(matched_hotkey)
                self.key_buffer.clear()  # Clear buffer after hotkey
                return  # Don't log the hotkey keys

        # Report keystroke
        if self.on_keystroke:
            self.on_keystroke(key_str, timestamp_ms, is_special)

    def start(self, start_time: float):
        """Start keyboard capture.

        Args:
            start_time: Session start time (time.time()) for timestamp calculation.
        """
        self.start_time = start_time
        try:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            print(f"[keyboard] Listener started, hotkey: {self.hotkey_screenshot}")
        except Exception as e:
            print(f"[keyboard] Failed to start listener: {e}")

    def stop(self):
        """Stop keyboard capture."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            print(
                f"[keyboard] Stopped. Total keystrokes: {self.total_keystrokes}, Hotkeys triggered: {self.hotkeys_triggered}"
            )
