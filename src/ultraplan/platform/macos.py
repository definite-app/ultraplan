"""macOS-specific utilities for ultraplan."""

import platform
import subprocess
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def check_blackhole_installed() -> bool:
    """Check if BlackHole virtual audio driver is installed."""
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        for d in devices:
            if "BlackHole" in d["name"]:
                return True
        return False
    except Exception:
        return False


def check_accessibility_permission() -> bool:
    """Check if app has accessibility permissions for keyboard monitoring.

    This performs a real test by trying to capture keyboard events.
    Uses AppleScript to check the actual permission state on macOS.
    """
    if not is_macos():
        return True  # Assume OK on non-macOS

    # First, try the AppleScript-based check which is more reliable
    try:
        # This AppleScript will prompt for permission if not granted
        # We just want to check, not prompt, so we use a different approach
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to return (UI elements enabled)'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # If we get "true", accessibility is enabled for something
        # But this doesn't guarantee our specific app has permission
    except Exception:
        pass

    # Capture stderr to detect the "not trusted" warning from pynput
    import io

    old_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        from pynput import keyboard

        def on_press(key):
            pass

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Give it a moment to potentially fail - increased from 0.1s
        import time

        time.sleep(0.3)

        listener.stop()

        # Check if the warning was printed
        stderr_output = sys.stderr.getvalue()
        if "not trusted" in stderr_output.lower() or "Input event monitoring" in stderr_output:
            return False

        return True
    except Exception:
        return False
    finally:
        sys.stderr = old_stderr


def check_screen_recording_permission() -> bool:
    """Check if app has screen recording permissions for screenshots."""
    if not is_macos():
        return True

    try:
        import mss

        with mss.mss() as sct:
            # Try to capture a small region
            sct.grab(sct.monitors[0])
        return True
    except Exception:
        return False


# =============================================================================
# Notifications
# =============================================================================


def play_sound(sound_name: str = "Ping") -> None:
    """Play a system sound on macOS.

    Available sounds: Basso, Blow, Bottle, Frog, Funk, Glass, Hero,
    Morse, Ping, Pop, Purr, Sosumi, Submarine, Tink
    """
    if not is_macos():
        # Terminal bell fallback
        print("\a", end="", flush=True)
        return

    try:
        subprocess.run(
            ["afplay", f"/System/Library/Sounds/{sound_name}.aiff"],
            capture_output=True,
            timeout=2,
        )
    except Exception:
        print("\a", end="", flush=True)  # Fallback to terminal bell


def send_notification(
    title: str,
    message: str,
    sound: bool = True,
    subtitle: Optional[str] = None,
) -> None:
    """Send a macOS notification using osascript.

    Args:
        title: Notification title
        message: Notification body
        sound: Whether to play a sound
        subtitle: Optional subtitle
    """
    if not is_macos():
        console.print(f"[bold]{title}[/bold]: {message}")
        return

    sound_str = 'sound name "Ping"' if sound else ""
    subtitle_str = f'subtitle "{subtitle}"' if subtitle else ""

    script = f'display notification "{message}" with title "{title}" {subtitle_str} {sound_str}'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        # Fallback to console
        console.print(f"[bold]{title}[/bold]: {message}")


def notify_screenshot_taken(filename: str) -> None:
    """Notify user that a screenshot was taken."""
    play_sound("Pop")
    # Don't send system notification for every screenshot - too noisy
    # Just the sound is enough feedback


def notify_recording_started() -> None:
    """Notify user that recording has started."""
    play_sound("Blow")


def notify_recording_stopped() -> None:
    """Notify user that recording has stopped."""
    send_notification(
        title="ultraplan",
        message="Recording stopped. Output files saved.",
        sound=True,
    )


def get_setup_instructions() -> str:
    """Get setup instructions for macOS system audio capture."""
    return """
To capture system audio on macOS, you need to set up a virtual audio device:

1. Install BlackHole (virtual audio driver):
   brew install blackhole-2ch

2. Open Audio MIDI Setup:
   /Applications/Utilities/Audio MIDI Setup.app

3. Create a Multi-Output Device:
   - Click the '+' button at bottom left
   - Select 'Create Multi-Output Device'
   - Check BOTH your speakers/headphones AND 'BlackHole 2ch'
   - Optionally rename it to 'Ultraplan Audio'

4. Set as system output:
   - System Settings > Sound > Output
   - Select your new Multi-Output Device

5. Run ultraplan with BlackHole as input:
   uv run ultraplan record --device "BlackHole 2ch"

Note: You'll hear audio through your speakers/headphones normally,
while ultraplan captures it via BlackHole.
"""


def check_setup():
    """Check macOS setup and display status."""
    if not is_macos():
        console.print("[yellow]Note: This setup guide is for macOS.[/yellow]")
        console.print("For other platforms, consult your OS documentation for audio routing.")
        return

    console.print("\n[bold]macOS Setup Check[/bold]\n")

    # Check BlackHole
    blackhole_ok = check_blackhole_installed()
    if blackhole_ok:
        console.print("[green]✓[/green] BlackHole virtual audio driver found")
    else:
        console.print("[red]✗[/red] BlackHole not found")

    # Check accessibility permissions
    accessibility_ok = check_accessibility_permission()
    if accessibility_ok:
        console.print("[green]✓[/green] Accessibility permissions granted")
    else:
        console.print(
            "[yellow]![/yellow] Accessibility permissions may be needed for keystroke logging"
        )
        console.print("  Go to: System Settings > Privacy & Security > Accessibility")
        console.print("  Add your terminal app (Terminal, iTerm2, etc.)")

    # Show instructions if BlackHole not installed
    if not blackhole_ok:
        console.print(
            Panel(get_setup_instructions(), title="Setup Instructions", border_style="blue")
        )
    else:
        console.print("\n[green]Your system appears ready for audio capture![/green]")
        console.print("\nTo start recording:")
        console.print('  uv run ultraplan record --device "BlackHole 2ch"')
