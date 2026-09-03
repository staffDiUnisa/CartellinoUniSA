# Eseguibili standalone (senza Python)

Ogni tag `v2.*`/`v3.*` genera automaticamente (GitHub Actions,
[`release.yml`](https://github.com/staffDiUnisa/CartellinoUniSA/blob/master/.github/workflows/release.yml))
eseguibili standalone per macOS, Windows e Linux, allegati alla relativa
[GitHub Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest). Ogni pacchetto
include **due eseguibili**: la TUI (`cartellino-unisa`) e la GUI (`cartellino-unisa-gui`), stessa
distribuzione combinata. Non serve installare Python, `mise` o `uv`.

**Chrome resta comunque una dipendenza esterna obbligatoria** (il download del cartellino usa
Selenium, non imbottigliabile in un eseguibile standalone): va installato separatamente,
qualunque sia il sistema operativo.

## macOS

**Opzione consigliata — installer `.pkg`:**

1. Dalla pagina delle [Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest),
   scarica `cartellino-unisa.pkg`.
2. Doppio click, segui la procedura guidata (installa in `/usr/local/cartellino-unisa`, crea i
   comandi `cartellino-unisa`/`cartellino-unisa-gui` nel `PATH`, e aggiunge due voci ad
   `/Applications`: **Cartellino UniSA** e **Cartellino UniSA (Terminale)**).
3. **Interfaccia grafica** (consigliata per chi non vuole usare il Terminale): apri **Launchpad**
   o **Applicazioni** e fai doppio click su **Cartellino UniSA**.
4. **Interfaccia testuale (TUI)**: doppio click su **Cartellino UniSA (Terminale)** — si apre un
   terminale con la TUI già avviata, a schermo massimizzato, e si chiude da solo all'uscita.

   Al primo avvio viene chiesto quale terminale usare tra quelli installati (**Terminale**
   nativo, **Ghostty**, **iTerm2** — non è supportato Warp, privo di automazione). La scelta si
   cambia in seguito da **Impostazioni → Terminale (solo macOS)**.

   In alternativa, direttamente da Terminale: `cartellino-unisa`.

Il `.pkg` (ed entrambi i launcher) sono **firmati con certificato Developer ID e
notarizzati/staplati da Apple**: Gatekeeper non dovrebbe mostrare alcun avviso, nemmeno offline.

!!! tip "`cartellino-unisa` non trovato (command not found)"
    `/usr/local/bin` è nel `PATH` di default su macOS, ma se il tuo shell profile lo sovrascrive
    esplicitamente potrebbe non esserci. Aggiungi `export PATH="/usr/local/bin:$PATH"` a
    `~/.zshrc` (zsh, default da Catalina in poi) o `~/.bashrc`/`~/.bash_profile` (bash), poi apri
    un nuovo Terminale.

**Opzione alternativa — zip della cartella onedir** (per chi preferisce non installare nulla a
livello di sistema):

```bash
# estrai cartellino-unisa-macos.zip, poi:
cd cartellino-unisa
./cartellino-unisa       # TUI
./cartellino-unisa-gui   # GUI (anche con doppio click dal Finder)
```

Se comparisse "app non verificata"/"sviluppatore non identificato": click destro (o
`Ctrl`+click) → **Apri**, poi conferma (necessario solo la prima volta).

## Windows

**Opzione consigliata — installer `cartellino-unisa-setup.exe`:**

1. Scarica `cartellino-unisa-setup.exe` dalle [Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest).
2. Doppio click, segui la procedura guidata (crea due voci nel Menu Start: **Cartellino UniSA**
   e **Cartellino UniSA (Terminale)**).
3. Avvia **Cartellino UniSA** per la GUI, oppure **Cartellino UniSA (Terminale)** per la TUI.

**Opzione alternativa — zip della cartella onedir:**

```powershell
# estrai cartellino-unisa-windows.zip, poi:
cd cartellino-unisa
.\cartellino-unisa.exe       # TUI
# oppure doppio click su cartellino-unisa-gui.exe per la GUI
```

Il binario **non è firmato** (nessun certificato di firma codice per Windows): al primo avvio
SmartScreen mostra "Windows ha protetto il PC" → **Ulteriori informazioni** → **Esegui comunque**
(necessario solo la prima volta).

## Linux

**Opzione consigliata — pacchetto `.deb`/`.rpm`:**

```bash
# Debian/Ubuntu
sudo dpkg -i cartellino-unisa_<versione>_amd64.deb
# Fedora/RHEL/openSUSE
sudo rpm -i cartellino-unisa-<versione>.x86_64.rpm
```

Poi: `cartellino-unisa` (TUI) o `cartellino-unisa-gui` (GUI) da terminale — nessuna icona/voce
nel menu applicazioni per ora.

**Opzione alternativa — zip della cartella onedir:**

```bash
unzip cartellino-unisa-linux.zip
cd cartellino-unisa
./cartellino-unisa
# se serve: chmod +x cartellino-unisa
```

In entrambi i casi Chrome/Chromium deve essere installato e raggiungibile dal `PATH`. Il
`.deb`/`.rpm` è costruito su Ubuntu (glibc recente): su distro molto datate possono presentarsi
incompatibilità di libreria.

## Note comuni

Perché una cartella (zip) e non un singolo eseguibile: la prima versione usava un eseguibile
"onefile", rotto su macOS (`pyarrow` falliva l'import sul binario scaricato) perché le librerie
native estratte a runtime in una cartella temporanea non firmata vengono bloccate da macOS. La
modalità "onedir" evita questa estrazione runtime — **non spostare l'eseguibile fuori dalla sua
cartella**.

Per rigenerare l'eseguibile localmente:

```bash
uv sync --group build
uv run pyinstaller packaging/cartellino.spec
./dist/cartellino-unisa/cartellino-unisa   # .exe su Windows
```
