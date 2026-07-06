# Camera File Cleaner

A small Windows tool to bulk-delete the low-resolution preview files that
DJI and GoPro cameras leave next to the real video files on the SD card.

| Extension | Camera | Content |
|-----------|--------|---------|
| `.LRF` | DJI | Low-resolution preview video |
| `.LRV` | GoPro | Low-resolution preview video |
| `.THM` | GoPro | Thumbnail image |

These files are only used for quick preview in the camera apps and can be
deleted safely — the original videos (MP4) are never touched.

![Python](https://img.shields.io/badge/python-3.x-blue) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## Features

- Lists all preview files in a folder and all its subfolders (so you can
  just select the root of the SD card) with size and modification date
- Checkboxes per file type (LRF / LRV / THM), all enabled by default
- Status bar with per-type counts and total size
- One button deletes everything shown in the list (with confirmation —
  deletion is permanent)
- Auto-refreshes the list whenever the window regains focus, so changes
  made in Explorer or a newly inserted SD card show up automatically
- Remembers the last folder and your file-type choices between runs
- Keyboard shortcuts: `Ctrl+O` open folder, `Del` delete, `F5` manual refresh

## Usage

**Option 1 - standalone exe (no Python required)**

Download `Camera_File_Cleaner.exe` and run it. Windows SmartScreen may warn
the first time because the exe is not code-signed; choose
"More info" → "Run anyway".

**Option 2 - run from source**

Requires Python 3 (Tkinter is included in the standard installer):

```
python camera_file_cleaner.py
```

## Building the exe yourself

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name Camera_File_Cleaner camera_file_cleaner.py
```

The result is written to `dist\Camera_File_Cleaner.exe`.
