@echo off
REM Start Django Web Server
REM Run this script from the strees_dection directory

echo Starting Django Web Server...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Django development server
python manage.py runserver

pause