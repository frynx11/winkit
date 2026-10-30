#define MyAppName "WinKit"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "WinKit"
#define MyAppExeName "WinKit.exe"

[Setup]
AppId={{A9D83C4E-15E2-4A90-9D3A-2B9BA813A820}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\WinKit
DefaultGroupName=WinKit
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=WinKit_Setup_2.0.0
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=2.0.0.0
VersionInfoProductName=WinKit
VersionInfoCompany=WinKit

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\WinKit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WinKit"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\WinKit"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch WinKit"; Flags: postinstall nowait skipifsilent
