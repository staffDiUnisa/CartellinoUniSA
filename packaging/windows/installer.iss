; Script Inno Setup per l'installer Windows di Cartellino UniSA.
;
; Usa la stessa cartella onedir già prodotta da PyInstaller
; (packaging/cartellino.spec, dist/cartellino-unisa/) come payload: nessuna
; ricompilazione, solo confezionamento in un setup.exe con procedura guidata.
;
; Uso: ISCC.exe packaging\windows\installer.iss /DMyAppVersion=2.0.0
; (versione passata da riga di comando dal workflow CI, estratta dal tag git)
;
; Installer NON firmato: vedi ignored/signed_windows.md (non versionato) per le
; opzioni valutate per aggiungere la firma in futuro.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{5C7B6E2A-4F3D-4B8C-9A1E-8F2C6D4A7B10}
AppName=Cartellino UniSA
AppVersion={#MyAppVersion}
AppPublisher=Staff di UniSA
DefaultDirName={autopf}\CartellinoUniSA
DefaultGroupName=Cartellino UniSA
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=cartellino-unisa-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
; Nessuna firma: vedi ignored/signed_windows.md

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\cartellino-unisa\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Crea un'icona sul Desktop"; Flags: unchecked

[Icons]
Name: "{group}\Cartellino UniSA"; Filename: "{app}\cartellino-unisa.exe"
Name: "{group}\Disinstalla Cartellino UniSA"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Cartellino UniSA"; Filename: "{app}\cartellino-unisa.exe"; Tasks: desktopicon
