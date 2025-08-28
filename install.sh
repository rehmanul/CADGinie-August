#!/bin/bash

echo "==============================================="
echo "   FLOORPLAN GENIE - INSTALLATION SCRIPT"
echo "   Professional CAD Analysis Engine Setup"
echo "==============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

echo "✓ Python found"
python3 --version

echo
echo "📦 Installing required packages..."
echo

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Upgrade pip
python3 -m pip install --upgrade pip

# Install requirements
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "❌ Installation failed!"
    echo "Please check the error messages above."
    exit 1
fi

echo
echo "✅ Installation completed successfully!"
echo
echo "🚀 To start the application, run:"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   source venv/bin/activate  # (if using virtual environment)"
fi
echo "   python3 run.py"
echo
echo "📍 Then open your browser to: http://localhost:5000"
echo