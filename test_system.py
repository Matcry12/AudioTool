#!/usr/bin/env python3
"""
TTS Converter Test Script
Quick test to verify all components are working correctly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import tkinter
        print("OK tkinter - GUI framework available")
    except ImportError:
        print("FAIL tkinter - Not available (GUI won't work)")
        return False
    
    try:
        import edge_tts
        print("OK edge-tts - Text-to-speech engine available")
    except ImportError:
        print("FAIL edge-tts - Not available (install with: pip install edge-tts)")
        return False
    
    try:
        import asyncio
        print("OK asyncio - Async support available")
    except ImportError:
        print("FAIL asyncio - Not available (should be included with Python)")
        return False
    
    return True

def test_files():
    """Test if all required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        "tts_gui_py313.py",
        "tts_converter_py313.py", 
        "requirements.txt",
        "README.md",
        ".gitignore",
        "launch.bat"
    ]
    
    required_dirs = [
        "Source",
        "Output"
    ]
    
    all_good = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"OK {file}")
        else:
            print(f"FAIL {file} - Missing")
            all_good = False
    
    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print(f"OK {dir_name}/ directory")
        else:
            print(f"FAIL {dir_name}/ directory - Missing")
            all_good = False
    
    return all_good

def test_sample_file():
    """Test if sample file exists."""
    print("\nTesting sample files...")
    
    sample_file = Path("Source/script.txt")
    if sample_file.exists():
        size = sample_file.stat().st_size
        print(f"OK Sample file: {sample_file} ({size} bytes)")
        return True
    else:
        print("FAIL No sample file found in Source/")
        return False

def test_ffmpeg():
    """Test if ffmpeg is available."""
    print("\nTesting ffmpeg availability...")
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            print("OK ffmpeg - Available (audio merging will work)")
            return True
        else:
            print("WARN ffmpeg - Not working properly")
            return False
    except FileNotFoundError:
        print("WARN ffmpeg - Not found (audio merging won't work, but chunks will)")
        print("  Install from: https://ffmpeg.org/download.html")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("TTS Converter - System Test")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("File Structure Test", test_files),
        ("Sample File Test", test_sample_file),
        ("FFmpeg Test", test_ffmpeg),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL {test_name} - Error: {e}")
            results.append((test_name, False))
        print()
    
    print("=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("SUCCESS All tests passed! TTS Converter is ready to use.")
        print("Run 'python tts_gui_py313.py' or use 'launch.bat' to start.")
    else:
        print("WARNING Some tests failed. Check the errors above.")
        if passed >= 2:  # Core functionality works
            print("Core functionality should still work.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
