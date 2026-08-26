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
cp env.template .env  # then edit with credentials
```

Per eseguire lo script principale:

```bash
mise run app        # equivalente a: uv run python cartellino_v2.py
# oppure direttamente:
uv run python cartellino_v2.py
```

Required `.env` variables:
- `USERNAME` / `PASSWORD` — UniSA credentials
- `CURRENT_YEAR` — year to process (e.g. `2025`)
- `MIN_DATE_RIPOSI_USATI` — cutoff date in `MM-DD` format for counting used compensatory rests

## Running

```bash
uv run python main.py           # prompts whether to download fresh data
uv run python main.py --no-aggiorna-cartellino  # skip download, process existing data
```

Download requires UniSA network access and Chrome Beta at `/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta`. Set `HEADLESS=True` in `.env` for headless mode.

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
