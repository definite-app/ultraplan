"""Clipboard monitoring using pyperclip and macOS native APIs for images."""

import hashlib
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import pyperclip


def _get_clipboard_image_data() -> Optional[bytes]:
    """Get image data from clipboard using macOS native APIs.

    Returns PNG data if clipboard contains an image, None otherwise.
    """
    try:
        from AppKit import NSPasteboard, NSPasteboardTypePNG, NSPasteboardTypeTIFF
        from Foundation import NSData

        pasteboard = NSPasteboard.generalPasteboard()

        # Try PNG first, then TIFF
        for img_type in [NSPasteboardTypePNG, NSPasteboardTypeTIFF]:
            data = pasteboard.dataForType_(img_type)
            if data:
                # Convert to PNG if needed
                if img_type == NSPasteboardTypeTIFF:
                    from AppKit import NSBitmapImageRep
                    rep = NSBitmapImageRep.imageRepWithData_(data)
                    if rep:
                        png_data = rep.representationUsingType_properties_(4, None)  # 4 = PNG
                        if png_data:
                            return bytes(png_data)
                else:
                    return bytes(data)
        return None
    except ImportError:
        return None
    except Exception:
        return None


class ClipboardMonitor:
    """Monitors clipboard for content changes (text and images)."""

    def __init__(
        self,
        on_change: Optional[Callable[[str, int], None]] = None,
        on_image: Optional[Callable[[bytes, int], None]] = None,
        poll_interval: float = 0.5,
    ):
        self.on_change = on_change
        self.on_image = on_image
        self.poll_interval = poll_interval
        self.running = threading.Event()
        self.last_content: str = ""
        self.last_image_hash: str = ""
        self.start_time: float = 0
        self.thread: Optional[threading.Thread] = None

    def _monitor_loop(self):
        """Poll clipboard for changes."""
        while self.running.is_set():
            try:
                # Check for image first
                image_data = _get_clipboard_image_data()
                if image_data:
                    # Use hash to detect changes (avoid comparing large byte arrays)
                    img_hash = hashlib.md5(image_data).hexdigest()
                    if img_hash != self.last_image_hash:
                        timestamp_ms = int((time.time() - self.start_time) * 1000)
                        self.last_image_hash = img_hash
                        if self.on_image:
                            self.on_image(image_data, timestamp_ms)
                else:
                    # Check for text
                    current = pyperclip.paste()
                    if current and current != self.last_content:
                        timestamp_ms = int((time.time() - self.start_time) * 1000)
                        self.last_content = current
                        if self.on_change:
                            self.on_change(current, timestamp_ms)
            except Exception:
                # Clipboard may be locked or contain unsupported data
                pass
            time.sleep(self.poll_interval)

    def start(self, start_time: float):
        """Start clipboard monitoring.

        Args:
            start_time: Session start time (time.time()) for timestamp calculation.
        """
        self.start_time = start_time

        # Get initial clipboard state to avoid triggering on existing content
        try:
            self.last_content = pyperclip.paste() or ""
        except Exception:
            self.last_content = ""

        # Get initial image hash
        try:
            image_data = _get_clipboard_image_data()
            if image_data:
                self.last_image_hash = hashlib.md5(image_data).hexdigest()
        except Exception:
            pass

        self.running.set()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop clipboard monitoring."""
        self.running.clear()
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
