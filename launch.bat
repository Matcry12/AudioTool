@echo off
title TTS Converter Launcher
echo.
echo ==========================================
echo    TTS Story Converter Launcher
echo ==========================================
echo.
echo Choose your option:
echo.
echo [1] GUI Version - Python 3.13 Compatible (RECOMMENDED)
echo [2] Command Line - Python 3.13 Compatible
echo [3] GUI Version - Original (requires pydub)
echo [4] Command Line - Original (requires pydub)
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting Python 3.13 compatible GUI version...
    python tts_gui_py313.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Starting Python 3.13 compatible command line version...
    echo Note: Edit tts_converter_py313.py to set your input file and voice
    pause
    python tts_converter_py313.py
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Starting original GUI version...
    echo Warning: This requires pydub to work properly
    python tts_gui.py
    goto end
)

if "%choice%"=="4" (
    echo.
    echo Starting original command line version...
    echo Note: Edit tts_converter.py to set your input file and voice
    echo Warning: This requires pydub to work properly
    pause
    python tts_converter.py
    goto end
)

if "%choice%"=="5" (
    echo.
    echo Goodbye!
    goto end
)

echo.
echo Invalid choice. Please try again.
pause

:end
echo.
echo Press any key to exit...
pause >nul
