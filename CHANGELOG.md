# Changelog

All notable changes to TTS Story Converter will be documented in this file.

## [2.0.0] - 2025-01-XX - Python 3.13 Compatibility Release

### Added
- ✨ **Python 3.13 compatibility** - New `_py313.py` versions that work with latest Python
- 📁 **Auto-move to Output folder** - Generated files automatically organized in Output/
- 🗑️ **Keep/Delete chunks option** - Choice to preserve or remove individual chunk files
- 🎤 **Vietnamese voice support** - Added `vi-VN-HoaiMyNeural` voice option
- 📋 **Comprehensive documentation** - Complete README with installation and usage guides
- 🧪 **System test script** - Automated testing of all components
- 📦 **Requirements.txt** - Proper dependency management
- 🚫 **Gitignore file** - Clean repository with appropriate exclusions
- 🚀 **Improved launcher** - Better batch file with version selection

### Changed
- 🔧 **Robust audio generation** - Switched from `communicate.save()` to streaming method
- 💾 **File organization** - All outputs now go to dedicated Output/ folder
- 🎮 **Enhanced GUI** - Added checkbox for chunk management
- 📝 **Better error handling** - More informative error messages and recovery
- 🎯 **Smart defaults** - Better configuration options for different use cases

### Fixed
- 🐛 **Python 3.13 audioop issues** - Removed pydub dependency for main versions
- 🔤 **Unicode encoding problems** - Fixed console output on Windows
- 📁 **File path handling** - More reliable absolute path usage
- 🎵 **Audio generation reliability** - Eliminated failed chunk issues

### Technical Details
- **New audio method**: Uses `edge_tts.Communicate().stream()` for reliability
- **Folder structure**: Source/ for inputs, Output/ for results
- **Dual compatibility**: Separate versions for Python 3.13+ and legacy versions
- **Optional merging**: ffmpeg integration for combining chunks
- **Voice support**: Both en-US-JennyNeural and vi-VN-HoaiMyNeural

## [1.0.0] - 2025-01-XX - Initial Release

### Added
- 🎙️ **Basic TTS conversion** - Text file to MP3 conversion
- 🖥️ **GUI interface** - User-friendly tkinter interface
- 📜 **Command line version** - Script-based conversion
- 🔀 **Text chunking** - Smart splitting at sentence boundaries
- 🔗 **Audio merging** - Combine chunks into single file
- 📊 **Progress tracking** - Real-time conversion status

### Features
- Edge TTS integration
- English voice support (Jenny Neural)
- Basic file management
- Simple error handling

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes

## Contributing

When adding entries:
1. Use the format: `### [Version] - YYYY-MM-DD - Description`
2. Group changes by type: Added, Changed, Deprecated, Removed, Fixed, Security
3. Use emojis for visual distinction
4. Include technical details when relevant
