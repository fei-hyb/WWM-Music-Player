; Inno Setup script for Game Music Player
; Build with: ISCC.exe packaging\game_music_player.iss

#define MyAppName "Game Music Player"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Game Music Tools"
#define MyAppExeName "GameMusicPlayer.exe"
#define MyAppDistDir "..\\dist"
#define MyAppExePath MyAppDistDir + "\\" + MyAppExeName

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\output
OutputBaseFilename=GameMusicPlayer_Installer
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableReadyPage=no
DisableFinishedPage=no
; Uncomment if you add an .ico file later
;SetupIconFile="{#MyAppDistDir}\\GameMusicPlayer.ico"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#MyAppExePath}"; DestDir: "{app}"; Flags: ignoreversion
; Add bundled docs for offline reference
Source: "..\\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\MIDI_FIX_COMPLETE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\PDF_READER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:";

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

