@echo off
REM Hostel Management System - Setup Script for Windows

echo ==================================
echo Hostel Management System Setup
echo ==================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version

if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Python is installed
echo.

REM Create virtual environment
set /p create_venv="Do you want to create a virtual environment? (y/n): "

if /i "%create_venv%"=="y" (
    echo Creating virtual environment...
    python -m venv venv
    
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo Virtual environment created and activated
    echo.
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully
echo.

REM Create necessary directories
echo Creating required directories...
if not exist "static\images" mkdir static\images
if not exist "static\qr" mkdir static\qr

echo Directories created
echo.

REM Initialize database
echo Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized successfully')"

echo.

REM Display completion message
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo To run the application:
echo.
if /i "%create_venv%"=="y" (
    echo 1. Activate virtual environment if not already active:
    echo    venv\Scripts\activate.bat
    echo.
)
echo 2. Start the server:
echo    python app.py
echo.
echo 3. Open your browser and go to:
echo    http://localhost:5000
echo.
echo Default Admin Credentials:
echo    Username: admin
echo    Password: admin123
echo.
echo WARNING: Change admin password in production!
echo.
echo ==================================

pause
