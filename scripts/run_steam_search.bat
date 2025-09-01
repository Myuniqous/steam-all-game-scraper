@echo off
echo Steam Games Database Search
echo ========================
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
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install required packages
echo Installing/Updating required packages...
python -m pip install --upgrade pip
pip install pandas tkcalendar openpyxl

REM Run the search application
echo Starting Steam Database Search...
python steam_db_search.py

REM Deactivate virtual environment
deactivate

pause