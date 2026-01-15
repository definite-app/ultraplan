# Global Keyboard Shortcut (macOS)

Start ultraplan recording from anywhere with a system-wide keyboard shortcut.

## Setup

### 1. Create the Launch Script

```bash
mkdir -p ~/bin
```

Create `~/bin/start-ultraplan.sh`:

```bash
#!/bin/bash
# Start ultraplan recording in a new terminal window

# Where to save recordings (change this to your preferred location)
RECORDING_DIR="$HOME/ultraplan-recordings"

# Create directory if it doesn't exist
mkdir -p "$RECORDING_DIR"

# Change to recording directory and start ultraplan
cd "$RECORDING_DIR"

# Launch in Ghostty (change this if you use a different terminal)
/Applications/Ghostty.app/Contents/MacOS/ghostty -e "uv run ultraplan record; echo 'Recording saved. Press Enter to close.'; read"
```

Make it executable:
```bash
chmod +x ~/bin/start-ultraplan.sh
```

### 2. Create Automator Quick Action

1. Open **Automator** (Spotlight → "Automator")
2. Click **New Document**
3. Select **Quick Action** → Create
4. Configure the workflow:
   - Set **"Workflow receives"** to **"no input"**
   - Set **"in"** to **"any application"**
5. From the left sidebar, drag **"Run Shell Script"** to the workflow area
6. Set **"Shell"** to `/bin/bash`
7. Replace the script content with:
   ```bash
   ~/bin/start-ultraplan.sh
   ```
8. **File → Save** as `Start Ultraplan Recording`

### 3. Assign Keyboard Shortcut

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Keyboard** → **Keyboard Shortcuts**
3. Select **Services** (or **App Shortcuts** → **Services**) in the left sidebar
4. Find **"Start Ultraplan Recording"** under **General**
5. Click **"none"** next to it and press your desired shortcut
   - Suggested: `⌃⌥U` (Control + Option + U)

### 4. Test It

Press your shortcut from any app. A new Ghostty window should open and start recording.

Press `Ctrl+C` in the terminal to stop recording.

## Customization

### Change Recording Directory

Edit `~/bin/start-ultraplan.sh` and change `RECORDING_DIR`:
```bash
RECORDING_DIR="$HOME/Documents/meeting-notes"
```

### Use Different Terminal

**iTerm2:**
```bash
osascript -e 'tell application "iTerm"
    create window with default profile
    tell current session of current window
        write text "cd ~/ultraplan-recordings && uv run ultraplan record"
    end tell
end tell'
```

**Terminal.app:**
```bash
osascript -e 'tell application "Terminal"
    do script "cd ~/ultraplan-recordings && uv run ultraplan record"
    activate
end tell'
```

**Kitty:**
```bash
/Applications/kitty.app/Contents/MacOS/kitty --directory ~/ultraplan-recordings -e uv run ultraplan record
```

### Add Recording Options

Edit the script to include options:
```bash
# Use small model for better accuracy
uv run ultraplan record -m small

# Disable keystroke logging
uv run ultraplan record --no-keys

# Capture system audio (requires BlackHole)
uv run ultraplan record --device "BlackHole 2ch"
```

## Troubleshooting

### Shortcut Not Working

1. Check System Settings → Privacy & Security → Accessibility
2. Ensure Automator has permission (may need to add it)
3. Try logging out and back in after creating the service

### "uv not found"

The script runs in a minimal shell. Add the full path to uv:
```bash
~/.cargo/bin/uv run ultraplan record
# or wherever uv is installed
```

Find it with: `which uv`

### Terminal Closes Immediately

Make sure the script waits for input at the end:
```bash
uv run ultraplan record; echo 'Done. Press Enter.'; read
```

### Recording Directory

By default, recordings go to `~/ultraplan-recordings`. Each session creates:
```
~/ultraplan-recordings/session_YYYYMMDD_HHMMSS/
├── recording.md
├── recording.json
├── audio.wav
└── img_*.png
```
