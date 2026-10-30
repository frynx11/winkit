@echo off
setlocal
cd /d "%~dp0"
echo This launcher is for running WinKit from source (developer mode).
echo End users should install WinKit_Setup_2.0.0.exe or run WinKit.exe
echo from the extracted portable package. No Python installation is needed.
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. For source mode only, install Python 3.10+.
  pause
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo WinKit source mode requires Python 3.10 or newer.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
python main.py
if errorlevel 1 pause
exit /b 0
:error
echo Could not prepare or start the source version.
pause
exit /b 1
