; ---------------------------------------------------------------------------
; Installeur du service OCR PDF (Inno Setup 6).
; Compilation : ISCC.exe build\installer.iss  (lancé depuis ocr-service)
;
; Attendus au moment de la compilation :
;   ..\dist\ocr-service\   (sortie PyInstaller : ocr-service.exe + _internal)
;   ..\vendor\             (tesseract\, gs\  -> voir fetch-vendor.ps1)
;   nssm.exe               (dans ce dossier build\)
; ---------------------------------------------------------------------------

#define AppName "Service OCR PDF"
#define AppVersion "1.0.0"
#define AppPublisher "Etude"
#define ServiceName "OcrPdfService"

[Setup]
AppId={{9F3B2C1A-7E4D-4B6A-9C2E-0A1B2C3D4E5F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\OCR PDF Service
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=OCR-PDF-Service-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "..\dist\ocr-service\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\vendor\*"; DestDir: "{app}\vendor"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "nssm.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Journal du service OCR"; Filename: "{commonappdata}\OcrPdfService\ocr-service.log"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"

[Run]
; 1. Génère la configuration par défaut (dossier surveillé choisi par l'utilisateur).
Filename: "{app}\ocr-service.exe"; Parameters: "--init-config ""{code:GetWatchDir}"""; \
    StatusMsg: "Configuration..."; Flags: runhidden waituntilterminated
; 2. Installe et configure le service Windows via NSSM.
Filename: "{app}\nssm.exe"; Parameters: "install {#ServiceName} ""{app}\ocr-service.exe"""; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppDirectory ""{app}"""; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} DisplayName ""{#AppName}"""; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} Description ""Reconnaissance de texte (OCR) automatique sur les PDF."""; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} Start SERVICE_AUTO_START"; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppExit Default Restart"; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppStdout ""{commonappdata}\OcrPdfService\service-out.log"""; \
    Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppStderr ""{commonappdata}\OcrPdfService\service-err.log"""; \
    Flags: runhidden waituntilterminated
; 3. Démarre le service immédiatement.
Filename: "{app}\nssm.exe"; Parameters: "start {#ServiceName}"; \
    Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\nssm.exe"; Parameters: "stop {#ServiceName}"; Flags: runhidden waituntilterminated; RunOnceId: "StopSvc"
Filename: "{app}\nssm.exe"; Parameters: "remove {#ServiceName} confirm"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveSvc"

[Code]
var
  WatchPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  WatchPage := CreateInputDirPage(wpSelectDir,
    'Dossier à surveiller',
    'Quel dossier contient vos fichiers PDF ?',
    'Le service surveillera ce dossier et TOUS ses sous-dossiers. Chaque PDF '
    + 'scanné (image) y sera automatiquement transformé en PDF texte '
    + 'recherchable, l''original étant remplacé.'#13#10#13#10
    + 'Sélectionnez le dossier racine, puis cliquez sur Suivant.',
    False, '');
  WatchPage.Add('');
  WatchPage.Values[0] := ExpandConstant('{userdocs}\PDF');
end;

function GetWatchDir(Param: String): String;
begin
  Result := WatchPage.Values[0];
end;
