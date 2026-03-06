@echo off
echo Stopping all Python processes on port 5000...
echo.

REM Find and kill processes on port 5000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    echo Killing process %%a...
    taskkill /F /PID %%a 2>nul
)

echo.
echo All processes stopped.
echo.
echo Starting Flask app...
python app.py
