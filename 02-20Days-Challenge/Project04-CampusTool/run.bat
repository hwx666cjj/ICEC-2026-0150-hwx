@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ============================================
echo  Campus Notice Aggregator - run once
echo ============================================
echo.

set "PY="
rem 1) try py launcher
where py >nul 2>&1
if %errorlevel%==0 set "PY=py"

rem 1.5) try python command (Windows App Execution Alias / on PATH)
if not defined PY (
  where python >nul 2>&1
  if %errorlevel%==0 set "PY=python"
)

rem 2) try common user-install locations (no PATH needed)
if not defined PY (
  for %%i in (39 310 311 312 313 314) do (
    if not defined PY (
      if exist "%LOCALAPPDATA%\Programs\Python\Python%%i\python.exe" (
        set "PY=%LOCALAPPDATA%\Programs\Python\Python%%i\python.exe"
      )
    )
  )
)

rem 3) try common system-install locations
if not defined PY (
  for %%i in (39 310 311 312 313 314) do (
    if not defined PY (
      if exist "C:\Python%%i\python.exe" set "PY=C:\Python%%i\python.exe"
    )
  )
)

if not defined PY (
  echo ERROR: Python not found on this machine.
  echo.
  echo  Fix it in 3 steps:
  echo   1. Download Python 3 from  https://www.python.org/downloads/
  echo   2. Run the installer and TICK "Add python.exe to PATH"
  echo      (bottom of first screen; it is OFF by default).
  echo   3. If Windows still opens the Microsoft Store instead of running
  echo      Python, turn OFF the "python.exe" / "python3.exe" App Execution
  echo      Aliases:  Settings - Apps - Advanced app settings - App execution aliases.
  echo.
  echo  After installing, just double-click this file again.
  pause
  exit /b 1
)

echo Using Python: %PY%
echo.
%PY% src\campus_digest.py
echo.
echo Done. Open digest\ for today's summary; process_logs\ for telemetry.
pause
