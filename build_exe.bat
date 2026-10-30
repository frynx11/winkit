@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================================
echo WinKit 2.0 - Standalone Windows build
echo ========================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on this BUILD computer.
  echo This script is for developers building locally only.
  echo End users should download WinKit_Setup_2.0.0.exe or
  echo WinKit_Portable_2.0.0.zip from the GitHub Actions artifact.
  echo They do NOT need Python installed.
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo Python 3.10 or newer is required on the build computer.
  pause
  exit /b 1
)

echo [1/4] Installing build dependencies on this build computer...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo [2/4] Building a self-contained application folder...
python -m PyInstaller --clean --noconfirm --windowed --onedir --name WinKit --collect-all PySide6 --collect-submodules psutil --hidden-import psutil main.py
if errorlevel 1 goto :error
if not exist "dist\WinKit\WinKit.exe" goto :error

echo [3/4] Creating portable ZIP...
if not exist release mkdir release
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\WinKit' -DestinationPath 'release\WinKit_Portable_2.0.0.zip' -Force"
if errorlevel 1 goto :error

echo [4/4] Looking for Inno Setup to create an installer...
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
  "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer\WinKit.iss
  if errorlevel 1 goto :error
) else (
  echo Inno Setup was not found. Portable ZIP is ready.
  echo Install Inno Setup 6 to also create WinKit_Setup_2.0.0.exe.
)

echo.
echo BUILD COMPLETE.
echo Portable package: release\WinKit_Portable_2.0.0.zip
echo Installer, if Inno Setup is installed: release\WinKit_Setup_2.0.0.exe
echo End users do not need Python or .NET installed.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Review the error shown above.
pause
exit /b 1
