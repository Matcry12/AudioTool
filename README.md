# TTS Story Converter

A cross-platform Python application that converts long text files to high-quality audio using Microsoft Edge Text-to-Speech (TTS). Supports both English and Vietnamese voices with smart text chunking and audio organization. Works on Windows, Ubuntu, and other Linux distributions.

## ✨ Features

- 🎙️ **High-quality voices**: English (Jenny Neural) and Vietnamese (Hoai My Neural)
- 📝 **Smart text chunking**: Respects sentence boundaries for natural audio flow
- 🖥️ **User-friendly GUI**: Easy-to-use interface with real-time progress tracking
- 📁 **Auto-organization**: Files automatically saved to Output folder
- 🔧 **Flexible options**: Keep or delete individual chunks after merging
- 🐍 **Python 3.13 compatible**: No dependency issues with latest Python
- 🔗 **Optional merging**: Automatic audio merging with ffmpeg (if installed)
- ⚡ **Robust generation**: Uses streaming method for reliable audio creation
- 🐧 **Cross-platform**: Works on Windows, Ubuntu, and other Linux distributions

## 🚀 Quick Start

### Ubuntu/Linux Quick Setup
```bash
# 1. Install dependencies
./install_dependencies.sh

# 2. Run the launcher
./launch.sh

# 3. Choose option 1 for the GUI version
```

### Full Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   
   **Windows:**
   ```bash
   pip install -r requirements.txt
   ```
   *Or run `install_dependencies.bat`*
   
   **Ubuntu/Linux:**
   ```bash
   pip3 install -r requirements.txt
   ```
   *Or run `./install_dependencies.sh`*

3. **Optional**: Install ffmpeg for automatic audio merging:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - **Ubuntu/Linux**: `sudo apt-get install ffmpeg`

### Usage

#### GUI Version (Recommended)

**Windows:**
```bash
python tts_gui_py313.py
```

**Ubuntu/Linux:**
```bash
python3 tts_gui_py313.py
```

#### Command Line Version
1. Edit `tts_converter_py313.py` settings:
   ```python
   INPUT_FILENAME = "Source/your_file.txt"
   VOICE_CHOICE = "English Female"  # or "Vietnamese Female"
   KEEP_CHUNKS = True  # Keep individual chunk files
   ```

2. Run the script:
   
   **Windows:**
   ```bash
   python tts_converter_py313.py
   ```
   
   **Ubuntu/Linux:**
   ```bash
   python3 tts_converter_py313.py
   ```

#### Easy Launcher

**Windows:** Double-click `launch.bat`

**Ubuntu/Linux:** Run `./launch.sh`

## 📂 Project Structure

```
TTS/
├── 🚀 launch.bat                    # Windows launcher
├── 🚀 launch.sh                     # Linux/Ubuntu launcher
├── 📦 install_dependencies.bat      # Windows dependency installer
├── 📦 install_dependencies.sh       # Linux/Ubuntu dependency installer
├── 🖥️ tts_gui_py313.py             # GUI version (Python 3.13)
├── 📜 tts_converter_py313.py        # Command line (Python 3.13)
├── 🖥️ tts_gui.py                   # GUI version (Legacy)
├── 📜 tts_converter.py              # Command line (Legacy)
├── 📖 README.md                     # This file
├── 🔧 requirements.txt              # Python dependencies
├── 📁 Source/                       # Input text files
│   ├── script.txt                  # Sample text file
│   └── your_stories.txt            # Your text files here
├── 📁 Output/                       # Generated audio files
│   ├── story_chunk_001.mp3         # Individual audio chunks
│   ├── story_chunk_002.mp3
│   └── story_merged.mp3            # Merged audio (if ffmpeg)
└── 📁 venv/                         # Python virtual environment
```

## 🎤 Voice Options

| Voice | Language | Code | Quality | Best For |
|-------|----------|------|---------|----------|
| **English Female (Jenny)** | English (US) | `en-US-JennyNeural` | High | Stories, narration, general content |
| **Vietnamese Female (Hoai My)** | Vietnamese | `vi-VN-HoaiMyNeural` | High | Vietnamese text, native pronunciation |

## ⚙️ Configuration Options

### GUI Settings
- **Voice selection**: Choose between English and Vietnamese
- **Chunk size**: 1000-2500 character ranges
- **Output filename**: Custom naming for generated files
- **Keep chunks**: Option to preserve individual audio files
- **Auto-merge**: Attempt merging with ffmpeg if available

### Command Line Settings
Edit the configuration section in `tts_converter_py313.py`:

```python
INPUT_FILENAME = "Source/script.txt"     # Path to input text file
OUTPUT_PREFIX = "story"                  # Prefix for output files
VOICE_CHOICE = "English Female"          # Voice selection
TRY_MERGE = True                         # Attempt ffmpeg merging
KEEP_CHUNKS = True                       # Keep individual chunks
```

## 🔧 Python Version Compatibility

### Python 3.13+ (Recommended)
- ✅ Use `tts_gui_py313.py` and `tts_converter_py313.py`
- ✅ No pydub dependency issues
- ✅ Individual chunk files always created
- ⚠️ Merging requires ffmpeg installation

### Python < 3.13 (Legacy)
- ✅ Use `tts_gui.py` and `tts_converter.py`
- ✅ Built-in audio merging with pydub
- ⚠️ May have audioop module compatibility issues

## 📋 Requirements

### Minimum (Python 3.13)
- Python 3.13+
- edge-tts
- tkinter (usually included with Python)

### Full Features
- Python 3.13+
- edge-tts
- tkinter
- ffmpeg (optional, for merging)

### Legacy Support (Python < 3.13)
- Python 3.7-3.12
- edge-tts
- pydub
- tkinter

## 🛠️ Installation Methods

### Method 1: Automatic

**Windows:**
```bash
install_dependencies.bat
```

**Ubuntu/Linux:**
```bash
./install_dependencies.sh
```

### Method 2: Manual

**Windows:**
```bash
# Install Python dependencies
pip install edge-tts

# Optional: Install ffmpeg for merging
# Download from: https://ffmpeg.org/download.html
```

**Ubuntu/Linux:**
```bash
# Install Python dependencies
pip3 install edge-tts

# Install tkinter if needed
sudo apt-get install python3-tk

# Optional: Install ffmpeg for merging
sudo apt-get install ffmpeg
```

### Method 3: Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Ubuntu/Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage Examples

### Example 1: Simple GUI Conversion
1. Run `python tts_gui_py313.py`
2. Click "Browse" and select `Source/script.txt`
3. Choose "English Female (Jenny)" voice
4. Click "Convert to Audio"
5. Audio files appear in `Output/` folder

### Example 2: Command Line Batch Processing
```python
# Edit tts_converter_py313.py
INPUT_FILENAME = "Source/my_novel.txt"
OUTPUT_PREFIX = "chapter1"
VOICE_CHOICE = "Vietnamese Female"
KEEP_CHUNKS = False  # Delete chunks after merge

# Run conversion
python tts_converter_py313.py
```

### Example 3: Multiple Files
```bash
# Process multiple files by running multiple times
# with different INPUT_FILENAME settings
```

## 🔍 Troubleshooting

### Common Issues

#### "No module named 'audioop'" Error
**Solution**: Use Python 3.13 compatible versions (`_py313.py` files)

#### No Audio Files Generated
**Causes & Solutions**:
- ❌ No internet connection → ✅ Edge TTS requires online access
- ❌ Invalid text file → ✅ Ensure UTF-8 encoding
- ❌ Empty text file → ✅ Add content to your text file

#### Merging Fails
**Solutions**:
- ✅ Install ffmpeg from https://ffmpeg.org/
- ✅ Use audio editor to manually combine chunks
- ✅ Chunks are numbered sequentially for easy ordering

#### GUI Won't Start
**Causes & Solutions**:
- ❌ tkinter not installed → ✅ Install tkinter: `pip install tk`
- ❌ Wrong Python version → ✅ Use Python 3.7+

### Performance Tips
- 📝 **Optimal chunk size**: 1500-2000 characters
- 🎯 **File organization**: Keep text files in `Source/` folder
- 💾 **Storage**: ~1MB per minute of generated audio
- ⚡ **Speed**: ~2-3 minutes processing time per minute of audio

## 🌐 Network Requirements

- **Internet connection required**: Edge TTS is a cloud-based service
- **Firewall**: Ensure Python can access Microsoft Edge TTS servers
- **Proxy**: May require proxy configuration in corporate environments

## 📊 Output Information

### File Naming Convention
```
{prefix}_chunk_{number:03d}.mp3
```

### Example Output
```
Output/
├── story_chunk_001.mp3    # 865.8 KB, ~2.5 min
├── story_chunk_002.mp3    # 874.4 KB, ~2.6 min
├── story_chunk_003.mp3    # 847.1 KB, ~2.4 min
└── story_merged.mp3       # 2.5 MB, ~7.5 min (if merged)
```

### Audio Specifications
- **Format**: MP3
- **Quality**: High (Edge TTS Neural voices)
- **Sample Rate**: 24kHz
- **Bitrate**: Variable (optimized by Edge TTS)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## ⚠️ Disclaimers

- **Microsoft Edge TTS**: This tool uses Microsoft's Edge Text-to-Speech service
- **Internet required**: Cloud-based TTS requires active internet connection
- **Usage limits**: Respect Microsoft's usage policies and rate limits
- **Audio quality**: Output quality depends on Edge TTS service

## 🆘 Support

### Getting Help
1. Check this README for common solutions
2. Review the console/log output for error messages
3. Ensure all requirements are properly installed
4. Verify internet connectivity for Edge TTS

### Reporting Issues
When reporting problems, include:
- Python version (`python --version`)
- Operating system
- Error messages (full traceback)
- Input file details (size, encoding)
- Steps to reproduce

---

**Made with ❤️ for creating high-quality audio content from text files.**
