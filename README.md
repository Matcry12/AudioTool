# TTS Project Folder

## ⚠️ Python 3.13 Compatibility Issue

**IMPORTANT:** If you're using Python 3.13, use the `_py313` versions of the scripts. The original versions require `pydub` which is not compatible with Python 3.13 due to the removal of the `audioop` module.

## Structure

```
TTS/
├── 🚀 launch.bat                    # Main launcher (choose your version)
├── 📦 install_dependencies.bat      # Install required packages
├── 🖥️ tts_gui_py313.py             # GUI - Python 3.13 Compatible (RECOMMENDED)
├── 📜 tts_converter_py313.py        # Command line - Python 3.13 Compatible
├── 🖥️ tts_gui.py                   # GUI - Original (requires pydub)
├── 📜 tts_converter.py              # Command line - Original (requires pydub)
├── 📖 README.md                     # This file
├── Source/                          # Input text files
│   ├── rezero_1-3_en.txt           # English source text
│   ├── rezero_1-3_vi.txt           # Vietnamese source text
│   ├── script.txt                  # Sample/test text
│   └── Rezero chapter 0 - 3.docx   # Original document
├── Output/                          # Generated audio files
│   ├── Chapter_0_EN.mp3            # Generated chapter audio
│   ├── Chapter_0_EN.srt            # Subtitle files
│   ├── Chapter_1_EN.mp3
│   ├── Chapter_1_EN.srt
│   ├── Chapter_2_EN.mp3
│   ├── Chapter_2_EN.srt
│   └── Chapter_1_3_EN.mp3
└── venv/                            # Python virtual environment
```

## Quick Start

1. **Double-click `launch.bat`**
2. **Choose option 1** (Python 3.13 compatible GUI)
3. **Browse for your text file**
4. **Select voice** (English or Vietnamese)
5. **Click "Convert to Audio"**

## Usage Options

### Option 1: Python 3.13 Compatible GUI (RECOMMENDED)
```bash
python tts_gui_py313.py
```
- **User-friendly interface**
- **Individual chunk files** (e.g., `story_chunk_001.mp3`, `story_chunk_002.mp3`)
- **Optional ffmpeg merging** (if ffmpeg is installed)
- **Voice selection** (English/Vietnamese)
- **Real-time progress** tracking

### Option 2: Python 3.13 Compatible Command Line
```bash
python tts_converter_py313.py
```
- Edit line 212: `INPUT_FILENAME = "Source/your_file.txt"`
- Edit line 214: `VOICE_CHOICE = "English Female"` or `"Vietnamese Female"`

### Option 3: Original Versions (Python < 3.13 only)
- `tts_gui.py` - Full merging capabilities with pydub
- `tts_converter.py` - Auto-merging into single file

## Voice Options

| Voice | Language | Code | Quality |
|-------|----------|------|---------|
| **English Female (Jenny)** | English (US) | `en-US-JennyNeural` | High |
| **Vietnamese Female (Hoai My)** | Vietnamese | `vi-VN-HoaiMyNeural` | High |

## Requirements

### Minimum (Python 3.13 Compatible)
```bash
pip install edge-tts
```

### Full Features (Python < 3.13)
```bash
pip install edge-tts pydub
```

### Optional (For Merging in Python 3.13)
- **ffmpeg** - Download from https://ffmpeg.org/download.html

## Python 3.13 vs Original Versions

| Feature | Python 3.13 Version | Original Version |
|---------|---------------------|------------------|
| **Text Chunking** | ✅ Smart sentence boundaries | ✅ Smart sentence boundaries |
| **Voice Options** | ✅ English & Vietnamese | ✅ English & Vietnamese |
| **Individual Chunks** | ✅ Always created | ✅ Always created |
| **Auto-merging** | ⚠️ Only with ffmpeg | ✅ Built-in with pydub |
| **File Cleanup** | ✅ Optional | ✅ Optional |
| **GUI Interface** | ✅ Full featured | ✅ Full featured |

## Troubleshooting

### "No module named 'audioop'" Error
- **Solution:** Use the `_py313` versions of the scripts
- **Cause:** Python 3.13 removed the `audioop` module that `pydub` depends on

### No Merged Audio File
- **For Python 3.13:** Install ffmpeg for automatic merging
- **Alternative:** Use any audio editor to manually combine the chunk files
- **Order:** Files are numbered sequentially (`chunk_001.mp3`, `chunk_002.mp3`, etc.)

### Edge TTS Not Working
- **Check internet connection** (Edge TTS requires online access)
- **Verify installation:** `pip install edge-tts`

## Output Files

### Python 3.13 Version Creates:
- Individual chunks: `story_chunk_001.mp3`, `story_chunk_002.mp3`, etc.
- Optional merged file: `story_merged.mp3` (if ffmpeg available)

### Original Version Creates:
- Individual chunks: `chunk_001.mp3`, `chunk_002.mp3`, etc.
- Merged file: `story_audio.mp3` (automatic with pydub)
