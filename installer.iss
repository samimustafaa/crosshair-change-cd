#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId=sg0hann-Crosshair-Color-Lab
AppName=sg0hann Crosshair Color Lab
AppVersion={#MyAppVersion}
AppPublisher=sg0hann
AppPublisherURL=https://github.com/samimustafaa/crosshair-change-cd
DefaultDirName={localappdata}\Programs\sg0hann Crosshair Color Lab
DefaultGroupName=sg0hann Crosshair Color Lab
UninstallDisplayIcon={app}\sg0hann-Crosshair.exe
OutputDir=dist
OutputBaseFilename=sg0hann-Crosshair-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
WizardStyle=modern
DisableWelcomePage=no
CloseApplications=yes
CloseApplicationsFilter=sg0hann-Crosshair.exe
RestartApplications=no
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\sg0hann-Crosshair.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\sg0hann Crosshair Color Lab"; Filename: "{app}\sg0hann-Crosshair.exe"
Name: "{autodesktop}\sg0hann Crosshair Color Lab"; Filename: "{app}\sg0hann-Crosshair.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\sg0hann-Crosshair.exe"; Description: "Launch sg0hann Crosshair Color Lab"; Flags: nowait
