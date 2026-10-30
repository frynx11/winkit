# Get a WinKit download without installing Python on the user's PC

WinKit is still implemented in Python/PySide6 internally, but the release packages bundle the Python runtime, PySide6/Qt libraries, psutil and the application. The end user does **not** install Python, PySide6, or .NET.

## Recommended: cloud build with GitHub Actions

1. Create a new GitHub repository.
2. Upload the **contents** of this project folder to the repository root (the `.github` folder must be included).
3. Open the repository's **Actions** tab.
4. Select **Build WinKit for Windows** and click **Run workflow**. A push to `main` or `master` also starts a build automatically.
5. When the run finishes successfully, open that run and download the `WinKit-Windows-2.0.0` artifact.
6. The artifact contains:
   - `WinKit_Setup_2.0.0.exe`: normal installer, installs under the current user's Local AppData and creates Start Menu shortcuts.
   - `WinKit_Portable_2.0.0.zip`: portable folder; extract the complete folder and run `WinKit.exe` inside it.

The Python installation in this workflow exists only on Microsoft's temporary GitHub Actions build machine. It is not copied as a requirement for the user to install: PyInstaller bundles the interpreter and required libraries into `dist/WinKit`.

## Build locally (developer-only)

A developer can run `build_exe.bat` on Windows. That build computer needs Python 3.10+ and the dependencies because it is compiling the app. This requirement does not apply to people who install or run the generated installer/portable package.

## What is bundled

- Python runtime used by the app
- PySide6 and the Qt runtime/plugins collected by PyInstaller
- psutil
- WinKit application code

## Notes

- Windows builds must be produced on Windows. The GitHub Actions workflow uses `windows-latest` for this reason.
- The installer does not request administrator rights; it installs for the current Windows user. WinKit may separately trigger Windows UAC for individual maintenance actions that genuinely require elevation.
- SmartScreen may show an unknown-publisher warning until the executable is code-signed. Do not bypass warnings for builds from an unknown or untrusted repository.
- The artifact is not a signed Microsoft Store package.
