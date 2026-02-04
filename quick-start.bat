@echo off
REM Quick Start Script for Stress Detection System
REM Run this script from the project root directory

echo ========================================
echo Stress Detection System - Quick Start
echo ========================================

REM Check if we're in the right directory
if not exist "strees_dection" (
    echo Error: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Setting up environment...

REM Navigate to Django project
cd strees_dection

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install Django==4.2.20 djangorestframework==3.15.2
pip install psycopg2-binary python-dotenv whitenoise
pip install djangorestframework-simplejwt PyJWT==2.4.0
pip install numpy pandas scikit-learn matplotlib librosa
pip install cryptography==3.4.8

REM Run migrations if needed
echo Running database migrations...
python manage.py migrate

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the full system, open THREE separate command prompts:
echo.
echo CMD 1 - Django Web Server:
echo   cd strees_dection
echo   venv\Scripts\activate.bat
echo   python manage.py runserver
echo.
echo CMD 2 - Rasa Actions Server:
echo   cd strees_dection
echo   "C:\Program Files\Python39\python.exe" -m rasa run actions --port 5055
echo.
echo CMD 3 - Rasa Core Server:
echo   cd strees_dection
echo   "C:\Program Files\Python39\python.exe" -m rasa run --enable-api --cors "*" --port 5005
echo.
echo Access the web application at: http://127.0.0.1:8000
echo.
pause