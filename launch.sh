#!/bin/bash

# TTS Story Converter Launcher for Ubuntu/Linux

echo ""
echo "=========================================="
echo "    TTS Story Converter Launcher"
echo "=========================================="
echo ""
echo "Choose your option:"
echo ""
echo "[1] GUI Version - Python 3.13 Compatible (RECOMMENDED)"
echo "[2] Command Line - Python 3.13 Compatible"
echo "[3] GUI Version - Original (requires pydub)"
echo "[4] Command Line - Original (requires pydub)"
echo "[5] Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Starting Python 3.13 compatible GUI version..."
        python3 tts_gui_py313.py
        ;;
    2)
        echo ""
        echo "Starting Python 3.13 compatible command line version..."
        echo "Note: Edit tts_converter_py313.py to set your input file and voice"
        read -p "Press Enter to continue..."
        python3 tts_converter_py313.py
        ;;
    3)
        echo ""
        echo "Starting original GUI version..."
        echo "Warning: This requires pydub to work properly"
        python3 tts_gui.py
        ;;
    4)
        echo ""
        echo "Starting original command line version..."
        echo "Note: Edit tts_converter.py to set your input file and voice"
        echo "Warning: This requires pydub to work properly"
        read -p "Press Enter to continue..."
        python3 tts_converter.py
        ;;
    5)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid choice. Please try again."
        read -p "Press Enter to exit..."
        exit 1
        ;;
esac

echo ""
read -p "Press Enter to exit..."