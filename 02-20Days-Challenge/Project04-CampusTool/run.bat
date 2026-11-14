@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ============================================
echo  Campus Notice Aggregator - run once
echo ============================================
echo.
py src\campus_digest.py
if errorlevel 1 python src\campus_digest.py
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3 and tick "Add python.exe to PATH".
  echo Download: https://www.python.org/downloads/
  pause
  exit /b 1
)
echo.
echo Done. Open the digest\ folder for today's summary,
echo and process_logs\ for the telemetry log.
pause
