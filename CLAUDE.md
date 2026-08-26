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

Per eseguire lo script principale (CLI non interattiva):

```bash
mise run app        # equivalente a: uv run python cartellino_v2.py
# oppure direttamente:
uv run python cartellino_v2.py
```

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
  - `app.py` — `CartellinoApp`, instrada verso `OnboardingScreen` o `DashboardScreen` in base
    alla presenza di `config.toml` (`Config.load()`); versione mostrata in header letta da
    `pyproject.toml` via `tomllib` (il progetto ha `tool.uv.package = false`, quindi non è
    installato come pacchetto e `importlib.metadata.version()` non funzionerebbe).
  - `logging_handler.py` — `RichLogHandler`, inoltra i record di `logging` a un widget
    `RichLog` in modo thread-safe (`App.call_from_thread`), usato dalla schermata di
    aggiornamento durante il download Selenium (lanciato con `@work(thread=True)`).
  - `screens/onboarding.py`, `dashboard.py`, `update.py`, `settings.py`, `reports.py`,
    `timesheet.py` — una schermata per ciascuna voce del TODO Fase 4; costruite sul layer di
    dominio esistente (`Cartellino`, `OreEccedenti`, `CreditoOre`, `Statistiche`,
    `OreGiornaliere`, `TimesheetProgetto`) senza modificarne la logica di calcolo.
  - Nota implementativa: `DashboardScreen.on_screen_resume` ricostruisce solo il container
    `#dashboard-body` (non l'intero screen via `recompose()`) — un `recompose()` pieno
    ricreerebbe anche l'`Header`, lasciando in sospeso il suo task interno di set-title contro
    l'istanza appena rimossa e rompendo la gestione del prossimo evento in Textual.

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
