# TODO — Roadmap verso v2.0.0 ✅ completata

> Rilasciato come [`v2.0.0`](https://github.com/staffDiUnisa/CartellinoUniSA/releases/tag/v2.0.0)
> (precedente: [`v1.2.0`](https://github.com/staffDiUnisa/CartellinoUniSA/releases/tag/v1.2.0)).
> Obiettivo v2.0.0: TUI (Textual) al posto dei prompt CLI, credenziali in OS keyring,
> tooling `mise`/`uv` al posto di `pip`/`venv`, dashboard iniziale sullo stato del cartellino,
> eseguibili standalone per macOS/Windows/Linux — tutte le 7 fasi sotto sono completate.

Decisioni prese:
- La v2 avrà **sia TUI che flag CLI non interattivi** (per uso scriptato).
- Credenziali salvate nel **keyring nativo del SO** (libreria `keyring`), non file cifrato custom.
- Eseguibili generati con **PyInstaller in CI (GitHub Actions)**, un job per OS, allegati alla Release.
  Chrome resta dipendenza esterna obbligatoria (Selenium non è bundlabile).
- **Niente SQLite/DB relazionale.** Il file scaricato è già la cache persistente tra un'esecuzione
  e l'altra (nessun re-download necessario per vedere la dashboard). I calcoli derivati (riposi,
  credito ore, statistiche) sono ricalcolati in memoria ad ogni avvio: dataset piccolo (poche
  centinaia di righe/anno), pandas ricalcola in <1s.
- **Storage dati grezzi**: da `cartellino.xlsx` a **Feather** (`pyarrow`) — preserva meglio i dtype
  del DataFrame ed è più veloce da leggere/scrivere di un roundtrip Excel. **xlsx/csv diventano
  solo formati di export on-demand**, selezionabili da Impostazioni (default xlsx).

## Dashboard iniziale (mostrata subito all'avvio della TUI)

Legge direttamente il Feather già su disco, **senza forzare un nuovo download**:

1. **Eccezioni del mese corrente** su codici configurabili (default `ERIT`, `SCN`)
2. **Saldo ore del mese corrente**, somma di codici configurabili (default `CRE`, `OE-DIU`, `SCN`)
3. **Riepilogo riposi compensativi**, per categoria:
   - completi e confermati (tutte le ore `[OK]`, cioè `stato == "ELAB P1"`)
   - completi ma non confermati (soglia 7h12m raggiunta, ma almeno un'ora `"ELAB GG"` → `[NO]`)
   - da completare (indicando le ore mancanti, `RiposoCompensativo.ore_mancanti()`)
   - già usati (`riposo.data` valorizzata, matchata con `SRC`)
4. **Giorni di ferie già utilizzati** nell'anno corrente (`FER`/`FEV`/`FST`)
5. **Permessi per gravi motivi familiari (PMF)** utilizzati nell'anno corrente
6. Data/ora dell'ultimo download (mtime del file Feather), per capire se i dati sono freschi
7. Se il Feather non esiste ancora (primo avvio), stato vuoto che invita al download

### Note tecniche sulla categorizzazione dei riposi compensativi

`OreEccedenti.raggruppa()` (esistente, `cartellino/ore_eccedenti.py`) già restituisce
`list[RiposoCompensativo]`. La categorizzazione per la dashboard è puro post-processing su quel
risultato, nessuna modifica alla logica di raggruppamento:

```
per ogni riposo in riposi:
    se riposo.data è valorizzata            -> USATO (SRC)
    altrimenti se riposo.ore_mancanti() <= 0:
        se tutte le ore_inserite hanno stato == "ELAB P1"  -> COMPLETO E CONFERMATO
        altrimenti                                          -> COMPLETO NON CONFERMATO
    altrimenti                               -> DA COMPLETARE (mancano riposo.ore_mancanti())
```

I due soli valori di stato realmente usati nel cartellino sono `"ELAB P1"` (confermato) e
`"ELAB GG"` (non confermato) — vedi confronto letterale già esistente in
`cartellino/ore_eccedenti.py` (`salva_testo`, formattazione `[OK]`/`[NO]`).

### Note su SCN/CRE e saldo mensile configurabile

- `SCN` non esiste ancora nel codice: stesso formato di `OE-DIU` nel testo "Voci Base"
  (pattern numerico `HH.MM`), stessa logica di estrazione già in `OreEccedenti._elabora`.
- `CRE` è già presente come codice raw nel cartellino ma non filtrato (elencato tra i "codici non
  usati" da `process.py`); trattato con lo stesso pattern di estrazione.
- Serve un helper condiviso che, dato un elenco di codici, filtra le righe
  (`Cartellino._filter`, già supporta codici arbitrari) e somma le ore estratte con lo stesso
  pattern regex oggi hardcoded per OE-DIU — riusato per il saldo mensile dashboard.

### Note su ferie/PMF "utilizzati"

`cartellino/statistiche.py` oggi espone solo elenchi grezzi (`Stato`, `Data`, `Voci Base`) per
ferie e PMF, senza logica di "usato/non usato" (a differenza di `TCK`, che ha già `data_ticket.txt`
come cutoff). Per la dashboard, "giorni utilizzati" è semplicemente il conteggio delle righe già
presenti nel cartellino per quei codici — nessuna proiezione futura richiesta.

---

## Fase 1 — Migrazione ambiente: pip/venv → mise/uv ✅

- [x] Creare `pyproject.toml` (metadati progetto, `requires-python = ">=3.12"`, dipendenze da
      `requirements.txt` + nuove: `textual`, `keyring`, `platformdirs`, `pyarrow` (per Feather))
- [x] Generare `uv.lock` (`uv lock`)
- [x] Aggiungere `.mise.toml` (pin versione Python, tool `uv`, task `install`/`app`)
- [x] Rimuovere `requirements.txt` (nessun bisogno di compatibilità con `pip` legacy)
- [x] Aggiornare `README.md` / `CLAUDE.md` con le nuove istruzioni di setup
      (`mise install`, `uv sync`, `uv run ...`)
- [x] Aggiornare eventuale CI esistente per usare `mise`/`uv` invece di `pip`
      (nessuna CI esistente nel repo, nulla da migrare)

## Fase 2 — Credenziali sicure (OS keyring) + config utente ✅

- [x] Modulo `cartellino/credentials.py` con `keyring.set_password`/`get_password`
      (service name dedicato, `"cartellino-unisa"`) per USERNAME/PASSWORD UniSA
- [x] File di config TOML in cartella utente standard (via `platformdirs`,
      `cartellino/user_config.py::UserConfig`) per: `current_year`, `min_date_riposi_usati`,
      `headless`, **formato di export** (xlsx/csv, default xlsx), **codici eccezione dashboard**
      (default `["ERIT", "SCN"]`), **codici saldo mensile** (default `["CRE", "OE-DIU", "SCN"]`)
- [x] Import automatico da `.env` legacy alla prima esecuzione v2
      (`migrate_from_env_if_needed`, invocato da `Config.load()`), con raccomandazione di
      eliminare `.env` dopo la migrazione. Nota: l'"offerto da TUI" del testo originale diventa
      "automatico e silenzioso" finché la TUI (Fase 4) non esiste ancora
- [x] Aggiornare `get.py` / `cartellino/config.py` per leggere da keyring/config
      (`Config.load()`, con fallback su `Config.from_env()` se manca sia `config.toml` che `.env`)
- [x] Aggiornare `env.template`, `README.md`, `CLAUDE.md`

## Fase 3 — Storage dati: Feather per l'import, xlsx/csv solo on-demand ✅

- [x] `get.py`: dopo lo scraping, salvare il DataFrame grezzo in
      `data/v2/{anno}/input/cartellino.feather` (via `df.to_feather`) invece di scrivere
      direttamente `cartellino.xlsx`
- [x] `cartellino/cartellino.py`: generalizzato `Cartellino.from_excel`/`from_feather`/`load`,
      con fallback di migrazione one-shot da un `cartellino.xlsx` legacy se il Feather non esiste
- [x] Tutte le pipeline di output (`Cartellino.salva`, `OreEccedenti.salva_dettaglio`,
      `salva_testo`, `CreditoOre.salva`, `Statistiche.salva`) restano metodi disponibili,
      invocati **on demand** (un'azione per report), nel formato scelto in Impostazioni (xlsx o
      csv — per csv, un file per foglio dove il report è multi-sheet). Chiuso sia lato TUI
      (`ReportsScreen`, Fase 4) sia lato CLI (`cartellino_v2.py --solo-report
      cartellino,riposo,credito,statistiche,ore-giornaliere`, Fase 5/6):
      `CartellinoProcessor.run(reports=...)` genera solo i report richiesti — `None` (default)
      continua a generarli tutti, comportamento storico invariato per gli usi già scriptati.
- [x] Helper condiviso per estrarre ore da "Voci Base" dato un elenco di codici
      (`cartellino/ore_helpers.py::estrai_ore_minuti`/`somma_ore_per_codici`, generalizzazione del
      pattern regex prima duplicato in `OreEccedenti._elabora`), riusabile per il saldo mensile
      dashboard (Fase 4)

## Fase 4 — Fondamenta TUI con Textual ✅

Nuovo entrypoint `cartellino_tui.py` (Textual `App`). File principali:
`cartellino/tui/app.py`, `cartellino/tui/screens/*.py`, `cartellino/tui/logging_handler.py`.

- [x] Schermata **Onboarding/Setup**: form per credenziali/config se mancanti
      (`cartellino/tui/screens/onboarding.py`)
- [x] **Schermata Dashboard/Home** (vedi sezione dedicata sopra), con **versione app sempre
      visibile** in header/footer — letta da `pyproject.toml` via `tomllib`, non
      `importlib.metadata` (il progetto ha `tool.uv.package = false`, quindi non è installato
      come pacchetto e `importlib.metadata.version()` non funzionerebbe)
- [x] **Scelta aggiornamento**: azione esplicita "Aggiorna cartellino" (mai automatica
      all'apertura), pulsante/binding al posto del prompt Typer `y/N`
      (`cartellino/tui/screens/update.py`)
- [x] **Scelta metodo di autenticazione**: `RadioSet` (Credenziali UNISA / SPID / CIE),
      opzione UNISA disabilitata se `is_on_unisa_network()` è False (funzione esistente in
      `get.py`, riusata senza modifiche)
- [x] **Log/Progress view**: `RichLog` per output in tempo reale — refactor di
      `get.py`/`cartellino/*.py` a `logging` fatto in una sessione precedente; operazioni
      lunghe (Selenium) lanciate via `@work(thread=True)`, log inoltrati al `RichLog` da
      `cartellino/tui/logging_handler.py::RichLogHandler` (thread-safe via `call_from_thread`)
- [x] **Schermata Impostazioni**: anno, min date, formato export, liste codici configurabili
      (eccezioni + saldo mensile), gestione credenziali (keyring)
      (`cartellino/tui/screens/settings.py`)
- [x] **Report on-demand**: schermata/menu per generare singolarmente i report (riposo
      compensativo, credito ore, statistiche, ore giornaliere) nel formato scelto
      (`cartellino/tui/screens/reports.py`); supporto xlsx/csv aggiunto in
      `cartellino/export_utils.py::save_sheets` (chiuso il punto lasciato aperto in Fase 3)
- [x] **Timesheet di progetto**: selezione di uno YAML esistente in `timesheet/` e generazione
      (`cartellino/tui/screens/timesheet.py`, tramite `cartellino/timesheet_runner.py`,
      condiviso con `cartellino_v2.py`). Niente wizard di creazione YAML da zero (rimane
      un'estensione futura, vedi nota sotto)

Estensioni future non incluse in questa fase: wizard di creazione guidata di un nuovo YAML di
timesheet progetto direttamente dalla TUI (oggi resta un'operazione manuale sul filesystem).

## Fase 5 — Parità funzionale CLI non interattiva ✅

- [x] Entrypoint CLI (Typer) con flag equivalenti (`--no-aggiorna-cartellino`,
      `--timesheet-progetto`, `--auth-method {unisa,spid,cie}`, `--export-format {xlsx,csv}`,
      `--solo-report {cartellino,riposo,credito,statistiche,ore-giornaliere}`)
- [x] CLI e TUI condividono le stesse funzioni di dominio e lo stesso storage
      credenziali/config/dati (Fasi 2-3) — `timesheet_runner.py`/`export_utils.py` (Fase 4) già
      usati da entrambe; `CartellinoProcessor.run()` ora passa `cfg.export_format` ai 4 report
      configurabili (prima lo ignorava, sempre xlsx indipendentemente dalla config)
- [x] **Deciso di non unificare**: `cartellino_v2.py` (CLI non interattiva) e `cartellino_tui.py`
      (TUI) restano due entrypoint separati — `cartellino_v2.py` non è legacy nel senso di
      "superato/da rimuovere" ma il percorso non interattivo/scriptabile voluto accanto alla
      TUI, entrambi sullo stesso layer di dominio condiviso. Nessun lavoro di rimozione/merge
      previsto per la Fase 6 (packaging): PyInstaller impacchetta l'entrypoint TUI, `main.py`/
      `process.py` restano il percorso legacy pre-v2 non toccato da questa roadmap.

## Fase 6 — Packaging multipiattaforma (PyInstaller + GitHub Actions) ✅

- [x] `packaging/cartellino.spec` per PyInstaller (entrypoint `cartellino_tui.py`, **onedir**,
      non onefile — vedi nota sotto). `keyring`/`pyarrow` non hanno bisogno di hidden-imports
      manuali: hanno già hook PyInstaller propri che raccolgono submodule/metadata/data file da
      soli. `selenium` invece sì (`selenium.webdriver.chrome.{webdriver,options,service}`): il suo
      hook raccoglie solo i data file, non i submodule dei browser, e
      `selenium/webdriver/__init__.py` espone `webdriver.Chrome` con `__getattr__` a livello di
      modulo (PEP 562, lazy import), invisibile all'analisi statica di PyInstaller. Textual non ha
      bisogno di hidden-imports, ma richiede `CartellinoApp._BASE_PATH` esplicito (basato su
      `sys._MEIPASS` quando "frozen") perché altrimenti risolverebbe `CSS_PATH` con
      `inspect.getfile()`, che non punta a un file reale una volta impacchettato — stesso
      discorso per la lettura di `pyproject.toml` in `_app_version()`
      (`cartellino/tui/app.py::_bundle_base()`).
- [x] `pyinstaller` aggiunto come `[dependency-groups] build` in `pyproject.toml` (non nelle
      dipendenze runtime — è uno strumento di packaging, non serve per usare l'app)
- [x] Workflow `.github/workflows/release.yml`: build matrix macOS/Windows/Linux
      (`uv sync --group build && uv run pyinstaller packaging/cartellino.spec`), il job
      `release` comprime ogni cartella onedir in uno zip (`chmod +x` ripristinato sul binario
      prima di comprimere: `upload-artifact`/`download-artifact` non preservano sempre il bit
      +x) e allega gli zip **come draft** alla GitHub Release (trigger su push tag `v2.*`;
      pubblicazione manuale dopo revisione, non automatica). Action aggiornate a versioni che
      dichiarano runtime Node 24 (`checkout@v7`, `upload-artifact@v7`, `download-artifact@v8`,
      `mise-action@v4`, `action-gh-release@v3`) per eliminare il warning di deprecazione Node 20.
- [x] **Firma e notarizzazione macOS**: il job `build (macos-latest, ...)` importa un
      certificato Developer ID Application da secrets GitHub
      (`MACOS_CERTIFICATE`/`MACOS_CERTIFICATE_PWD`/`APPLE_ID`/`APPLE_ID_PASSWORD`/
      `APPLE_TEAM_ID` — procedura per ottenerli/generarli in `ignored/signed_macos.md`, non
      versionato), firma ogni Mach-O reale nella cartella onedir (rilevato con `file`, non per
      estensione `.so`/`.dylib`: `selenium-manager` di `selenium` è un binario nativo senza
      estensione) con `packaging/entitlements.plist` (hardened runtime +
      `disable-library-validation`), notarizza con `notarytool submit --wait
      --output-format json` controllando esplicitamente lo `status` nella risposta (senza,
      `--wait` esce con codice 0 anche a notarizzazione rifiutata). Niente step di stapling:
      confermato che non supporta un eseguibile "sciolto" (non `.app`/`.pkg`/`.dmg`).
- [x] Documentato nel `README.md` (§ "Eseguibili standalone"): istruzioni passo-passo per
      macOS/Windows/Linux, Chrome dipendenza esterna obbligatoria, avviso SmartScreen su
      Windows (nessun certificato di firma codice per Windows — macOS invece firmato/notarizzato).
- [x] **`cartellino_tui.py`**: cartella dati/log fissa (`~/.cartellino_unisa/`,
      `%LOCALAPPDATA%\cartellino_unisa\` su Windows) invece che relativa alla cwd — necessario
      per un eseguibile lanciabile da qualunque cartella (Desktop, Downloads, ecc.).

**Verificato interamente con build reali su tag di prova** (`v2.0.0-rc1`...`rc12`, poi
eliminati) **e con un uso reale end-to-end del binario macOS** (download completo funzionante).
Bug trovati e corretti, nessuno riproducibile con una build/esecuzione locale non impacchettata
— solo grazie a run CI reali + test sul binario scaricato:
1. `pyarrow` falliva l'import nel binario **onefile** scaricato da Release (funzionava in
   locale): librerie native estratte non firmate a runtime, bloccate da macOS — risolto
   passando a **onedir**.
2. Un `:` non quotato nel nome di uno step rompeva il parsing YAML del workflow.
3. `zip` non è disponibile in Git Bash su `windows-latest` — compressione spostata nel job
   `release` (sempre `ubuntu-latest`).
4. Notarizzazione rifiutata da Apple (`status: Invalid`) passava inosservata: `notarytool
   submit --wait` esce con codice 0 anche a rifiuto — va controllato lo `status` nel JSON.
5. `selenium-manager` (binario nativo senza estensione, incluso da `selenium` stesso) non
   veniva firmato dal filtro per estensione `.so`/`.dylib` → notarizzazione rifiutata.
6. Bit `+x` perso su macOS/Linux tra `upload-artifact`/`download-artifact`.
7. `ModuleNotFoundError: selenium.webdriver.chrome.webdriver` all'avvio del download (lazy
   import via `__getattr__`, invisibile a PyInstaller) → aggiunto a `hiddenimports`.
8. `ImportError: Import pyarrow failed` su un Mac con `apache-arrow` installato via Homebrew:
   `DYLD_LIBRARY_PATH`/`DYLD_FALLBACK_LIBRARY_PATH` (esportate da Homebrew) fanno caricare a
   `dyld` la libreria di sistema invece di quella bundled. Un primo tentativo con
   `os.environ.pop(...)` non bastava (dyld fissa queste variabili all'avvio del processo): serve
   un **re-exec** (`os.execve`) con ambiente ripulito.

### Estensione post-v2.0.0 — installer nativi per OS ✅

Oltre agli zip onedir sopra (che restano invariati), aggiunto un vero installer per piattaforma,
riusando la stessa cartella prodotta da PyInstaller come payload:

- [x] **macOS `.pkg`**: `pkgbuild` con un **secondo certificato**, "Developer ID Installer"
      (distinto da "Developer ID Application" usato per l'eseguibile — procedura per generarlo
      aggiunta a `ignored/signed_macos.md`; secrets `MACOS_INSTALLER_CERTIFICATE`/
      `MACOS_INSTALLER_CERTIFICATE_PWD`), notarizzato separatamente e **staplato** — a differenza
      dell'eseguibile sciolto, il `.pkg` è un formato supportato dallo stapler. `postinstall`
      (`packaging/macos/postinstall`) crea il symlink `/usr/local/bin/cartellino-unisa`.
- [x] **Windows `.exe`**: installer Inno Setup (`packaging/windows/installer.iss`, compilato con
      `ISCC.exe`). **Non firmato** per ora — `ignored/signed_windows.md` (non versionato)
      raccoglie le opzioni valutate (OV/EV/SignPath.io) e le istruzioni concrete per il percorso
      OV, da seguire quando/se si deciderà di procedere.
- [x] **Linux `.deb`/`.rpm`**: `fpm`, un solo comando per formato dalla stessa cartella onedir
      mappata su `/opt/cartellino-unisa/`; `postinstall.sh` (`packaging/linux/postinstall.sh`)
      crea lo stesso symlink in `/usr/local/bin`, stesso schema del `.pkg` macOS.
- [x] Versione per tutti e tre gli strumenti estratta dal **tag git**, non da `pyproject.toml`
      (più robusto in CI). Nel job `release`, i quattro nuovi artifact (file singoli già pronti)
      vengono copiati direttamente senza passare dallo step di compressione zip.
- [x] `README.md`/`CLAUDE.md` aggiornati con le istruzioni utente e le note tecniche.

**Verificato con build reali su tag di prova** (`v2.0.1-rc1`, poi eliminato) e pubblicato in
`v2.0.1`. Un bug trovato solo grazie alla run CI reale: `gem install fpm` falliva con
`Gem::FilePermissionError` sul runner `ubuntu-latest` (l'utente non privilegiato non ha permessi
di scrittura su `/var/lib/gems`) — risolto con `sudo gem install`.

## Fase 7 — Rilascio v2.0.0 ✅

- [x] Bump versione a `2.0.0` in `pyproject.toml`
- [x] Tag `v2.0.0` + GitHub Release con i binari allegati dalla pipeline CI (pubblicata, non più draft)

---

## Analisi dipendenze tra fasi

```
Fase 1 (mise/uv)
  ├─→ Fase 2 (keyring/config)  ──┐
  └─→ Fase 3 (Feather/export)  ──┼─→ Fase 4 (TUI) ──┬─→ Fase 6 (packaging) ─→ Fase 7 (release)
                                  │                    │
                                  └─→ Fase 5 (CLI) ────┘
```

- **Fase 1** è prerequisito puro per 2, 3, 6 (dichiara le nuove dipendenze `textual`, `keyring`,
  `platformdirs`, `pyarrow` nel `pyproject.toml`). Nessuna dipendenza in ingresso.
- **Fase 2** e **Fase 3** sono indipendenti tra loro — possono procedere **in parallelo** una
  volta chiusa la Fase 1 (toccano moduli diversi: credenziali/config vs. storage dati/pipeline
  di output). Entrambe sono prerequisito per la Fase 4 (la dashboard iniziale legge sia il
  Feather sia i codici configurabili da Fase 2) e per la Fase 5 (CLI legge lo stesso storage).
- **Fase 4** dipende da 2+3 completate (non ha senso costruire onboarding/dashboard su uno
  storage o un formato di credenziali ancora instabile). Durante la Fase 4, i `print()` in
  `get.py`/`cartellino/*.py` vengono sostituiti con `logging` — questo refactor va fatto una
  sola volta e **beneficia anche la Fase 5** (stesso layer di dominio, niente duplicazione).
- **Fase 5** può partire in parallelo alla Fase 4 (stessa base 2+3), ma il taglio finale di
  `cartellino_v2.py` legacy conviene farlo solo dopo che il layer di dominio condiviso è stato
  stabilizzato durante la Fase 4, per evitare di rifare la stessa rifattorizzazione due volte.
- **Fase 6** dipende da Fase 1 (build tool) e Fase 4 (serve un entrypoint TUI funzionante da
  impacchettare); beneficia anche del completamento di Fase 5 per impacchettare/validare pure
  il percorso CLI non interattivo.
- **Fase 7** dipende dal completamento di tutte le fasi precedenti.

**Percorso critico**: Fase 1 → (Fase 2 ∥ Fase 3) → Fase 4 → Fase 6 → Fase 7. La Fase 5 non è sul
percorso critico se sviluppata in parallelo alla Fase 4, ma richiede comunque che 2+3 siano
chiuse prima di partire.

## Stima di complessità e impatto

Stima relativa (non ore precise), pensata per sviluppo part-time da parte di una persona sola:
`S` = 1-2 giorni, `M` = 3-5 giorni, `L` = 6-10 giorni, `XL` = 10+ giorni.

| Fase | Complessità | Impatto utente | Rischio principale |
|------|:---:|:---:|---|
| 1. mise/uv | **S** | Basso (solo setup) | Basso — cambio tooling ben documentato, reversibile |
| 2. Keyring + config | **M** | Medio (cambia il flusso di setup credenziali) | Backend keyring assente su Linux headless/minimale; migrazione da `.env` da testare bene |
| 3. Feather + export on-demand | **L** | Alto (cambia formato dati e comportamento di scrittura file) | **Rischio più alto di regressione**: tocca tutta la pipeline core (`Cartellino`, `OreEccedenti`, `CreditoOre`, `Statistiche`); serve fallback di migrazione da xlsx legacy e writer CSV nuovi (oggi esiste solo il path xlsx via `apply_table_format`) |
| 4. TUI Textual | **XL** | **Alto — è il cuore della richiesta** | Superficie più ampia (più schermate, worker thread per Selenium/elaborazione bloccanti, refactor `print()`→`logging`); maggiore effort totale di tutta la roadmap |
| 5. CLI non interattiva | **M** | Medio (solo utenti che scriptano) | Duplicazione di logica se non si riusa bene il layer condiviso costruito in Fase 4 |
| 6. Packaging PyInstaller | **L** | Alto (rende l'app installabile senza Python) | Quirk specifici per OS: hidden-imports per Textual/pyarrow/Selenium, percorso cache di `webdriver-manager` in binario "frozen", avvisi Gatekeeper/SmartScreen non firmati |
| 7. Release v2.0.0 | **S** | Alto (simbolico: consegna finale) | Nessuno, è solo tagging/release una volta che 1-6 sono verdi |

**Nota**: la Fase 4 è di gran lunga la più corposa (stimabile quanto tutte le altre fasi messe
insieme) perché non è solo "wrapping" delle classi esistenti in widget, ma richiede: gestione
asincrona delle operazioni bloccanti (Selenium `WebDriverWait`, I/O su disco) tramite
`App.run_worker`, un logging bridge per il `RichLog`, e la costruzione ex-novo di 6+ schermate.
Vale la pena valutare se spezzarla in sotto-milestone incrementali (es. prima Dashboard+Onboarding
in sola lettura, poi le azioni di download/export) invece di consegnarla in un unico blocco.
