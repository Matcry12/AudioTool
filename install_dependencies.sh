#!/bin/bash

# TTS Converter - Install Dependencies for Ubuntu/Linux

echo ""
echo "=========================================="
echo "   Installing TTS Converter Dependencies"
echo "=========================================="
echo ""
echo "This will install the required packages for TTS Story Converter:"
echo "- edge-tts (Microsoft Edge Text-to-Speech)"
echo "- tkinter (GUI framework, if not already installed)"
echo ""
echo "Optional (install separately):"
echo "- ffmpeg for audio merging: sudo apt-get install ffmpeg"
echo ""
read -p "Press Enter to continue..."

echo ""
echo "Checking Python 3 version..."
python3 --version
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 using: sudo apt-get install python3 python3-pip"
    exit 1
fi

echo ""
echo "Checking pip installation..."
pip3 --version
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: pip3 is not installed"
    echo "Installing pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install pip3"
        exit 1
    fi
fi

echo ""
echo "Checking tkinter installation..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "tkinter not found - installing..."
    sudo apt-get install -y python3-tk
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to install tkinter"
        echo "You can install it manually with: sudo apt-get install python3-tk"
    fi
else
    echo "✓ tkinter is already installed"
fi

echo ""
echo "Installing dependencies from requirements.txt..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies"
    echo "Trying alternative installation method..."
    echo ""
    echo "Installing edge-tts directly..."
    pip3 install edge-tts
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install edge-tts"
        echo "Please check your internet connection and try again"
        exit 1
    fi
fi

echo ""
echo "Checking if ffmpeg is available..."
ffmpeg -version >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ ffmpeg is available - audio merging will work"
else
    echo "⚠ ffmpeg not found - audio merging will not work"
    echo "  You can still use individual chunk files"
    echo "  Install ffmpeg with: sudo apt-get install ffmpeg"
fi

echo ""
echo "Creating required directories..."
mkdir -p Source Output

echo ""
echo "=========================================="
echo "    Installation Complete!"
echo "=========================================="
echo ""
echo "✓ Python dependencies installed successfully"
echo "✓ TTS Converter is ready to use"
echo ""
echo "Next steps:"
echo "1. Run './launch.sh' to start the application"
echo "2. Choose the Python 3.13 GUI version (option 1)"
echo "3. Browse for a text file and convert to audio"
echo ""
echo "Optional:"
echo "- Install ffmpeg for automatic audio merging:"
echo "  sudo apt-get install ffmpeg"
echo "- Put your text files in the 'Source' folder"
echo ""
read -p "Press Enter to exit..."