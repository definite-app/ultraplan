"""CLI entry point for ultraplan."""

import click
import sounddevice as sd
from rich.console import Console

from ultraplan import __version__
from ultraplan.config import SessionConfig, get_default_sessions_dir

console = Console()


def list_audio_devices():
    """List all available audio input devices."""
    devices = sd.query_devices()
    console.print("\n[bold]Available Audio Devices:[/bold]\n")

    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            name = device["name"]
            channels = device["max_input_channels"]
            rate = int(device["default_samplerate"])
            marker = " [green](BlackHole)[/green]" if "BlackHole" in name else ""
            console.print(f"  [{i}] {name} ({channels}ch, {rate}Hz){marker}")

    console.print("\n[dim]Use --device 'Device Name' to select a device[/dim]")


@click.group()
@click.version_option(version=__version__)
def cli():
    """ultraplan - Record context for AI agent prompts.

    Capture audio transcription, keystrokes, clipboard, and screenshots
    to generate detailed context for AI coding assistants.
    """
    pass


def check_permissions(enable_keylogging: bool) -> tuple[bool, bool]:
    """Check macOS permissions before starting.

    Returns (accessibility_ok, screen_recording_ok)
    """
    from ultraplan.platform.macos import (
        is_macos,
        check_accessibility_permission,
        check_screen_recording_permission,
    )

    if not is_macos():
        return True, True

    accessibility_ok = True
    screen_ok = True

    if enable_keylogging:
        console.print("[dim]Checking accessibility permissions...[/dim]", end=" ")
        accessibility_ok = check_accessibility_permission()
        if accessibility_ok:
            console.print("[green]OK[/green]")
        else:
            console.print("[red]DENIED[/red]")
            console.print()
            console.print("[yellow]⚠ Accessibility permission required for keystroke logging[/yellow]")
            console.print()
            console.print("  To fix this:")
            console.print("  1. Open [bold]System Settings → Privacy & Security → Accessibility[/bold]")
            console.print("  2. Click [bold]+[/bold] and add your terminal app")
            console.print("  3. Toggle it [bold]ON[/bold]")
            console.print("  4. [bold]Restart your terminal[/bold]")
            console.print()

    console.print("[dim]Checking screen recording permissions...[/dim]", end=" ")
    screen_ok = check_screen_recording_permission()
    if screen_ok:
        console.print("[green]OK[/green]")
    else:
        console.print("[yellow]LIMITED[/yellow]")
        console.print("  Screenshots may show blank windows without permission.")

    return accessibility_ok, screen_ok


@cli.command()
@click.option(
    "-o",
    "--output",
    default=None,
    help="Output directory for recordings (default: ~/.ultraplan/sessions)",
)
@click.option(
    "-m",
    "--model",
    default="base",
    type=click.Choice(["tiny", "base", "small", "medium", "large-v3"]),
    help="Whisper model size",
)
@click.option(
    "--device",
    default=None,
    help="Audio input device name (use --list-devices to see options)",
)
@click.option(
    "--no-keys",
    is_flag=True,
    help="Disable keystroke logging",
)
@click.option(
    "--no-clipboard",
    is_flag=True,
    help="Disable clipboard monitoring",
)
@click.option(
    "--no-audio",
    is_flag=True,
    help="Disable audio recording (skip saving WAV file)",
)
@click.option(
    "--list-devices",
    is_flag=True,
    help="List available audio devices and exit",
)
@click.option(
    "--hotkey",
    default="jj",
    help="Hotkey sequence for screenshot (default: jj)",
)
@click.option(
    "--voice",
    default="marco",
    help="Voice trigger word for screenshot (default: marco)",
)
@click.option(
    "--voice-stop",
    default="finito",
    help="Voice phrase to stop recording (default: finito)",
)
@click.option(
    "--open/--no-open",
    default=True,
    help="Open the markdown file after recording (default: --open)",
)
@click.option(
    "--vocab",
    multiple=True,
    help="Add words to boost recognition (can use multiple times)",
)
def record(output, model, device, no_keys, no_clipboard, no_audio, list_devices, hotkey, voice, voice_stop, open, vocab):
    """Start a recording session.

    Press Ctrl+C to stop recording and generate output files.
    Press 'jj' (double-j quickly) to take a screenshot.
    """
    if list_devices:
        list_audio_devices()
        return

    console.print("\n[bold green]ultraplan[/bold green] - Recording Session\n")

    # Check permissions first
    accessibility_ok, screen_ok = check_permissions(not no_keys)

    if not accessibility_ok and not no_keys:
        console.print()
        if not click.confirm("Continue without keystroke logging?", default=True):
            console.print("[yellow]Aborted. Run 'ultraplan setup' for help.[/yellow]")
            return
        no_keys = True  # Disable keylogging since permission denied
        console.print()

    config = SessionConfig(
        output_dir=output if output else get_default_sessions_dir(),
        whisper_model=model,
        audio_device=device,
        enable_keylogging=not no_keys,
        enable_clipboard=not no_clipboard,
        save_audio=not no_audio,
        hotkey_screenshot=hotkey,
        voice_trigger=voice,
        voice_stop=voice_stop,
        vocabulary_boost=list(vocab) if vocab else None,
    )

    # Import here to avoid slow startup for --help
    from ultraplan.core.session import RecordingSession
    from ultraplan.platform.macos import notify_recording_started, notify_recording_stopped

    session = RecordingSession(config)

    console.print()
    console.print(f"  Output:     {config.output_dir.resolve()}")
    console.print(f"  Model:      whisper-{config.whisper_model}")
    console.print(f"  Device:     {config.audio_device or 'default'}")
    console.print(f"  Keylogging: {'enabled' if config.enable_keylogging else 'disabled'}")
    console.print(f"  Clipboard:  {'enabled' if config.enable_clipboard else 'disabled'}")
    console.print(f"  Save Audio: {'enabled' if config.save_audio else 'disabled'}")
    console.print(f"  Screenshot: type '{config.hotkey_screenshot}' or say \"{config.voice_trigger}\"")
    console.print(f"  Stop:       Ctrl+C or say \"{config.voice_stop}\" (fuh·nee·toh)")
    console.print()

    try:
        session.start()
        notify_recording_started()
        stop_reason = session.wait()  # Block until Ctrl+C or voice stop

        if stop_reason == "voice":
            console.print(f"\n[cyan]Voice command detected: \"{voice_stop}\"[/cyan]")
        console.print("[yellow]Stopping recording...[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping recording...[/yellow]")
    finally:
        session.stop()
        notify_recording_stopped()
        console.print(f"\n[green]Session saved to: {session.session_dir}[/green]")

        # Open markdown file if requested
        if open and session.session_dir:
            md_path = session.session_dir / "recording.md"
            if md_path.exists():
                import subprocess
                import platform
                console.print(f"[dim]Opening {md_path}...[/dim]")
                if platform.system() == "Darwin":
                    subprocess.run(["open", str(md_path)], check=False)
                elif platform.system() == "Windows":
                    subprocess.run(["start", str(md_path)], shell=True, check=False)
                else:  # Linux
                    subprocess.run(["xdg-open", str(md_path)], check=False)


@cli.command()
def setup():
    """Check system requirements and show setup instructions."""
    from ultraplan.platform.macos import check_setup

    check_setup()


if __name__ == "__main__":
    cli()
