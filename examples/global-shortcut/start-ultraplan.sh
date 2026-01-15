#!/bin/bash
# Start ultraplan recording in a new terminal window
#
# Setup:
#   1. Copy to ~/bin/start-ultraplan.sh
#   2. chmod +x ~/bin/start-ultraplan.sh
#   3. Create Automator Quick Action (see README.md)
#   4. Assign keyboard shortcut in System Settings

# === CONFIGURATION ===

# Where to save recordings
RECORDING_DIR="$HOME/ultraplan-recordings"

# Terminal app (change if not using Ghostty)
TERMINAL_APP="/Applications/Ghostty.app/Contents/MacOS/ghostty"

# Recording options (uncomment/modify as needed)
ULTRAPLAN_OPTS=""
# ULTRAPLAN_OPTS="-m small"              # Better transcription accuracy
# ULTRAPLAN_OPTS="--no-keys"             # Disable keystroke logging
# ULTRAPLAN_OPTS="--device 'BlackHole 2ch'"  # Capture system audio

# Path to uv (find with: which uv)
UV_PATH="uv"
# UV_PATH="$HOME/.cargo/bin/uv"  # Use if uv not in PATH

# === END CONFIGURATION ===

# Create recording directory if needed
mkdir -p "$RECORDING_DIR"

# Build the command
CMD="cd '$RECORDING_DIR' && $UV_PATH run ultraplan record $ULTRAPLAN_OPTS"
CMD="$CMD; echo ''; echo 'Recording saved to $RECORDING_DIR'; echo 'Press Enter to close...'; read"

# Launch in terminal
"$TERMINAL_APP" -e "$CMD"
