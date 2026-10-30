# WinKit safety model

- Registry presets modify current-user (`HKCU`) visual preferences only.
- Before the first WinKit change in a registry group, original values are saved under `%APPDATA%\\WinKit\\registry_backups.json`.
- Restore actions only restore values captured by WinKit. No machine-wide registry paths are changed.
- Temporary cleanup is limited to the current user's TEMP directory, skips symbolic links and reparse points throughout the tree, and skips locked/inaccessible items.
- Recycle Bin emptying is classified as high impact and always requires confirmation.
- Network stack resets, administrator commands and other potentially disruptive actions require confirmation or the normal Windows UAC prompt.
- WinKit does not disable Microsoft Defender, Windows Firewall, Windows Update, UAC, or security services.
- Software updates are previewed using WinGet first. Updating eligible packages requires a separate confirmation and runs in a visible console.
- Importing a WinGet package list previews package identifiers and requires explicit confirmation.
- Disk Analyzer only reads files and never deletes them. It skips links/reparse points and caps scans at 50,000 files.
- System reports are generated locally. Review them before sharing because they can include device and network-adapter information.
