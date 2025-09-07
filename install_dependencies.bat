@echo off
title TTS Converter - Install Dependencies
echo.
echo ==========================================
echo    Installing TTS Converter Dependencies
echo ==========================================
echo.
echo This will install the required packages:
echo - edge-tts (Microsoft Edge Text-to-Speech)
echo - pydub (Audio processing)
echo.
echo Note: You may need ffmpeg for audio merging.
echo If merging fails, install ffmpeg from: https://ffmpeg.org/download.html
echo.
pause

echo.
echo Installing edge-tts...
pip install edge-tts
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install edge-tts
    pause
    exit /b 1
)

echo.
echo Installing pydub...
pip install pydub
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install pydub
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    Installation Complete!
echo ==========================================
echo.
echo All required packages have been installed.
echo You can now run the TTS Converter.
echo.
echo Next steps:
echo 1. Double-click "launch.bat" to start the application
echo 2. Choose the GUI version for the best experience
echo 3. If audio merging fails, install ffmpeg
echo.
pause
