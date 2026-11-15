@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ============================================
echo  Campus Notice Aggregator - run once
echo ============================================
echo.

set "PY="
rem 0) python-manager install (this machine's real Python - highest priority)
if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PY=%LOCALAPPDATA%\Python\bin\python.exe"

rem 1) try py launcher
if not defined PY (
  where py >nul 2>&1
  if %errorlevel%==0 set "PY=py"
)

rem 2) try python command on PATH
if not defined PY (
  where python >nul 2>&1
  if %errorlevel%==0 set "PY=python"
)

rem 3) classic per-user installs (no PATH needed)
if not defined PY (
  for %%i in (39 310 311 312 313 314 315) do (
    if not defined PY (
      if exist "%LOCALAPPDATA%\Programs\Python\Python%%i\python.exe" (
        set "PY=%LOCALAPPDATA%\Programs\Python\Python%%i\python.exe"
      )
    )
  )
)

rem 4) classic system installs
if not defined PY (
  for %%i in (39 310 311 312 313 314 315) do (
    if not defined PY (
      if exist "C:\Python%%i\python.exe" set "PY=C:\Python%%i\python.exe"
    )
  )
)

if not defined PY (
  echo ERROR: Python not found on this machine.
  echo.
  echo  Fix: install Python 3 from https://www.python.org/downloads/
  echo       and TICK "Add python.exe to PATH" on the first screen.
  echo %DATE% %TIME% - ERROR python not found >> process_logs\run_diagnostics.log
  timeout /t 8 >nul 2>&1
  exit /b 1
)

echo Using Python: %PY%
echo.
echo %DATE% %TIME% - START using %PY% >> process_logs\run_diagnostics.log

%PY% src\campus_digest.py
set "RC=%errorlevel%"
if "%RC%"=="0" (
  echo %DATE% %TIME% - OK exit=%RC% >> process_logs\run_diagnostics.log
) else (
  echo %DATE% %TIME% - FAIL exit=%RC% >> process_logs\run_diagnostics.log
)

echo.
echo Done. Open digest\ for summary; process_logs\ for telemetry.
rem auto-close after 8s (works for scheduled runs and manual double-click)
timeout /t 8 >nul 2>&1
