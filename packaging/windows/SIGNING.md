# Firma dell'installer Windows

`cartellino-unisa-setup-*.exe` (generato da `packaging/windows/installer.iss` via Inno Setup, nel
job `build (windows-latest, ...)` di `.github/workflows/release.yml`) viene pubblicato **non
firmato** dalla CI. La firma è un passo manuale, eseguito da un maintainer dopo il push del tag,
tramite [`packaging/windows/sign-release.ps1`](sign-release.ps1) da una macchina Windows.

> Firmi da un Mac? `signtool.exe` è Windows-only (non basta avere PowerShell installato) — usa
> invece [`sign-release-macos.sh`](sign-release-macos.sh), documentato in
> [`SIGNING-macos.md`](SIGNING-macos.md), che attende automaticamente il draft della CI e firma
> con `osslsigncode` + PKCS#11.

## Perché la firma non è automatizzata in CI

Il certificato usato è un **certificato OV (Organization Validation) gratuito per progetti
open-source**, emesso da **Certum** tramite **SimplySign** (Certum SimplySign Open Source Code
Signing). A differenza del percorso valutato in precedenza (certificato OV a pagamento,
esportabile come `.pfx` — vedi `ignored/signed_windows.md`, non versionato), questo certificato
**non è esportabile**: la chiave privata vive in un HSM cloud gestito da Certum e ogni sessione di
firma richiede un'autenticazione a due fattori tramite l'app mobile SimplySign.

Questo rende impossibile automatizzare la firma su un runner GitHub-hosted headless: non c'è modo
di soddisfare il prompt 2FA sul telefono del maintainer da un processo CI non presidiato. La firma
resta quindi **human-in-the-loop**: un maintainer con SimplySign Desktop attivo sul proprio
computer scarica l'installer non firmato dal draft della release, lo firma in locale, e ricarica
l'asset firmato prima di pubblicare.

## Setup one-time

1. Installa **SimplySign Desktop** (client Certum che espone il certificato al sistema operativo
   come se fosle uno smart card locale) sulla macchina che userai per firmare.
2. Avvia SimplySign Desktop e fai il primo login: inserisci le credenziali dell'account Certum,
   poi conferma l'OTP inviato tramite l'app mobile SimplySign (va installata sul telefono
   associato all'account). Da questo momento, finché SimplySign Desktop resta loggato, il
   certificato compare nello store `Cert:\CurrentUser\My` come un normale certificato di code
   signing.
3. Recupera il **thumbprint** del certificato, da usare ad ogni firma:

   ```powershell
   Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Format-List Subject, Thumbprint
   ```

   Se compare più di un certificato, identifica quello giusto dal campo `Subject` (nome
   dell'organizzazione/progetto).

## Prerequisiti per ogni sessione di firma

- **`signtool.exe`** nel `PATH` — incluso nel Windows SDK (o disponibile aprendo un "Developer
  Command Prompt for VS").
- **GitHub CLI (`gh`)** autenticato: `gh auth login`, se non già fatto.
- **SimplySign Desktop** avviato e loggato (la sessione OTP scade dopo un certo periodo di
  inattività — se `sign-release.ps1` non trova il certificato nello store, il primo sospetto è
  una sessione SimplySign scaduta: riapri l'app e rifai il login con un nuovo OTP).

## Procedura

1. Attendi che la CI abbia completato la build sul tag pushato e creato il **draft** della
   release su GitHub (job `release` di `release.yml`), con l'installer `.exe` non firmato tra gli
   asset.
2. In PowerShell, imposta il thumbprint del certificato (ottenuto nel setup one-time) e lancia lo
   script indicando il tag:

   ```powershell
   $env:CERT_THUMBPRINT = "<thumbprint>"
   .\packaging\windows\sign-release.ps1 -Tag v3.0.0
   ```

   Lo script verifica i prerequisiti, scarica l'asset `.exe` dal draft, lo firma con `signtool`
   (timestamp RFC3161 via il TSA di Certum), verifica la firma, aggiorna `SHA256SUMS` se presente
   tra gli asset, e ricarica gli asset firmati sulla draft — che resta in draft.
3. Verifica l'output dello script e, se vuoi, controlla a mano gli asset caricati sulla draft
   release su GitHub.
4. Quando sei soddisfatto, rilancia lo script con `-Publish` per pubblicare la release (rimuove lo
   stato draft):

   ```powershell
   .\packaging\windows\sign-release.ps1 -Tag v3.0.0 -Publish
   ```

Se ometti `-Tag`, lo script prova a dedurlo dall'ultimo tag Git locale
(`git describe --tags --abbrev=0`) — utile se stai firmando la release appena taggata, ma va
comunque verificato che corrisponda al tag giusto prima di procedere.

## Nota su `CERT_THUMBPRINT`

Il thumbprint di un certificato **non è un segreto**: è un hash pubblico legato al certificato,
non alla chiave privata (che resta nell'HSM di Certum, mai esposta). Non c'è quindi un rischio di
sicurezza a scriverlo in chiaro. Va comunque tenuto **fuori dai file versionati** — non per
segretezza, ma per evitare confusione: se in futuro il certificato viene rinnovato o sostituito,
un thumbprint committato nel repo resterebbe silenziosamente stantio finché qualcuno non si accorge
che le firme falliscono. Impostalo come variabile d'ambiente (`$env:CERT_THUMBPRINT`) o passalo
esplicitamente con `-CertThumbprint` ad ogni sessione di firma.
