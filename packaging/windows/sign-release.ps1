<#
.SYNOPSIS
    Firma manualmente l'installer Windows (.exe) di una GitHub Release in draft
    usando il certificato Certum SimplySign Open Source Code Signing, e
    opzionalmente pubblica la release.

.DESCRIPTION
    Human-in-the-loop signing: la pipeline CI produce gia' un draft di release
    con l'installer NON firmato (packaging\windows\installer.iss via Inno Setup).
    Questo script:
      1. Verifica i prerequisiti (signtool, gh CLI autenticato, certificato
         SimplySign disponibile nello store e non scaduto).
      2. Scarica l'asset .exe non firmato dal draft della release indicata.
      3. Firma il file con signtool + timestamp RFC3161 (Certum TSA).
      4. Verifica la firma.
      5. Ricalcola/aggiorna SHA256SUMS se presente tra gli asset della release.
      6. Ricarica gli asset firmati nella draft (sovrascrivendo quelli non firmati).
      7. Se -Publish e' specificato, pubblica la release (draft=false).

.PARAMETER Tag
    Tag della release da firmare (es. v3.0.0). Se omesso, usa l'ultimo tag
    locale (git describe --tags --abbrev=0).

.PARAMETER CertThumbprint
    Thumbprint SHA1 (40 caratteri esadecimali) del certificato Code Signing
    nello store Cert:\CurrentUser\My. Se omesso, legge $env:CERT_THUMBPRINT.

.PARAMETER Publish
    Se specificato, pubblica la release (rimuove lo stato draft) dopo la
    firma e la verifica. Se omesso, lascia la release come draft per
    permettere un controllo manuale finale prima della pubblicazione.

.EXAMPLE
    $env:CERT_THUMBPRINT = "8F4C4829B74A64E26CFCBADCF0AF77B20267DA3E"
    .\packaging\windows\sign-release.ps1 -Tag v3.0.0

.EXAMPLE
    .\packaging\windows\sign-release.ps1 -Tag v3.0.0 -CertThumbprint 8F4C... -Publish
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Tag,

    [Parameter(Mandatory = $false)]
    [string]$CertThumbprint = $env:CERT_THUMBPRINT,

    [Parameter(Mandatory = $false)]
    [switch]$Publish
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Host "ERRORE: $Message" -ForegroundColor Red
    exit 1
}

function Step($Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

# --- 1. Prerequisiti ---------------------------------------------------------

Step "Verifica prerequisiti"

if (-not (Get-Command signtool.exe -ErrorAction SilentlyContinue)) {
    Fail "signtool.exe non trovato nel PATH. Installa Windows SDK o esegui da un 'Developer Command Prompt for VS'."
}

if (-not (Get-Command gh.exe -ErrorAction SilentlyContinue)) {
    Fail "GitHub CLI (gh) non trovato nel PATH. Installa da https://cli.github.com/"
}

$ghAuthStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Fail "GitHub CLI non autenticato. Esegui 'gh auth login' prima di continuare.`n$ghAuthStatus"
}

if ([string]::IsNullOrWhiteSpace($CertThumbprint)) {
    Fail "CERT_THUMBPRINT non specificato. Passa -CertThumbprint oppure imposta `$env:CERT_THUMBPRINT."
}

$CertThumbprint = $CertThumbprint.Trim().ToUpper() -replace '\s', ''

$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object { $_.Thumbprint -eq $CertThumbprint }

if (-not $cert) {
    Fail "Nessun certificato di code signing con thumbprint $CertThumbprint trovato in Cert:\CurrentUser\My. Verifica che SimplySign Desktop sia aperto e loggato (la sessione OTP potrebbe essere scaduta)."
}

if ($cert.NotAfter -lt (Get-Date)) {
    Fail "Il certificato $CertThumbprint e' scaduto il $($cert.NotAfter)."
}

Write-Host "Certificato trovato: $($cert.Subject) (valido fino al $($cert.NotAfter))" -ForegroundColor Green

# --- 2. Determina il tag ------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($Tag)) {
    Step "Nessun tag specificato, rilevo l'ultimo tag locale"
    $Tag = git describe --tags --abbrev=0
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Tag)) {
        Fail "Impossibile determinare automaticamente il tag. Specifica -Tag esplicitamente."
    }
    Write-Host "Tag rilevato: $Tag" -ForegroundColor Green
}

# --- 3. Scarica l'asset non firmato -------------------------------------------

Step "Scarico l'asset .exe della release $Tag dal draft"

$workDir = Join-Path $env:TEMP "cartellino-sign-$Tag"
if (Test-Path $workDir) { Remove-Item $workDir -Recurse -Force }
New-Item -ItemType Directory -Path $workDir | Out-Null

gh release download $Tag --dir $workDir --pattern "cartellino-unisa-setup-*.exe"
if ($LASTEXITCODE -ne 0) {
    Fail "Download dell'asset .exe fallito. Verifica che il tag $Tag esista e che la release sia in draft con l'asset presente."
}

$exeFile = Get-ChildItem $workDir -Filter "cartellino-unisa-setup-*.exe" | Select-Object -First 1
if (-not $exeFile) {
    Fail "Nessun file cartellino-unisa-setup-*.exe trovato tra gli asset scaricati."
}

Write-Host "Asset scaricato: $($exeFile.Name)" -ForegroundColor Green

# --- 4. Firma con signtool ----------------------------------------------------

Step "Firmo $($exeFile.Name) con signtool"

& signtool.exe sign `
    /sha1 $CertThumbprint `
    /fd sha256 `
    /tr http://time.certum.pl/ `
    /td sha256 `
    /d "Cartellino UniSA" `
    /du "https://github.com/staffDiUnisa/CartellinoUniSA" `
    $exeFile.FullName

if ($LASTEXITCODE -ne 0) {
    Fail "signtool sign ha restituito un errore (exit code $LASTEXITCODE)."
}

# --- 5. Verifica la firma ------------------------------------------------------

Step "Verifico la firma"

& signtool.exe verify /pa /v $exeFile.FullName
if ($LASTEXITCODE -ne 0) {
    Fail "signtool verify ha fallito: la firma non risulta valida."
}

Write-Host "Firma verificata con successo." -ForegroundColor Green

# --- 6. Aggiorna SHA256SUMS se presente tra gli asset --------------------------

Step "Controllo SHA256SUMS tra gli asset della release"

$sumsFile = Join-Path $workDir "SHA256SUMS"
gh release download $Tag --dir $workDir --pattern "SHA256SUMS" 2>$null

if (Test-Path $sumsFile) {
    $newHash = (Get-FileHash $exeFile.FullName -Algorithm SHA256).Hash.ToLower()
    $lines = Get-Content $sumsFile
    $updated = $lines | ForEach-Object {
        if ($_ -match [regex]::Escape($exeFile.Name)) {
            "$newHash  $($exeFile.Name)"
        } else {
            $_
        }
    }
    Set-Content -Path $sumsFile -Value $updated -Encoding UTF8
    Write-Host "SHA256SUMS aggiornato con il nuovo hash del file firmato." -ForegroundColor Green
} else {
    Write-Host "Nessun file SHA256SUMS trovato tra gli asset, salto questo step." -ForegroundColor Yellow
}

# --- 7. Ricarica gli asset firmati nella draft ----------------------------------

Step "Carico gli asset firmati sulla draft release $Tag"

gh release upload $Tag $exeFile.FullName --clobber
if ($LASTEXITCODE -ne 0) {
    Fail "Upload dell'exe firmato fallito."
}

if (Test-Path $sumsFile) {
    gh release upload $Tag $sumsFile --clobber
    if ($LASTEXITCODE -ne 0) {
        Fail "Upload di SHA256SUMS aggiornato fallito."
    }
}

Write-Host "Asset firmati caricati sulla draft release $Tag." -ForegroundColor Green

# --- 8. Pubblica se richiesto ----------------------------------------------------

if ($Publish) {
    Step "Pubblico la release $Tag (rimuovo lo stato draft)"
    gh release edit $Tag --draft=false
    if ($LASTEXITCODE -ne 0) {
        Fail "Pubblicazione della release fallita."
    }
    Write-Host "Release $Tag pubblicata." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "La release $Tag resta in DRAFT. Verifica manualmente gli asset firmati, poi rilancia con -Publish per pubblicare." -ForegroundColor Yellow
}

Remove-Item $workDir -Recurse -Force -ErrorAction SilentlyContinue
