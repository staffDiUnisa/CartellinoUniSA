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
timesheet di progetto. Usa lo stesso storage di `cartellino_v2.py`
(`data/v2/{anno}/`). Vedi il pacchetto `cartellino/tui/` sotto per i dettagli.

### Packaging (Fase 6 TODO v2.0.0)

`packaging/cartellino.spec` — spec PyInstaller (onefile) per `cartellino_tui.py`:

```bash
uv sync --group build   # installa pyinstaller (dependency-group "build", non nelle
                         # dipendenze runtime: pyinstaller serve solo per impacchettare)
uv run pyinstaller packaging/cartellino.spec --noconfirm
./dist/cartellino-unisa  # .exe su Windows
```

- `keyring`, `pyarrow`, `selenium` hanno già hook PyInstaller propri (rispettivamente in
  `PyInstaller.hooks` e `_pyinstaller_hooks_contrib`) che raccolgono automaticamente
  submodule/metadata/data file — nessun `hiddenimports` manuale necessario per questi tre.
- `cartellino/tui/app.py::CartellinoApp._BASE_PATH`/`_bundle_base()`: Textual risolve `CSS_PATH`
  con `inspect.getfile(CartellinoApp)`, che una volta "frozen" non punta a un file reale su disco
  (il modulo vive nell'archivio PYZ, non estratto). `_BASE_PATH` viene quindi impostato in base a
  `sys._MEIPASS` quando l'app è frozen; lo stesso vale per la lettura di `pyproject.toml` in
  `_app_version()`. Il file `cartellino/tui/app.tcss` e `pyproject.toml` sono dichiarati come
  `datas` nello spec, con gli stessi percorsi relativi attesi da `_bundle_base()`.
- `.github/workflows/release.yml`: build matrix macOS/Windows/Linux su push di un tag `v2.*`,
  allega i binari come **draft** alla GitHub Release (pubblicazione manuale dopo revisione).
- Chrome resta dipendenza esterna obbligatoria (Selenium non è imbottigliabile); i binari non
  sono firmati/notarizzati (avvisi Gatekeeper/SmartScreen, documentati in README.md).

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
    `Da ricevere == 1`, dalla stessa `Statistiche`).
  - Nota implementativa: `DashboardScreen.on_screen_resume`/`_build_body` ricostruiscono i
    widget con `Vertical(*children)` (costruttore diretto), non con `with Vertical(): yield ...`
    — quel pattern di composizione funziona solo dentro una vera chiamata a `compose()` (si
    appoggia allo stack interno `App._compose_stacks`), mentre `_build_body` viene richiamato
    anche da `on_screen_resume` per rinfrescare i dati al ritorno da un'altra schermata, fuori
    da quel contesto. Va ricostruito solo il container `#dashboard-body`, non l'intero screen
    via `recompose()`: un `recompose()` pieno ricreerebbe anche l'`Header`, lasciando in sospeso
    il suo task interno di set-title contro l'istanza appena rimossa e rompendo la gestione del
    prossimo evento in Textual.

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
