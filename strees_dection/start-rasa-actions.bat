@echo off
REM Start Rasa Actions Server
REM Run this script from the strees_dection directory

echo Starting Rasa Actions Server on port 5055...

REM Use system Python to avoid virtual environment conflicts
"C:\Program Files\Python39\python.exe" -m rasa run actions --port 5055

pause