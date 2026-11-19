@echo off
title Student Performance Prediction System - Launcher
color 0b

echo ======================================================================
echo       STUDENT PERFORMANCE PREDICTION SYSTEM
echo       A Real-Life Application Using Machine Learning Algorithms
echo       Developed by: P. Sree Sai Kiran & R. Harshavardhan
echo ======================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: Check if virtual environment exists; create if not
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Verifying and installing required packages...
pip install -r requirements.txt --quiet

:: Launch Browser after 2 seconds in background
start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:5000"

:: Start Flask Application
echo.
echo ======================================================================
echo  Flask Server starting at: http://127.0.0.1:5000
echo  Default Faculty Credentials:
echo    Username: admin
echo    Password: admin123
echo  Press Ctrl+C to stop the application server.
echo ======================================================================
echo.

python app.py

pause
