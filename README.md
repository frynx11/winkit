# WinKit 2.0

WinKit is a Windows 10/11 maintenance, diagnostics and productivity hub built with **Python + PySide6**.

## What's included in 2.0

### Interface
- New desktop UI built with PySide6 rather than Tkinter.
- Four themes: Dark Fluent, Clean Light, Midnight and Graphite.
- Animated page transitions, staggered card fade-ins, hover and pressed states.
- Arabic, English and French interface languages, with right-to-left layout in Arabic.
- Quick search (`Ctrl+K`), category filtering, favorites and recent activity.

### Windows tools
- 38 searchable actions across cleanup, repair, network, performance, gaming, appearance and system shortcuts.
- Preserved core tools: user Temp cleanup, Recycle Bin, SFC, DISM, Windows Update, DNS flush, IP details, Winsock and TCP/IP reset, startup settings, power settings, Game Mode, Windows theme switching, Task Manager, Device Manager and more.
- High-impact operations require confirmation. Administrator operations use the normal Windows UAC prompt.

### New centers
- **Smart Fix Center:** network diagnostics for IP configuration, DNS resolution and a basic external TCP connection check.
- **Performance Studio:** a low-end visual-effects preset limited to current-user preferences, with backup and restore. It does not promise FPS gains.
- **Hardware Monitor:** CPU, RAM, system-drive usage and uptime, plus the top memory-consuming processes when `psutil` is available.
- **Software Center:** WinGet installed-app list, update preview, confirmed update-all, and export/import of WinGet app manifests.
- **Disk Analyzer:** largest files and file-type size totals. Read-only, skips symlinks/reparse points, and caps each scan at 50,000 files.
- **SHA-256 checker:** calculate a file's SHA-256 hash.
- **System Report:** locally generated HTML report containing basic OS, hardware, disk, network adapter and optional WinGet app details.

## End-user installation (no Python required)

The recommended release is the Windows installer or portable package produced by GitHub Actions. PyInstaller bundles the Python runtime, PySide6/Qt and psutil into the application package. End users do **not** need to install Python, PySide6, or .NET.

See [BUILD_WINDOWS.md](BUILD_WINDOWS.md) for the cloud-build steps and how to download the ready-to-use `WinKit_Setup_2.0.0.exe` or `WinKit_Portable_2.0.0.zip`.

WinGet (App Installer) is optional; the Software Center explains when it is missing. Internet access is needed only for build dependencies and online WinGet sources. The application itself does not upload reports or settings.

## Run from source (developer mode only)

Running `main.py` directly is optional and requires Python 3.10+ with the dependencies in `requirements.txt`. End users should use the installer or portable build instead.

## Build locally (developer mode only)

On a Windows build computer, `build_exe.bat` creates a self-contained folder in `dist\WinKit` and a portable ZIP. If Inno Setup 6 is installed, it also creates `release\WinKit_Setup_2.0.0.exe`. The build computer needs Python, but the generated packages bundle the runtime for end users.

## Safety and limitations

- Registry presets modify current-user (`HKCU`) visual preferences only. Original values are backed up before the first change in each group.
- Temp cleanup is limited to the current user's TEMP directory and does not traverse symlinks/reparse points. Locked or protected entries are skipped.
- Recycle Bin emptying is marked high impact and always requires confirmation.
- Software update-all is blocked until the user runs the update preview and explicitly confirms. WinGet runs in a visible console.
- Importing a WinGet manifest previews package identifiers and requires confirmation before installation.
- Disk Analyzer reads but never deletes files. It has a 50,000-file scan cap.
- System reports are local. Review them before sharing because they may contain device and network adapter information.
- GPU temperature/utilization is not reported generically because hardware vendors expose different sensor interfaces. CPU, RAM, disk and uptime are monitored.
- The low-end preset changes selected visual effects only. It cannot guarantee higher FPS and does not replace checking the real performance bottleneck.
- The source was syntax-checked and the filesystem helper functions were tested in this environment. A full PySide6 GUI run and Windows 10/11 integration test still need to be performed on a Windows PC before calling the release production-ready.

## Project layout

- `main.py` - app UI, action library and feature logic.
- `requirements.txt` - runtime dependencies.
- `run_winkit.bat` - source/developer launcher only.
- `build_exe.bat` - local self-contained build (developer machine only).
- `.github/workflows/build-windows.yml` - Windows cloud build that packages the ready-to-use downloads.
- `installer/WinKit.iss` - Inno Setup installer definition.
- `BUILD_WINDOWS.md` - steps to get the installer without Python on the end-user PC.
- `SAFETY.md` - safety model.
- `ROADMAP.md` - useful modules intentionally deferred to later versions.
