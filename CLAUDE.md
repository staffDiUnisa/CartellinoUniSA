# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python CLI tool that downloads and processes UniSA employee attendance data (cartellino presenze) from `https://presenze.unisa.it`. It calculates overtime hours, compensatory rest days, monthly hour credits, and generates per-project timesheets.

## Setup

Il progetto usa `mise` (pin versione Python + tool `uv`) e `uv` (gestione dipendenze/venv)
al posto di `pip`/`venv`. Dipendenze dichiarate in `pyproject.toml`, risolte in `uv.lock`.

```bash
mise install   # installa Python 3.12 e uv secondo .mise.toml
mise run install   # equivalente a: uv sync
```

Per eseguire lo script principale (CLI non interattiva, Fase 5 TODO v2.0.0):

```bash
mise run app        # equivalente a: uv run python cartellino_v2.py
# oppure direttamente:
uv run python cartellino_v2.py
```

Flag non interattivi (`cartellino_v2.py`, nessun prompt se specificati): `--aggiorna-cartellino`/
`--no-aggiorna-cartellino`, `--auth-method {unisa,spid,cie}` (passato a
`get.ottieni_cartellino(metodo=...)`, bypassa `scegli_metodo_autenticazione()`),
`--export-format {xlsx,csv}` (sovrascrive `Config.export_format` per questa sola esecuzione,
senza toccare `config.toml`), `--solo-report` (comma-separated tra
`cartellino/processor.py::REPORT_KEYS` = `cartellino,riposo,credito,statistiche,ore-giornaliere`;
omesso = tutti, comportamento storico invariato), `--timesheet-progetto`.
`CartellinoProcessor.run(reports=...)` genera solo i report richiesti (`None` = tutti) e passa
`cfg.export_format` ai quattro configurabili (riposo compensativo, credito ore, statistiche, ore
giornaliere) tramite `cartellino/export_utils.py::save_sheets` — condiviso con la TUI
(`ReportsScreen`, che invoca un report alla volta allo stesso modo), insieme a
`cartellino/timesheet_runner.py` per `--timesheet-progetto`. Chiude il punto lasciato aperto in
Fase 3 TODO.md (scrittura report "on demand" anche lato CLI, non solo TUI).

Per la TUI (Fase 4 TODO v2.0.0, entrypoint consigliato, vedi sezione dedicata sotto):

```bash
mise run tui         # equivalente a: uv run python cartellino_tui.py
```

### Credenziali e configurazione (`cartellino_v2.py` / pacchetto `cartellino/`)

A partire dalla Fase 2 del TODO (v2.0.0), il percorso `cartellino_v2.py` legge la configurazione
da `config.toml` (cartella utente standard via `platformdirs`, `Config.load()` /
`cartellino/user_config.py`) e le credenziali UniSA dal **keyring nativo del SO** (libreria
`keyring`, service name `"cartellino-unisa"`, vedi `cartellino/credentials.py`), non più da `.env`.

Alla prima esecuzione, se non esiste ancora `config.toml` ma è presente un `.env` legacy con le
variabili sotto, viene eseguita una **migrazione automatica one-shot**
(`cartellino/user_config.py::migrate_from_env_if_needed`): `config.toml` viene creato e le
credenziali salvate nel keyring; il messaggio a schermo consiglia poi di eliminare `.env`.

Variabili `.env` legacy (usate solo per la migrazione, o come fallback puro se non è disponibile
né `config.toml` né un backend keyring):
- `USERNAME` / `PASSWORD` — UniSA credentials
- `CURRENT_YEAR` — year to process (e.g. `2025`)
- `MIN_DATE_RIPOSI_USATI` — cutoff date in `MM-DD` format for counting used compensatory rests
- `HEADLESS` — `True` per Chrome headless (solo login Credenziali UNISA)

Il vecchio percorso `main.py` / `process.py` (legacy, vedi sotto) continua a leggere `CURRENT_YEAR`
e `MIN_DATE_RIPOSI_USATI` direttamente da `.env`/env vars: non è stato migrato a `config.toml`,
perché fuori dallo scope della roadmap v2.0.0 (che riguarda solo `cartellino_v2.py` e il pacchetto
`cartellino/`).

## Running

```bash
uv run python main.py           # prompts whether to download fresh data
uv run python main.py --no-aggiorna-cartellino  # skip download, process existing data
```

Download requires UniSA network access and Chrome Beta at `/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta`. Set `HEADLESS=True` in `.env` for headless mode.

### `cartellino_tui.py` — TUI Textual (Fase 4 TODO v2.0.0, entrypoint consigliato)

```bash
mise run tui
# oppure
uv run python cartellino_tui.py
```

App Textual (pacchetto `cartellino/tui/`) con dashboard, onboarding, aggiornamento
(con scelta metodo auth e log in tempo reale), impostazioni, report on-demand e
timesheet di progetto. Stessa struttura dati di `cartellino_v2.py` (`data/v2/{anno}/`), ma con
root diversa: `cartellino_tui.py` definisce `APP_DATA_DIR`/`DATA_FOLDER`/`LOG_FILE` fissi nella
home dell'utente (`~/.cartellino_unisa/`, `%LOCALAPPDATA%\cartellino_unisa\` su Windows,
`_app_data_dir()`) invece che relativi alla cwd — necessario per l'eseguibile standalone
(Fase 6), lanciabile da qualunque cartella. Vedi il pacchetto `cartellino/tui/` sotto per i
dettagli.

### `cartellino_gui.py` — GUI desktop PySide6 (TODO_gui.md, v3.0.0)

```bash
mise run gui
# oppure
uv run python cartellino_gui.py
```

App PySide6 (pacchetto `cartellino/gui/`), affianca la TUI senza sostituirla — stessa scelta di
"distribuzione combinata" descritta in `TODO_gui.md`: un solo pacchetto/installer per OS include
entrambi gli eseguibili. Stessa struttura dati/cartella fissa della TUI (`APP_DATA_DIR` in
`cartellino_gui.py`, `~/.cartellino_unisa/` su macOS/Linux, `%LOCALAPPDATA%\cartellino_unisa\` su
Windows — **condivisa** con `cartellino_tui.py`, non separata: GUI e TUI sono due frontend sullo
stesso `config.toml`/dati, non due prodotti indipendenti). Vedi il pacchetto `cartellino/gui/`
sotto per i dettagli.

### Packaging (Fase 6 TODO v2.0.0)

`packaging/cartellino.spec` — spec PyInstaller (**onedir**, non onefile — vedi sotto) per
`cartellino_tui.py`:

```bash
uv sync --group build   # installa pyinstaller (dependency-group "build", non nelle
                         # dipendenze runtime: pyinstaller serve solo per impacchettare)
uv run pyinstaller packaging/cartellino.spec --noconfirm
./dist/cartellino-unisa/cartellino-unisa  # .exe su Windows; NON spostare l'eseguibile
                                            # fuori dalla cartella (librerie accanto)
```

- **Onedir, non onefile**: la prima versione dello spec produceva un eseguibile onefile
  (`EXE(pyz, a.scripts, a.binaries, a.datas, ...)`), rotto su macOS — `pyarrow` (usato da
  `pd.read_feather`) falliva l'import sul binario scaricato dalla Release
  (`ImportError: Import pyarrow failed`), pur funzionando su una build fatta ed eseguita in
  locale. Causa: in onefile le librerie native vengono estratte in una cartella temporanea *a
  runtime*, non firmate — macOS (specie Apple Silicon) può bloccarle, in particolare per un
  binario scaricato da browser (quarantena). Lo spec ora usa `EXE(..., exclude_binaries=True)` +
  `COLLECT(...)`: le librerie stanno accanto all'eseguibile fin dalla build, niente estrazione
  runtime. Il workflow comprime la cartella in uno zip per l'asset della Release
  (`.github/workflows/release.yml`).
- `keyring` e `pyarrow` hanno già hook PyInstaller propri (rispettivamente in `PyInstaller.hooks`
  e `_pyinstaller_hooks_contrib`) che raccolgono automaticamente submodule/metadata/data file —
  nessun `hiddenimports` manuale necessario per questi due. Il hook di `selenium` raccoglie solo
  i data file, non i submodule dei browser: `selenium/webdriver/__init__.py` espone
  `webdriver.Chrome` con `__getattr__` a livello di modulo (PEP 562, lazy import), invisibile
  all'analisi statica di PyInstaller (riscontrato in produzione:
  `ModuleNotFoundError: No module named 'selenium.webdriver.chrome.webdriver'` all'avvio del
  download) — vanno dichiarati esplicitamente in `hiddenimports` nello spec
  (`selenium.webdriver.chrome.{webdriver,options,service}`).
- `cartellino/tui/app.py::CartellinoApp._BASE_PATH`/`_bundle_base()`: Textual risolve `CSS_PATH`
  con `inspect.getfile(CartellinoApp)`, che una volta "frozen" non punta a un file reale su disco
  (il modulo vive nell'archivio PYZ, non estratto). `_BASE_PATH` viene quindi impostato in base a
  `sys._MEIPASS` quando l'app è frozen; lo stesso vale per la lettura di `pyproject.toml` in
  `_app_version()`. Il file `cartellino/tui/app.tcss` e `pyproject.toml` sono dichiarati come
  `datas` nello spec, con gli stessi percorsi relativi attesi da `_bundle_base()`.
- `.github/workflows/release.yml`: build matrix macOS/Windows/Linux su push di un tag `v2.*`,
  ogni job di build carica la cartella onedir grezza come artifact; il job `release`
  (ubuntu-latest, unico posto dove serve `zip`: assente in Git Bash su `windows-latest`) le
  scarica e comprime ciascuna in `<asset>.zip`, poi allega gli zip come **draft** alla GitHub
  Release (pubblicazione manuale dopo revisione).
- **`CHANGELOG.md`**: sezioni `## vX.Y.Z` (senza suffisso `-rcN`) con le novità principali di
  ogni release definitiva, in italiano. Il job `release` estrae con `awk` la sezione il cui
  titolo corrisponde esattamente al tag pushato (`## ${GITHUB_REF_NAME}`) e la passa come
  `body_path` a `softprops/action-gh-release` (insieme a `generate_release_notes: true`, che
  aggiunge comunque il changelog automatico di GitHub sotto). Nessun `if` esplicito limita
  l'estrazione alle sole release definitive: un tag `-rcN` non ha mai una sezione corrispondente
  in `CHANGELOG.md` (per costruzione — non se ne scrivono per le rc), quindi l'estrazione produce
  un file vuoto e la release non ha descrizione extra, comportamento identico a prima
  dell'introduzione di questo meccanismo. Va aggiunta la sezione della prossima versione **prima**
  di taggare una release definitiva, altrimenti va persa la descrizione delle novità (solo il
  changelog auto-generato) — uno step logga un `::warning::` in quel caso, ma non fa fallire la
  build.
- Chrome resta dipendenza esterna obbligatoria (Selenium non è imbottigliabile).
- **`cartellino_tui.py` importa `pyarrow` esplicitamente all'avvio, sul thread principale, e
  ripulisce `DYLD_LIBRARY_PATH`/`DYLD_FALLBACK_LIBRARY_PATH` (macOS) tramite re-exec del
  processo prima di qualunque altro import.** Due problemi distinti riscontrati in produzione
  sul binario firmato/notarizzato, entrambi con lo stesso sintomo ("Import pyarrow failed"):
  1. L'import lazy di `pyarrow` fatto da `pandas` solo alla prima chiamata reale a
     `to_feather()`/`read_feather()` avveniva dentro il worker thread del download
     (`UpdateScreen._scarica`, `@work(thread=True)`), rendendo il vero errore difficile da
     diagnosticare (visibile solo come messaggio breve nel log). Importarlo eagerly
     all'avvio, sul thread principale, rende qualunque problema di import immediato e con
     traceback completo invece che nascosto dentro un worker thread.
  2. **Causa reale, trovata grazie al punto precedente**: su un Mac con `apache-arrow`
     installato via Homebrew, `DYLD_LIBRARY_PATH`/`DYLD_FALLBACK_LIBRARY_PATH` (esportate da
     Homebrew nella shell) puntano a `/opt/homebrew/lib`, facendo sì che `dyld` carichi
     `libarrow.dylib` di sistema (stesso nome/versione nominale, ma compilata con una versione
     diversa di Abseil) al posto di quella bundled — `ImportError: ... Symbol not found:
     __ZN4absl...`. Riprodotto e confermato in locale impostando le stesse variabili.
     `os.environ.pop(...)` da solo **non basta**: dyld fissa queste variabili all'avvio del
     processo, una modifica di `os.environ` fatta da Python dopo non ha effetto retroattivo
     (stesso errore identico anche col pop). Serve un **re-exec** (`os.execve`) con ambiente
     ripulito, che riavvia il processo da zero senza quelle variabili fin dall'inizio —
     verificato che risolve il problema con lo stesso identico ambiente che prima crashava.
- **Firma e notarizzazione macOS** (job `build (macos-latest, ...)`, richiede i secrets
  `MACOS_CERTIFICATE`/`MACOS_CERTIFICATE_PWD`/`APPLE_ID`/`APPLE_ID_PASSWORD`/`APPLE_TEAM_ID` —
  procedura per generarli/ottenerli in `ignored/signed_macos.md`, non versionato):
  1. Importa il certificato Developer ID `.p12` in un keychain temporaneo creato ad-hoc
  2. Firma **ogni** Mach-O reale nella cartella onedir (rilevato con `file`, non per estensione
     `.so`/`.dylib`: alcuni pacchetti — es. `selenium-manager` di `selenium` — includono binari
     nativi senza estensione, causa di un primo rifiuto di notarizzazione), poi l'eseguibile, con
     `packaging/entitlements.plist` (hardened runtime + `disable-library-validation`, necessario
     perché le dylib vendored di pyarrow/numpy potrebbero non condividere la stessa identity)
  3. `xcrun notarytool submit --wait --output-format json` su uno zip temporaneo (creato con
     `ditto`, non `zip`, per preservare i metadati di firma); lo step controlla esplicitamente lo
     `status` nel JSON e fa fallire la build se non è `Accepted` — `--wait` da solo esce con
     codice 0 anche se Apple rifiuta la richiesta, quindi un semplice check dell'exit code
     lascerebbe passare come "verde" un binario NON notarizzato (successo così in un run di
     prova). In caso di rifiuto stampa anche `xcrun notarytool log` per il motivo esatto.
  4. **Niente stapling sull'eseguibile grezzo**: `xcrun stapler staple` non supporta un eseguibile
     "sciolto" (non un `.app`/`.pkg`/`.dmg` — risposta verificata: "Stapler is incapable of working
     with Document files"), quindi il passo è stato rimosso invece di lasciarlo fallire ad ogni
     run per l'eseguibile onedir grezzo. La notarizzazione resta comunque valida senza stapling:
     Gatekeeper fa una verifica online al primo avvio invece che offline (verificato: un binario
     con attributo di quarantena reale si avvia senza blocchi). Il `.pkg` sotto, invece, viene
     staplato: è un formato supportato.
  Windows resta non firmato (nessun certificato acquistato): SmartScreen mostra comunque
  l'avviso, documentato in README.md.
- **Installer nativi per OS** (job `build`, oltre agli zip onedir storici — vedi README.md §
  "Eseguibili standalone" per le istruzioni utente finale):
  - **macOS `.pkg`**: `pkgbuild --root pkgroot --install-location / --scripts packaging/macos ...`
    (root sintetizzato in CI, vedi launcher `.app` sotto — prima della v2.0.2 era
    `--root dist/cartellino-unisa --install-location /usr/local/cartellino-unisa`), firmato
    con un **secondo certificato**, "Developer ID Installer" (distinto da "Developer ID
    Application" usato per l'eseguibile — stessa Apple Developer membership, procedura per
    generarlo al punto 5 di `ignored/signed_macos.md`; secrets `MACOS_INSTALLER_CERTIFICATE`/
    `MACOS_INSTALLER_CERTIFICATE_PWD`, **già configurati sul repo** e importati nello stesso
    keychain temporaneo del certificato Application). Notarizzato separatamente e **staplato**
    (a differenza dell'eseguibile sciolto, il `.pkg` è un formato supportato dallo stapler).
    `packaging/macos/postinstall` crea un symlink `/usr/local/bin/cartellino-unisa` verso
    l'installazione in `/usr/local/cartellino-unisa`. Verificato con una build reale (tag di
    prova `v2.0.1-rc1`, poi eliminato) e pubblicato in `v2.0.1`.
    - **Launcher `.app` per macOS** (incluso dentro lo stesso `.pkg`, non un artifact separato —
      un solo download per l'utente finale): `packaging/macos/launcher.applescript`, sorgente
      AppleScript versionato (non un `.app` compilato committato — binario, diff illeggibili,
      specifico della versione Xcode/OS del runner), compilato in CI con
      `osacompile -o "Cartellino UniSA.app" packaging/macos/launcher.applescript`. Preferito a
      uno script di shell scritto a mano come `Contents/MacOS/<eseguibile>`: `osacompile` produce
      un vero Mach-O (`Contents/MacOS/applet`), firmabile/notarizzabile con la **stessa identity**
      Developer ID Application della CLI, ma con un **entitlements dedicato**
      (`packaging/macos/launcher-entitlements.plist`, non `packaging/entitlements.plist`):
      sotto hardened runtime, inviare un Apple Event (`tell application "Terminal"`) richiede
      l'entitlement `com.apple.security.automation.apple-events`, altrimenti fallisce con
      `Not authorised to send Apple events to Terminal. (-1743)` anche dopo che l'utente ha
      concesso il permesso nel prompt di Automazione — riscontrato in produzione sulla
      v2.0.2-rc1, il flag va dichiarato a livello di firma, il prompt di sistema da solo non
      basta. L'AppleScript apre Terminale e lancia il **percorso assoluto**
      `/usr/local/cartellino-unisa/cartellino-unisa`, non il comando `cartellino-unisa` dal
      `PATH`: un Terminale aperto da Finder subito dopo l'installazione potrebbe non avere ancora
      un `PATH` aggiornato (stesso problema di profili shell che sovrascrivono `PATH` documentato
      in README.md per l'uso manuale). L'Info.plist di default di `osacompile` (identifier
      generico `com.apple.ScriptEditor.id.*`, nessuna versione) viene patchato con
      `/usr/libexec/PlistBuddy` (`CFBundleIdentifier` → `org.antaresnet.cartellino-unisa.launcher`,
      nome/versione) **prima** della firma — pkgbuild non firma il payload, solo l'installer
      package.
      - **Notarizzazione e stapling separati per l'app**: a differenza dell'eseguibile CLI sciolto
        (nessuno stapling, verifica online al primo avvio), l'app viene notarizzata (stesso
        pattern `ditto` + `notarytool submit --wait` con controllo esplicito dello status) **e**
        staplata (`xcrun stapler staple`, formato `.app` supportato): un'app avviata con doppio
        click da Finder non ha un contesto terminale che mostrerebbe un eventuale errore di
        verifica online, va quindi resa verificabile offline fin dal primo lancio.
      - **Un solo `.pkg` per CLI + app**: `pkgbuild` accetta una sola coppia
        `--root`/`--install-location`, quindi CLI e app vengono staged in un unico root
        sintetizzato in CI (`pkgroot/usr/local/cartellino-unisa/*` +
        `pkgroot/Applications/Cartellino UniSA.app`) con `pkgbuild --root pkgroot
        --install-location / ...`. Scartata l'alternativa con due pacchetti componente +
        `productbuild --package ... --package ...` (Distribution XML): CLI e app si
        installano/aggiornano sempre insieme, nessuno scenario di installazione indipendente
        giustifica la complessità aggiuntiva di due identifier/receipt separati.
        `packaging/macos/postinstall` non ha richiesto modifiche: usa già percorsi assoluti
        indipendenti da `--install-location`.
      - **Bug reale in produzione (v3.0.1, issue GitHub #6): GUI "non risponde" per minuti
        all'avvio da Finder/Launchpad**. Fino a v3.0.1 il launcher `Cartellino UniSA.app` era solo
        un'icona: il suo eseguibile era uno script di shell che faceva `exec` del binario
        installato in `/usr/local/cartellino-unisa/cartellino-unisa-gui`. `exec` sostituisce
        l'immagine del processo ma **non** la sua identità di bundle macOS — il processo
        risultante ha come percorso un binario "sciolto" fuori da qualunque `Contents/MacOS/`,
        quindi `CFBundleGetMainBundle()` non trova alcun `Info.plist`. Diagnosticato riproducendo
        l'hang in locale (`sample`/`log show` sul processo bloccato): senza un'identità di bundle
        valida, CoreFoundation non può usare la cache delle preferenze per-bundle, e ogni lookup
        di localizzazione fatto da PySide6/Shiboken durante l'inizializzazione lazy dei tipi Qt
        (`QLocale` e affini, migliaia di volte durante l'avvio) degrada a una query NON
        cache-ata via XPC a `cfprefsd` (~100ms l'una, migliaia di eventi "Retrieve User by ID"
        osservati nei log di sistema durante l'hang, contro **zero** nello stesso identico onedir
        lanciato da dentro un vero bundle `.app`) — non un deadlock, ma un loop di lookup non
        cacheati che si accumula a minuti. **Fix**: l'eseguibile PyInstaller reale (già firmato) e
        le sue librerie di supporto (`_internal`) vengono copiati direttamente dentro
        `Contents/MacOS` e `Contents/Frameworks` del bundle `Cartellino UniSA.app` (niente più
        script/`exec` verso un percorso esterno), nello step "Genera e firma il launcher GUI .app"
        di `release.yml` — verificato con una build locale non firmata: lo stesso identico onedir
        si avvia in ~1s da dentro questa struttura invece di restare bloccato per minuti. La
        firma del bundle va fatta con le stesse `packaging/entitlements.plist`
        dell'eseguibile grezzo (hardened runtime + `disable-library-validation`): il main
        executable del bundle ora è quel binario, e una firma "pulita" del bundle senza
        entitlements le sovrascriverebbe con nessuna, reintroducendo il problema di library
        validation per le dylib vendored di pyarrow/numpy/PySide6 già risolto altrove per
        l'eseguibile sciolto. Il symlink `/usr/local/bin/cartellino-unisa-gui`
        (`packaging/macos/postinstall`) punta ora alla copia **dentro** il bundle
        (`/Applications/Cartellino UniSA.app/Contents/MacOS/cartellino-unisa-gui`), non più
        all'eseguibile sciolto in `/usr/local/cartellino-unisa/`: quest'ultimo resta comunque
        privo di identità di bundle valida e andrebbe incontro allo stesso hang se lanciato
        direttamente. `packaging/macos/gui_launcher/Contents/MacOS/` nel repo contiene solo un
        `.gitkeep` (git non traccia le cartelle vuote): l'eseguibile reale viene copiato lì da CI
        ad ogni build, non è mai committato (stesso principio delle icone generate).
      - **Icona personalizzata** (v2.0.3): `resources/logo.png` (512x512, non versionato prima
        d'ora) è la sorgente unica per le icone generate in CI, mai committata già convertita
        (formati binari `.ico`/`.icns`, diff illeggibili — stesso principio già seguito per
        l'AppleScript sorgente del launcher). `packaging/generate_icons.py`
        (`uv run python packaging/generate_icons.py`, dipende da `pillow`, aggiunto al
        dependency-group `build`) genera `packaging/build/icon.ico` (multi-risoluzione, per
        Windows) da eseguire su qualunque OS; per macOS il workflow usa invece i tool nativi
        `sips`/`iconutil` (nessuna dipendenza aggiuntiva, `.icns` più affidabile) per produrre
        `packaging/build/icon.icns` da un iconset temporaneo — la risoluzione più alta
        (1024, `icon_512x512@2x`) è un upscale della sorgente 512x512, unico asset disponibile.
        `packaging/build/` è gitignored (matcha il pattern esistente `build/`, senza slash
        iniziale — nessuna nuova regola necessaria).
        - **macOS**: l'icona del launcher `Cartellino UniSA.app` (non della CLI sciolta, che
          in Terminale non mostra comunque un'icona propria) viene sostituita **dopo**
          `osacompile` e **prima** della firma, così viene notarizzata/staplata insieme al resto.
          `osacompile` chiama di default l'icona `applet.icns` con `CFBundleIconFile = applet`:
          basta sovrascrivere quel file con il nostro `.icns` mantenendo lo stesso nome. Il
          bundle include però anche un `Assets.car` (asset catalog compilato) referenziato da
          `CFBundleIconName`, che su macOS moderni ha **priorità** su `CFBundleIconFile` se
          presente — verificato rimuovendo `Assets.car` e la chiave `CFBundleIconName` (via
          `PlistBuddy -c "Delete :CFBundleIconName"`) su una build di prova locale: senza questo
          passo l'icona sostituita verrebbe ignorata a favore del contenuto (default) dell'asset
          catalog.
        - **Windows**: l'icona viene incorporata direttamente nell'eseguibile da PyInstaller
          (`icon=` in `EXE()`, `packaging/cartellino.spec` — condizionale a `sys.platform ==
          "win32"`, dato che questo spec non produce un vero bundle `.app` via `BUNDLE()` e
          quindi `icon=` non avrebbe effetto su macOS/Linux). Le voci `[Icons]` di
          `installer.iss` puntano già a `cartellino-unisa.exe`, quindi ereditano l'icona
          incorporata senza bisogno di `IconFilename` esplicito; `SetupIconFile` imposta invece
          l'icona del `setup.exe` stesso (Esplora risorse/procedura guidata), file distinto
          dall'eseguibile installato.
        - **Linux**: nessuna icona per `.deb`/`.rpm` — richiederebbe un file `.desktop` e
          l'installazione dell'icona nel tema icone di sistema (`/usr/share/icons/...`),
          infrastruttura che non esiste ancora nel repo (l'app si lancia da riga di comando, non
          da un launcher grafico) — fuori scope per questa modifica.
      - **Chiusura automatica, scelta del terminale, finestra massimizzata** (v2.0.3):
        `launcher.applescript` non apre più solo Terminal.app — dispatcher verso uno di tre
        blocchi (`launchInTerminalApp`/`launchInGhostty`/`launchInITerm2`) in base a un bundle id
        scelto dall'utente. **Warp escluso di proposito**: nessun supporto AppleScript (verificato
        — richiesta aperta dal 2022 su GitHub, mai implementata), nessun modo di
        lanciare/tracciare/chiudere/ridimensionare una finestra Warp via script.
        - **Persistenza separata da `config.toml`**: `macos_terminal.txt` (stessa cartella di
          `config.toml`, file distinto) contiene una riga col bundle id scelto — letto/scritto
          in AppleScript senza parsing TOML, e da `cartellino/tui/macos_terminal.py` lato Python
          (usato solo da `SettingsScreen`, campo "Terminale (solo macOS)" gated da
          `sys.platform == "darwin"`, primo codice OS-conditional del repo Python). File separato
          perché il picker gira **prima** di qualunque cosa Python, quindi prima dell'onboarding,
          quando `UserConfig` non è costruibile (`current_year` obbligatorio, senza default).
        - **`run script` per Ghostty/iTerm2, non `tell application id` diretto** — scoperta
          critica in fase di implementazione: `osacompile` deve risolvere la terminologia
          AppleScript di un'app (comandi non-Standard-Suite come `new window with configuration`)
          **al momento della compilazione**, non solo a runtime. Il runner CI (`macos-latest` su
          GitHub Actions) non ha né Ghostty né iTerm2 installati — solo Terminal.app (di sistema).
          Un `tell application id "com.mitchellh.ghostty" to <comando specifico>` scritto
          direttamente nel file fallirebbe quindi la compilazione in CI. Soluzione: i blocchi
          Ghostty/iTerm2 costruiscono il proprio codice come stringa AppleScript ed eseguono con
          `run script ... with parameters {...}` (i valori dinamici passano come parametri,
          niente escaping manuale di quote annidate) — la risoluzione della terminologia avviene
          così solo a runtime, sulla macchina dell'utente finale che avrà scelto quell'app solo se
          installata. Verificato: un file che referenzia Ghostty/iTerm2 solo dentro `run script`
          compila con `osacompile` anche senza quelle app installate.
        - **Terminal.app**: `do script` restituisce un riferimento diretto alla tab, quindi
          `repeat while busy of t` è un polling preciso (chiude esattamente la finestra aperta,
          non "una finestra Terminal.app qualunque"). Massimizzazione via `bounds of front window`
          impostato a un rettangolo volutamente più grande dello schermo reale (es.
          `{0, 0, 4000, 4000}`): il window server clippa alle dimensioni reali, evitando di dover
          chiedere un secondo permesso Automazione solo per interrogare Finder/System Events sulla
          risoluzione — scelta esplicita dell'utente: "finestra massimizzata", non fullscreen
          nativo macOS (Space dedicato), per evitare il permesso Accessibilità aggiuntivo che
          servirebbe per simulare la scorciatoia da tastiera via System Events.
        - **Ghostty** (AppleScript in preview da v1.3, soggetto a modifiche in v1.4): verificato a
          mano con `sdef`/`osascript` su Ghostty realmente installato. Il dizionario NON ha un
          `do script` atomico né un verbo "toggle_fullscreen" diretto: si crea la finestra con
          `new window with configuration {initial input:...}` (record "surface configuration",
          `initial input` = testo inviato al terminale come se digitato — non il campo `command`,
          la cui semantica shell non è documentata con certezza) e si massimizza con il comando
          generico `perform action "toggle_fullscreen" on <terminal>` (non su una "window" — va
          ottenuto `focused terminal of (selected tab of <window>)`). Nessuna proprietà
          "busy"/di stato del processo: l'unico modo per chiudere a fine esecuzione è appendere
          `osascript -e 'tell application id "com.mitchellh.ghostty" to close window (front
          window)'` alla riga di comando stessa — limite noto e accettato, potrebbe chiudere "la"
          finestra Ghostty frontmost, non necessariamente quella aperta qui, se un'altra diventa
          frontmost nel frattempo (non risolvibile con l'API attuale).
        - **iTerm2**: testato a mano (non solo da documentazione) dopo l'installazione durante lo
          sviluppo di questa feature — e la documentazione ufficiale si è rivelata fuorviante su
          due punti concreti: (1) `create window with default profile command` **non restituisce
          un riferimento valido alla finestra creata** (torna sempre `missing value`, bug
          riproducibile, nonostante il dizionario dichiari `result type window`), e la proprietà
          `current window` dell'applicazione è ugualmente inaffidabile — quindi niente polling
          preciso su una sessione specifica come per Terminal.app, si usa lo stesso meccanismo di
          self-close appeso al comando già usato per Ghostty, con lo stesso limite noto; (2) la
          proprietà per "massimizzata" non è `fullscreen` (come suggerito da fonti generiche) ma
          `zoomed` (il classico zoom del pulsante verde macOS, confermato funzionante) — avvolta
          in un `try` comunque, per non rompere il lancio se una versione futura di iTerm2
          cambiasse ancora nome/comportamento.
  - **Windows `.exe`**: Inno Setup (`packaging/windows/installer.iss`, compilato con `ISCC.exe`
    installato via `choco install innosetup`), payload = stessa cartella onedir. **Non firmato**
    per ora — `ignored/signed_windows.md` (non versionato) raccoglie le opzioni valutate
    (certificato OV esportabile con lo stesso pattern del `.p12` macOS, EV via servizio di firma
    cloud dato che la chiave non è esportabile, o SignPath.io gratuito per OSS) da decidere in un
    secondo momento.
  - **Linux `.deb`/`.rpm`**: `fpm` (Ruby gem, installato in CI con `gem install fpm` +
    `apt-get install rpm ruby-dev build-essential` per il target rpm, che richiede `rpmbuild`),
    un solo comando per formato dalla stessa cartella onedir mappata su `/opt/cartellino-unisa/`,
    nessun file `.spec`/`control` scritto a mano. `packaging/linux/postinstall.sh` (via
    `--after-install`) crea il symlink in `/usr/local/bin`, stesso schema del `.pkg` macOS.
  - La versione passata a tutti e tre gli strumenti viene estratta dal **tag git** (`v2.0.0` →
    `2.0.0`), non da `pyproject.toml`: più robusto in CI, dato che il bump versione precede
    sempre il tag per convenzione del progetto.
  - Nel job `release`, i quattro nuovi artifact (già file singoli pronti) vengono copiati
    direttamente in `release/` senza passare dallo step di compressione zip, che resta solo per
    gli asset onedir storici (necessario perché `zip` non è disponibile in Git Bash su
    `windows-latest`, quindi la compressione va fatta sempre nel job `release`, `ubuntu-latest`).
  - **Nome degli artefatti della release** (da `v2.0.2` in poi, sia draft che pubbliche): ogni
    file allegato alla release (zip onedir, `.pkg`, `.exe`, `.deb`, `.rpm`) include versione e
    commit nel nome, es. `cartellino-unisa-setup-2.0.2_rc5-27c435a.exe`. Calcolati una sola volta
    nello step "Calcola versione e commit per il nome degli artefatti" (`release.yml`, job
    `release`): `version_slug` da `GITHUB_REF_NAME` (tag) con `-` sostituito da `_` (es.
    `v2.0.2-rc5` → `2.0.2_rc5` — l'underscore evita l'ambiguità con il `-` che separa poi versione
    e sha nel nome file finale) e `short_sha` da `git rev-parse --short HEAD`. Lo step successivo
    di compressione/copia usa questi due valori per rinominare esplicitamente ogni artefatto per
    tipo (non un suffisso automatico generico sul nome originale, che per `.deb`/`.rpm` prodotti
    da `fpm` avrebbe già contenuto una propria versione, duplicandola nel nome finale).
  - **Packaging combinato TUI+GUI** (Fase 12-13 TODO_gui.md, v3.0.0): `packaging/cartellino.spec`
    usa due `Analysis`/`EXE` distinti (entrypoint ed hiddenimports diversi: la GUI non importa
    Textual/selenium direttamente) uniti con `MERGE`, che deduplica i moduli/binari condivisi
    (pandas, pyarrow, PySide6, ecc.) nell'onedir finale invece di raddoppiarli — un solo
    `dist/cartellino-unisa/` con dentro sia `cartellino-unisa` (console) sia
    `cartellino-unisa-gui` (windowed, `console=False` in `EXE()`). Nessun `hiddenimport`
    aggiuntivo per PySide6 (hook PyInstaller propri, bundled in `PySide6-Essentials`/
    `PySide6-Addons`); gli hiddenimports selenium vanno duplicati anche nell'`Analysis` della GUI
    perché `cartellino/gui/workers.py` importa `get.py` per il download.
    - **macOS, due launcher `.app` nello stesso `.pkg`**: il launcher AppleScript esistente
      (sopra) è stato **rinominato** da "Cartellino UniSA.app" a
      "Cartellino UniSA (Terminale).app" — quel nome ora appartiene al nuovo launcher GUI
      (`packaging/macos/gui_launcher/`, decisione presa con l'utente prima di procedere: la GUI
      eredita il nome "principale", comportamento atteso da un doppio click da Finder/Launchpad).
      Il nuovo launcher non usa AppleScript: la GUI è già una finestra nativa, quindi
      `Contents/MacOS/cartellino-unisa-gui-launcher` è un semplice script di shell che fa `exec`
      del binario installato (path assoluto, stesso motivo del launcher TUI) — niente picker
      "quale terminale", niente entitlement `com.apple.security.automation.apple-events` (nessun
      Apple Event da inviare). Firmato con la stessa identity Developer ID Application, notarizzato
      e staplato con lo stesso trattamento del launcher TUI (stesso loop nello step di
      notarizzazione, non più due step quasi identici separati).
    - **Bug reale trovato nella prima release-candidate reale (`v3.0.0-rc1`), non riproducibile
      in locale**: `packaging/macos/gui_launcher/Contents/Resources/` era una cartella vuota nel
      sorgente — Git non traccia le cartelle vuote, quindi dopo il checkout in CI la cartella non
      esisteva affatto e `cp packaging/build/icon.icns ".../Resources/icon.icns"` falliva con
      "No such file or directory". Le verifiche locali (build reali con `uv run pyinstaller`)
      non l'avevano mai riscontrato perché lì la cartella esisteva comunque sul filesystem locale
      (creata a mano durante lo sviluppo), anche se non tracciata da Git — solo un vero checkout
      Git (come fa CI) espone il problema. Fix: `mkdir -p` esplicito prima della `cp`
      nel workflow, non affidarsi a cartelle vuote committate. **Verificato che si ripete anche
      per altre cartelle vuote nel repo**: nessun'altra riscontrata, ma è la lezione generale da
      questo bug — una cartella vuota nel working tree locale non garantisce che esista dopo un
      `git clone`/checkout.
    - **Trigger del workflow**: `on.push.tags` era ancora `"v2.*"` (mai aggiornato prima di questa
      fase, perché tutte le verifiche precedenti erano state fatte in locale, mai con un vero tag
      pushato) — un tag `v3.0.0-rc1` non faceva partire alcuna run. Generalizzato a `"v[0-9]*"`
      così non andrà più toccato ad ogni bump di versione major futuro.
    - Symlink aggiuntivi (`cartellino-unisa-gui` in `/usr/local/bin`/`/opt/.../` a seconda dell'OS,
      `packaging/macos/postinstall`/`packaging/linux/postinstall.sh`) e voci `[Icons]` aggiuntive
      nell'installer Windows (`packaging/windows/installer.iss`, "Cartellino UniSA" ora punta a
      `cartellino-unisa-gui.exe`, "Cartellino UniSA (Terminale)" a `cartellino-unisa.exe`) — nessuna
      icona/voce desktop per la GUI su Linux (fuori scope, richiederebbe un file `.desktop` e
      l'installazione nel tema icone di sistema, infrastruttura non ancora nel repo).

## Architecture

**Entry point**: `main.py` — Typer CLI that chains `get.run()` and `process.run()`.

**`get.py`** — Selenium scraper that logs into `presenze.unisa.it`, navigates the cartellino page, paginates through all rows, and saves to `data/{year}/input/cartellino.xlsx`.

**`process.py`** — Main processing pipeline (`processa_dati`):
1. Reads `data/{year}/input/cartellino.xlsx`, explodes multi-value `Voci Base` cells (separated by `\xa0&-&\xa0`), and extracts a `Codice` field.
2. Filters by relevant codes (`OE-DIU`, `OO-DIU`, `SRC`, `TCK`, `VSG`, `STRSOS`, etc.) to produce separate DataFrames.
3. Calculates overtime (`OE-DIU` rows), groups them into compensatory rests (each = 7h 12m), and correlates with used rest dates from `SRC` rows or `riposi_usati.txt`.
4. Writes outputs to `data/{year}/output/`.

**`processor/cartellinoprogetto.py`** — `CartellinoProgetto` class distributes project hours (CUP: D43C22005040001) across working days, capped by `max_project_hours_per_day` and `max_project_hours`. Writes monthly sheets to `data/{year}/output/ore_svolte_per_giorno/`.

**`model/`** — Pydantic models: `RiposoCompensativo` (groups overtime entries toward a 7h12m threshold) and `OreInserite` (single day's overtime contribution).

### Pacchetto `cartellino/` (percorso `cartellino_v2.py`, v2.0.0 in corso)

- **`cartellino/credentials.py`** — wrapper sottile su `keyring` per le credenziali UniSA
  (`get_credentials`/`set_credentials`/`delete_credentials`, service `"cartellino-unisa"`).
- **`cartellino/user_config.py`** — dataclass `UserConfig` (letta/scritta come TOML in
  `platformdirs.user_config_dir("cartellino-unisa")/config.toml`, via `tomllib`/`tomli_w`) e
  `migrate_from_env_if_needed` per la migrazione one-shot da `.env` legacy.
- **`cartellino/config.py`** — `Config.load()` è il punto d'ingresso principale: usa
  `UserConfig`/migrazione, con fallback su `Config.from_env()` (puro `.env`/env vars) se non c'è
  né `config.toml` né `.env` valido (utile per CI/ambienti scriptati).
- **`cartellino/cartellino.py`** — `Cartellino.load()` legge il cartellino grezzo da **Feather**
  (`cartellino.feather`, formato primario, via `pd.read_feather`/`to_feather`) invece che da xlsx;
  se il Feather non esiste ma c'è un `cartellino.xlsx` legacy, esegue una migrazione one-shot
  (legge l'xlsx, riscrive subito il Feather) così le esecuzioni successive non toccano più l'xlsx.
  `get.py` (funzione `ottieni_cartellino`) scrive direttamente in Feather dopo lo scraping.
- **`cartellino/ore_helpers.py`** — `estrai_ore_minuti`/`somma_ore_per_codici`: helper condiviso
  per estrarre ore/minuti dal pattern `HH.MM` di "Voci Base", generalizzato da quanto usato in
  `OreEccedenti._elabora` per `OE-DIU`; riusabile per qualunque codice con lo stesso formato
  (es. `SCN`, `CRE` per il saldo mensile della dashboard).
- **`cartellino/export_utils.py`** — `save_sheets(sheets, output_path, fmt)`: scrive uno o più
  DataFrame in xlsx (un foglio per voce, stile tabella) o csv (un file per foglio). Usato da
  `Statistiche.salva`, `CreditoOre.salva`, `OreGiornaliere.salva`,
  `OreEccedenti.salva_dettaglio` per il parametro `fmt` (`Config.export_format`, scelto nella
  TUI in Impostazioni).
- **`cartellino/timesheet_runner.py`** — `esegui_timesheet_progetto`/`risolvi_percorso_timesheet`:
  sequenza `ConfigTimesheet.from_yaml` → `TimesheetProgetto.salva` → `RendicontoExcel.genera`
  (se `template_rendiconto` è impostato), condivisa tra `cartellino_v2.py` (flag
  `--timesheet-progetto`) e la schermata Timesheet della TUI.
- **`cartellino/tui/`** — TUI Textual (Fase 4 TODO v2.0.0, entrypoint `cartellino_tui.py`):
  - `app.py` — `CartellinoApp`, instrada verso `OnboardingScreen` se manca `config.toml`
    (`Config.load()`), altrimenti verso `UpdateScreen` (sopra una `DashboardScreen`, per l'`Esc`)
    se manca ancora `cartellino.feather` nella cartella dati configurata — "primo avvio" per
    quella cartella, che può cambiare in qualunque momento da Impostazioni — o verso
    `DashboardScreen` normalmente. Versione mostrata in header letta da `pyproject.toml` via
    `tomllib` (il progetto ha `tool.uv.package = false`, quindi non è installato come pacchetto
    e `importlib.metadata.version()` non funzionerebbe).
    - **Persistenza del tema** (palette comandi Textual, `^p` → Theme): `on_mount` applica
      `UserConfig.theme` (se presente) a `self.theme` **prima** di iscriversi a
      `self.theme_changed_signal` — nell'ordine inverso, applicare il tema salvato farebbe
      scattare subito il salvataggio dello stesso valore appena letto. Ogni cambio successivo
      dalla palette pubblica sul signal (`App._watch_theme`), gestito da `_save_theme` che
      ricarica `UserConfig` da disco, aggiorna solo il campo `theme` e salva — nessun effetto
      prima del completamento dell'Onboarding (`UserConfig.load()` ritorna `None` finché
      `config.toml` non esiste, dato che richiede `current_year`).
  - `logging_handler.py` — `RichLogHandler`, inoltra i record di `logging` a un widget
    `RichLog` in modo thread-safe (`App.call_from_thread`), usato dalla schermata di
    aggiornamento durante il download Selenium (lanciato con `@work(thread=True)`); il testo va
    escapato (`rich.markup.escape`) perché può contenere `[...]` (es. path chromedriver) che
    romperebbero il parsing markup del `RichLog`.
  - `screens/onboarding.py`, `dashboard.py`, `update.py`, `settings.py`, `reports.py`,
    `timesheet.py`, `folder_picker.py`, `date_escluse.py`, `credentials.py`, `statistiche.py` —
    una schermata per ciascuna voce del
    TODO Fase 4 (più `folder_picker.py`, modale `DirectoryTree` riusata da Impostazioni per
    scegliere cartella dati/output); costruite sul layer di dominio esistente (`Cartellino`,
    `OreEccedenti`, `CreditoOre`, `Statistiche`, `OreGiornaliere`, `TimesheetProgetto`) senza
    modificarne la logica di calcolo. `settings.py` gestisce anche `data_ticket.txt` (widget
    `MaskedInput`, template `DD-MM-YYYY`) e le impostazioni `UserConfig.data_folder`/
    `output_folder` che risolvono rispettivamente `Config.input_folder` (dove va
    `cartellino.feather`) e `Config.output_folder` (se diverso dal default
    `data_folder/{anno}/output`). `date_escluse.py` (raggiungibile da un pulsante in
    Impostazioni) gestisce `date_escluse.txt`: aggiunta (`MaskedInput` data + ora opzionale) e
    rimozione per riga, stesso formato letto da `OreEccedenti._elabora`
    (`DD-MM-YYYY` = giornata intera esclusa, `DD-MM-YYYY HH:MM` = sottrae solo quell'orario).
    `credentials.py` (`CredentialsScreen`, raggiunta dal pulsante "Modifica credenziali" in
    Impostazioni) isola username/password in una schermata separata invece di campi inline;
    ritorna `True`/`False` via `Screen.dismiss()` + callback così Impostazioni sa quando
    aggiornare la riga di stato "Credenziali UniSA: impostate (username: ...)".
    `statistiche.py` (`StatisticheScreen`, raggiunta dal pulsante "Statistiche" della
    Dashboard) mostra a schermo (in una `DataTable`, senza scrivere file) le stesse 7 categorie
    di `Statistiche.calcola()` di `statistiche.xlsx` (`statistica_ticket` → "Buoni pasto",
    `ferie`, `permessi_gravi_motivi`, `entrata_ritardo`, `straordinari`,
    `visite_specialistiche`, `malattia`), un pulsante colorato diversamente per categoria,
    disabilitato se il relativo DataFrame è vuoto. `Statistiche.calcola()` non solleva più
    `FileNotFoundError` se manca `data_ticket.txt`: salta solo i fogli `ticket`/
    `statistica_ticket` (con un `log.warning`), lasciando le altre categorie utilizzabili — la
    Dashboard mostra anche una sezione "Ticket da ricevere" (righe di `ticket` con
    `Da ricevere == 1`, dalla stessa `Statistiche`). Un ottavo pulsante, "Riposo compensativo",
    mostra un `MarkdownViewer` (invece della `DataTable` usata per le altre 7 categorie: il
    contenuto — un titolo + tabella per ogni riposo compensativo — non è tabulare come le altre,
    e il TOC del `MarkdownViewer` aiuta a saltare tra i riposi) al posto della `DataTable`
    (`display` alternato tra i due widget). Contenuto prodotto da
    `OreEccedenti.riposi_markdown()` (nuovo metodo, accanto a `salva_testo()` che scrive
    `riposi_compensativi.txt`): **non** legge/riformatta quel file — richiama la stessa
    `OreEccedenti.raggruppa()` con la stessa logica di scelta `riposi_usati` (`cfg.min_date` →
    `get_date_usate_from_src`, altrimenti `get_date_usate_from_file`) già usata da
    `CartellinoProcessor.run` per il report `"riposo"`, così questa vista resta sempre coerente
    con le stesse regole del report anche se quest'ultimo cambia, senza doverle duplicare o
    disallinearsi da un file scritto in un momento diverso.
  - Nota implementativa: `DashboardScreen.on_screen_resume`/`_build_body` ricostruiscono i
    widget con `Vertical(*children)` (costruttore diretto), non con `with Vertical(): yield ...`
    — quel pattern di composizione funziona solo dentro una vera chiamata a `compose()` (si
    appoggia allo stack interno `App._compose_stacks`), mentre `_build_body` viene richiamato
    anche da `on_screen_resume` per rinfrescare i dati al ritorno da un'altra schermata, fuori
    da quel contesto. Va ricostruito solo il container `#dashboard-body`, non l'intero screen
    via `recompose()`: un `recompose()` pieno ricreerebbe anche l'`Header`, lasciando in sospeso
    il suo task interno di set-title contro l'istanza appena rimossa e rompendo la gestione del
    prossimo evento in Textual.
  - **Controllo aggiornamenti dell'app** (post-v2.0.0, issue GitHub #3): `cartellino/update_checker.py`
    (`check_for_update(current_version) -> ReleaseInfo | None`), nessuna dipendenza da Textual —
    chiama `GET /repos/staffDiUnisa/CartellinoUniSA/releases/latest` con `urllib.request` di
    stdlib (nessuna nuova dipendenza runtime: niente `requests`/`httpx`) e confronta la tupla
    `(major, minor, patch)` col tag della release più recente (l'endpoint `/releases/latest`
    esclude di suo draft/prerelease, coerente con la convenzione del progetto di non taggare
    mai una sezione CHANGELOG per le `-rcN`). **Niente self-update automatico**: il binario è
    pacchettizzato **onedir** (non sostituibile file-per-file), il `.pkg` macOS è
    firmato/notarizzato/staplato (non replicabile da un updater in-app) e l'`.exe` Windows non è
    sovrascrivibile mentre è in esecuzione — la nuova schermata `cartellino/tui/screens/app_update.py`
    (`AppUpdateScreen`, nome scelto per non confondersi con `UpdateScreen` che aggiorna i *dati*
    del cartellino, non l'app) si limita a mostrare le note di rilascio e ad aprire la pagina
    GitHub Release nel browser di sistema (`webbrowser.open`), lasciando l'installazione manuale
    come oggi. Innescato in due punti, entrambi via worker Textual in thread
    (`@work(thread=True)`, stesso pattern di `UpdateScreen._scarica`) per non bloccare la UI:
    on-demand dal pulsante "Controlla aggiornamenti" in Dashboard, e all'avvio da
    `CartellinoApp.on_mount()` (solo se non è il primo avvio/onboarding, e solo se
    `UserConfig.check_updates_on_startup` — nuovo campo, default `True`, toggle in Impostazioni —
    è vero); il check in avvio fallisce silenziosamente (nessuna notifica) se la rete non è
    disponibile o l'API non risponde, per non degradare l'esperienza di avvio offline.

### Pacchetto `cartellino/gui/` (percorso `cartellino_gui.py`, TODO_gui.md, v3.0.0)

GUI desktop PySide6, affianca la TUI senza sostituirla (stesso layer di dominio riusato senza
modifiche in tutte le schermate). Nessuna dipendenza da Textual: pattern di navigazione e widget
sono Qt nativi, non un porting 1:1 dei widget Textual.

- **`app.py`** — `MainWindow`, mirror di `CartellinoApp` ma con `QStackedWidget` al posto dello
  screen stack di Textual: le schermate primarie (Onboarding/Update/Dashboard/Reports/Timesheet/
  Statistiche/Settings/DateEscluse) vivono tutte nello stesso stack e la navigazione tra loro
  cambia pagina (`stack.setCurrentWidget`), non impila finestre — i popup con valore di ritorno
  (Credentials, App update) usano invece `QDialog` modali separati, fuori dallo stack.
  `reload_config_and_route()` è la stessa identica logica di instradamento di
  `CartellinoApp.reload_config_and_route` (Onboarding se manca `config.toml`, Update se manca il
  feather, altrimenti Dashboard + controllo aggiornamenti all'avvio), riusata senza modifiche.
  `_app_version()`/`_bundle_base()` risolvono `pyproject.toml` con lo stesso schema `sys._MEIPASS`
  già usato da `cartellino/tui/app.py` per il binario PyInstaller.
- **`workers.py`** — `QtLogHandler`+`DownloadWorker`+`UpdateCheckWorker`, mirror concettuale di
  `RichLogHandler`+`@work(thread=True)`+`App.call_from_thread`: Qt gestisce nativamente la stessa
  cosa, un `Signal` emesso da un thread diverso da quello del ricevente diventa automaticamente
  una `QueuedConnection` (eseguita sul thread del ricevente), niente equivalente esplicito di
  `call_from_thread` da scrivere a mano. `UpdateCheckWorker` è condiviso tra il pulsante
  "Controlla aggiornamenti" della Dashboard e il controllo automatico all'avvio di `MainWindow`
  (era prima duplicato in `dashboard.py` come classe privata, spostato qui quando è servito
  anche a `app.py`).
- **`screens/`** — una classe per schermata, mirror di `cartellino/tui/screens/`, costruite sullo
  stesso layer di dominio esistente senza modificarne la logica di calcolo:
  - `onboarding.py`/`settings.py`/`credentials.py` (`CredentialsDialog`, `QDialog` con
    `QPushButton` custom "Salva"/"Annulla" — **non** `QDialogButtonBox` con pulsanti standard: le
    stringhe standard di Qt come "Save"/"Cancel" restano in inglese senza caricare le traduzioni
    Qt integrate, non bundled nell'app, incoerente con un progetto interamente in italiano; bug
    reale trovato in QA, Fase 14 TODO_gui.md) usano `UserConfig.save()`/`set_credentials()`
    riusati identici dalla TUI.
  - `settings.py` **non** ha il campo "Terminale (solo macOS)" della TUI (non applicabile — lancio
    come app nativa, nessun terminale da scegliere) e usa `QFileDialog.getExistingDirectory`
    nativo per cartella dati/output al posto del `FolderPickerScreen` custom (semplificazione
    prevista dal piano, `cartellino/tui/screens/folder_picker.py` non ha equivalente lato GUI).
    "Gestisci date escluse" apre `date_escluse.py` (`QTableWidget` con un pulsante "Rimuovi" per
    riga via `setCellWidget`, stesso formato file di `date_escluse.txt`).
  - `dashboard.py`/`settings.py` avvolgono il contenuto in un `QScrollArea`
    (`setWidgetResizable(True)`): senza, su una finestra piccola il layout costringeva la
    finestra a crescere oltre lo schermo pur di mostrare tutti i widget invece di scorrere (bug
    trovato in QA catturando screenshot a dimensioni ridotte, Fase 14 TODO_gui.md) — mirror del
    `VerticalScroll` già usato dalle stesse due schermate nella TUI. Per la Dashboard solo il
    testo delle sezioni scorre (`QScrollArea` dedicato attorno alla sola `sections_label`), i
    pulsanti di navigazione restano sempre visibili in fondo, a differenza della TUI dove
    scrollano via insieme al resto.
  - `statistiche.py` usa `_DataFrameTableModel(QAbstractTableModel)` (piccolo modello scritto ad
    hoc per esporre un `pd.DataFrame` a `QTableView`: nessun drop-in Qt equivalente alla
    `DataTable` di Textual, che accetta righe direttamente) per le 7 categorie tabulari, e un
    `QTextBrowser` con `setMarkdown()` (supporto Markdown nativo Qt) per l'ottavo pulsante
    "Riposo compensativo" — stessa fonte dati `OreEccedenti.riposi_markdown()` della TUI.
  - `update.py` esegue `get.ottieni_cartellino` in un `DownloadWorker` (`QThread`) con log in
    tempo reale via `QtLogHandler` verso un `QPlainTextEdit`.
  - `app_update.py` (`AppUpdateDialog`) mostra le note di rilascio in `QTextBrowser` Markdown e
    apre la pagina GitHub Release con `QDesktopServices.openUrl` (non `webbrowser.open` — l'API Qt
    nativa) — stesso "niente self-update automatico" della TUI, stessi motivi (onedir, `.pkg`
    firmato/notarizzato, `.exe` in esecuzione). Sostituisce un `QMessageBox` usato
    provvisoriamente prima che questo dialog venisse scritto (Fase 3 → Fase 11 TODO_gui.md). Il
    ramo "nessun aggiornamento disponibile" ha un `layout.addStretch()` esplicito: senza, uno
    spazio senza widget "expanding" da assorbire farebbe distribuire lo spazio extra tra i widget
    invece che in fondo se l'utente ridimensiona manualmente il dialog (stesso bug di
    `CredentialsDialog`, stessa causa, trovato e corretto nello stesso giro di QA).
- **QA senza framework di test automatico** (`pytest-qt` resta un'opportunità futura, fuori
  scope): verificato ogni schermata catturando uno screenshot reale con `QWidget.grab()` — funziona
  anche con `QT_QPA_PLATFORM=offscreen` (rendering software Qt, non serve un vero window server),
  utile per CI headless in futuro. Non sostituisce test automatici, ma è più affidabile di un
  controllo solo testuale ("non va in crash") per bug di layout — è così che sono stati trovati i
  bug di spaziatura/scroll sopra.

## Data flow

```
data/{year}/input/cartellino.xlsx       ← downloaded by get.py
data/{year}/input/date_escluse.txt      ← dates to exclude from overtime (format: DD-MM-YYYY or DD-MM-YYYY HH:MM)
data/{year}/input/riposi_usati.txt      ← fallback for used rest dates (format: YYYY-MM-DD per line)
data/{year}/input/data_ticket.txt       ← date from which meal tickets were paid (format: DD-MM-YYYY)

data/{year}/output/cartellino.xlsx      ← processed cartellino with Codice column
data/{year}/output/riposo_compensativo.xlsx
data/{year}/output/riposi_compensativi.txt
data/{year}/output/credito_ore.xlsx
data/{year}/output/statistiche.xlsx     ← multi-sheet: tickets, overtime, sick leave, holidays, etc.
data/{year}/output/ore_giornaliere.xlsx
data/{year}/output/ore_svolte_per_giorno/{MM}_{month}.xlsx
```

Il diagramma sopra descrive il percorso legacy (`main.py`/`process.py`). Il percorso
`cartellino_v2.py` (`data/v2/{year}/...`) usa lo stesso schema di output, ma per l'input usa
**`data/v2/{year}/input/cartellino.feather`** come formato primario (vedi `Cartellino.load()`
sopra); `cartellino.xlsx` nella stessa cartella è supportato solo come sorgente legacy per la
migrazione one-shot al primo avvio.

## Key codes in the cartellino

| Code | Meaning |
|------|---------|
| `OE-DIU` | Overtime hours (ore eccedenti) |
| `OO-DIU` | Daily hours worked (ore ordinarie) |
| `SRC` | Used compensatory rest |
| `TCK` | Meal ticket |
| `VSG` | Specialist visit |
| `STRSOS` / `FSTLAV` / `OS-FSD` | Overtime |
| `FER` / `FEV` / `FST` | Holidays |
| `MAL` / `RIC` | Sick leave |

## Important implementation notes

- `current_year` in `process.py` is a module-level global overwritten at runtime by `CURRENT_YEAR` env var; functions like `scrivi_riposi_compensativi` rely on this global.
- `date_escluse.txt` accepts full dates (`DD-MM-YYYY`) or datetime with time (`DD-MM-YYYY HH:MM`); the time variant subtracts the given time from that day's overtime rather than excluding the day entirely.
- `MIN_DATE_RIPOSI_USATI` takes precedence over `riposi_usati.txt`; it filters `SRC` rows from the cartellino itself to determine already-used rests.
