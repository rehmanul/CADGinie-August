@echo off
echo ===============================================
echo    FLOORPLAN GENIE - INSTALLATION SCRIPT
echo    Professional CAD Analysis Engine Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✓ Python found
python --version

echo.
echo 📦 Installing required packages...
echo.

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install requirements
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Installation failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Installation completed successfully!
echo.
echo 🚀 To start the application, run:
echo    python run.py
echo.
echo 📍 Then open your browser to: http://localhost:5000
echo.
pause