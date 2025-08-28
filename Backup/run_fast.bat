@echo off
echo === FAST FLOORPLAN GENIE ===
echo Stopping any existing processes...
taskkill /f /im python.exe 2>nul

echo Starting optimized engine...
cd /d "%~dp0"
python app_fast.py

pause