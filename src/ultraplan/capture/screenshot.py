"""Screenshot capture using mss."""

from pathlib import Path

import mss
import mss.tools


class ScreenshotCapture:
    """Captures screenshots using mss (fast cross-platform)."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, timestamp_ms: int) -> str:
        """Take screenshot and save to file.

        Args:
            timestamp_ms: Milliseconds since session start.

        Returns:
            Filename (not full path) of saved screenshot.
        """
        filename = f"img_{timestamp_ms:06d}.png"
        filepath = self.output_dir / filename

        with mss.mss() as sct:
            # Capture all monitors (monitor[0] is the combined virtual screen)
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(filepath))

        return filename
