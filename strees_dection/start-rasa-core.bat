@echo off
REM Start Rasa Core Server
REM Run this script from the strees_dection directory

echo Starting Rasa Core Server on port 5005...

REM Use system Python to avoid virtual environment conflicts
"C:\Program Files\Python39\python.exe" -m rasa run --enable-api --cors "*" --port 5005

pause