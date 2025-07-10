@echo off
REM Setup script for MACAD-Thesis-MEP-Graph project (Windows)

echo Setting up MACAD-Thesis-MEP-Graph project...

REM Check if Python 3.12 is installed
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.12 is not installed or not available
    echo Please install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment with Python 3.12
echo Creating virtual environment with Python 3.12...
py -3.12 -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To activate the virtual environment in the future:
echo   venv\Scripts\activate.bat        (Command Prompt)
echo   .\venv\Scripts\Activate.ps1      (PowerShell)
echo.
echo To run the graph viewer:
echo   panel serve graph_viewer.py --show
echo.
pause
