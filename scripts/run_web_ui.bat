@echo off
echo Steam Game Scraper - Web UI
echo ============================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.x from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create and activate virtual environment if it doesn't exist
if not exist "..\venv" (
    echo Creating virtual environment...
    cd ..
    python -m venv venv
    cd scripts
)

REM Activate virtual environment
call ..\venv\Scripts\activate.bat

REM Install required packages for web UI
echo Installing/Updating required packages for Web UI...
python -m pip install --upgrade pip
pip install flask flask-socketio selenium beautifulsoup4 requests pandas tkcalendar webdriver_manager openpyxl

REM Clear screen and show startup info
cls
echo.
echo ========================================
echo   STEAM GAME SCRAPER - WEB UI
echo ========================================
echo.
echo Starting the web application...
echo.
echo Once started, you can access the Web UI at:
echo.
echo    http://localhost:5000
echo.
echo Features available:
echo  - Modern web interface
echo  - Real-time scraping progress
echo  - Database search and filtering
echo  - Export results (CSV, JSON, Excel)
echo  - Responsive design
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Start the Flask web application
cd ..\src
python app.py

REM Deactivate virtual environment when done
deactivate

pause