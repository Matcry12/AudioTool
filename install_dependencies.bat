@echo off
title TTS Converter - Install Dependencies
echo.
echo ==========================================
echo    Installing TTS Converter Dependencies
echo ==========================================
echo.
echo This will install the required packages for TTS Story Converter:
echo - edge-tts (Microsoft Edge Text-to-Speech)
echo.
echo Optional (install separately):
echo - ffmpeg for audio merging: https://ffmpeg.org/download.html
echo.
pause

echo.
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from: https://python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Trying alternative installation method...
    echo.
    echo Installing edge-tts directly...
    pip install edge-tts
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install edge-tts
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
)

echo.
echo Checking if ffmpeg is available...
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ffmpeg is available - audio merging will work
) else (
    echo ⚠ ffmpeg not found - audio merging will not work
    echo   You can still use individual chunk files
    echo   Install ffmpeg from: https://ffmpeg.org/download.html
)

echo.
echo ==========================================
echo    Installation Complete!
echo ==========================================
echo.
echo ✓ Python dependencies installed successfully
echo ✓ TTS Converter is ready to use
echo.
echo Next steps:
echo 1. Double-click "launch.bat" to start the application
echo 2. Choose the Python 3.13 GUI version (option 1)
echo 3. Browse for a text file and convert to audio
echo.
echo Optional:
echo - Install ffmpeg for automatic audio merging
echo - Put your text files in the "Source" folder
echo.
pause
