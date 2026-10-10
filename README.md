# Karaoke Manager - Interactive Queue List

## Features

✅ **Interactive Queue with Full Control:**
- View all songs in queue
- Play any song directly from queue
- Delete songs from queue
- Move songs up/down to reorder

✅ **Music Search & Library:**
- Search songs by title
- Browse local music folder
- Support for MP3, MP4, MKV, AVI, MOV, WMV, WEBM, WAV, FLAC

✅ **Playback Controls:**
- Play next, pause, stop
- Repeat mode
- Volume control with mute
- Seek slider with time display

✅ **Video Output:**
- Main screen video display
- Secondary screen support (dual monitor karaoke)
- Fullscreen mode

## Requirements

- Windows 10 or Windows 11
- Python 3.11+ (for development)
- **VLC Media Player** must be installed on target PC

## Quick Start - Windows

### Option 1: Automatic Build & ZIP

```bash
build_and_zip.bat
```

This creates: `karaoke_manager_windows.zip`

### Option 2: Manual Build

1. Open Command Prompt in this folder

2. Install dependencies:
```bash
py -m pip install -r requirements.txt
```

3. Build EXE:
```bash
py build_exe.py
```

4. Output: `dist\karaoke_manager.exe`

### Option 3: Compress Manually

- Right-click `dist` folder
- Send to > Compressed (zipped) folder

## Usage

1. Click **📁 Select Music/Video Folder**
2. Search for songs or browse results
3. Click **＋ Add** to add to queue
4. In queue, use buttons:
   - **▶** = Play this song now
   - **↑** = Move up in queue
   - **↓** = Move down in queue
   - **✕** = Delete from queue
5. Use **▶ Play Next** to play first song in queue

## Queue Controls

| Button | Action |
|--------|--------|
| ▶ | Play song immediately |
| ↑ | Move song up in queue |
| ↓ | Move song down in queue |
| ✕ | Remove from queue |

## System Requirements

- **Windows:** 10 or 11
- **RAM:** 2GB minimum
- **Storage:** ~200MB for app
- **VLC:** Required for playback

## Distribution

The ZIP file contains:
- `karaoke_manager.exe` - Main application
- All required libraries bundled

**Installation on target PC:**
1. Extract ZIP
2. Install VLC Media Player (if not installed)
3. Run `karaoke_manager.exe`

## Notes

- VLC Media Player must be installed separately on each PC
- The app scans all subfolders for media files
- Queue persists until app is closed
- Supports dual monitor karaoke setup

## Made by David/Daviro
