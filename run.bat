@echo off
echo ================================================================
echo FLOORPLAN GENIE - PRODUCTION ENGINE
echo ================================================================
echo Advanced CAD Processing ^& Intelligent Layout Generation
echo.

echo Stopping any existing processes...
taskkill /f /im python.exe 2>nul

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo Starting Production Engine...
echo ================================================================
echo Features:
echo   * Multi-sheet DXF/DWG/PDF parsing
echo   * Architectural element classification  
echo   * Intelligent ilot placement (10%%-35%% coverage)
echo   * Mandatory corridor network generation
echo   * Pixel-perfect professional rendering
echo   * Interactive legend and measurements
echo   * High-resolution export (300 DPI)
echo.
echo Access Points:
echo   Web Interface: http://localhost:5000
echo   API Endpoint:  http://localhost:5000/api/process
echo   API Status:    http://localhost:5000/api/status
echo ================================================================
echo.

cd /d "%~dp0"
python app.py

pause