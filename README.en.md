# 📊 UniSA Attendance Card Processing

![Release](https://img.shields.io/github/v/release/staffDiUnisa/CartellinoUniSA?include_prereleases&label=release&style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL_3.0-blue?style=for-the-badge&logo=gnu&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Textual](https://img.shields.io/badge/TUI-Textual-8A2BE2?style=for-the-badge)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

![macOS](https://img.shields.io/badge/macOS-pkg%20firmato%20%26%20notarizzato-success?style=flat-square&logo=apple&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-installer%20.exe-blue?style=flat-square&logo=windowsterminal&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-.deb%20%2F%20.rpm-blue?style=flat-square&logo=linux&logoColor=white)

> This is the English translation of the project's README, provided for reference (e.g. for
> third-party review purposes). The Italian version, [README.md](README.md), is the primary and
> authoritative document — please refer to it for the definitive information.

A Python tool for automatically downloading and processing UniSA employee attendance data
("cartellino presenze") from [presenze.unisa.it](https://presenze.unisa.it). It calculates
overtime hours, compensatory rest days, monthly hour credits, and generates timesheets for
research projects. Available as a desktop **GUI** (PySide6), an interactive **TUI** (text user
interface), and a scriptable **CLI** — all downloadable as standalone executables with no Python
installation required.

📚 **[Full documentation](https://cartellino-unisa.readthedocs.io/)** (Italian)

## 🎯 Features

- **Automatic download** of the attendance card from `presenze.unisa.it` via Selenium
- **Authentication** with UniSA credentials, SPID, or CIE (Italian digital identity systems)
- **Overtime hours** (OE-DIU): calculation with configurable date exclusions, including partial subtraction
- **Compensatory rest days**: automatic grouping (threshold: 7h 12m per rest day) and correlation with already-used rest days
- **Monthly hour credit** by processing status (OO-DIU)
- **Multi-sheet statistics**: meal tickets, specialist medical visits, overtime, sick leave, holidays, exam supervision, family-related leave, late arrivals
- **Daily hours** worked per month
- **Project timesheet**: configurable distribution of hours across selected months, with full days and fixed hours, output as monthly Excel files per project subfolder
- **Formal report**: automatic filling of the institutional Excel template (`TS_*.xlsx`) with personal data, hours per day, weekend colors updated to the correct year, and updated references in the summary sheet

## 📋 Prerequisites

- [`mise`](https://mise.jdx.dev/) (manages the Python version and installs `uv`)
- [`uv`](https://docs.astral.sh/uv/) (dependency and virtualenv management) — installed automatically by `mise`
- Google Chrome installed (ChromeDriver managed automatically)
- University network connection **only** for the "UniSA Credentials" method (SPID and CIE also work from outside the network)
- A valid UniSA account

## 🚀 Installation

```bash
git clone https://github.com/staffDiUnisa/CartellinoUniSA.git
cd CartellinoUniSA

mise install       # installs Python 3.12 and uv (versions pinned in .mise.toml)
mise run install   # equivalent to: uv sync (installs dependencies from pyproject.toml/uv.lock)
```

## ⚙️ Configuration

### `cartellino_v2.py` — OS keyring credentials + `config.toml`

Starting with v2.0.0, `cartellino_v2.py` no longer uses `.env`: configuration is stored in a
`config.toml` file in the operating system's standard configuration folder (via `platformdirs`),
and UniSA credentials are stored in the **native OS keyring** (Keychain on macOS, Credential
Manager on Windows, Secret Service/kwallet on Linux).

**If you already have a `.env` from a previous version**, no action is needed: on the first run
of `cartellino_v2.py` (or `get.py`), an **automatic one-shot migration** is performed that
creates `config.toml`, saves the credentials in the keyring, and prints a message confirming the
migration and recommending you delete the old `.env`.

**For a fresh setup**, without `.env`, you can create `config.toml` and the credentials
programmatically:

```bash
uv run python -c "
from cartellino.user_config import UserConfig
from cartellino.credentials import set_credentials

UserConfig(current_year=2025, min_date_riposi_usati='01-01', headless=False).save()
set_credentials('mario.rossi@unisa.it', 'YourPassword')
"
```

(alternatively, the TUI — see below — has an Onboarding screen that performs this step
interactively, with no need to run code by hand)

`config.toml` fields:

| Field | Required | Description |
|-------|:---:|---------|
| `current_year` | ✅ | Year to process |
| `min_date_riposi_usati` | ❌ | Minimum date (`MM-DD`) for counting already-used SRC rest days. If missing, `riposi_usati.txt` is used |
| `headless` | ❌ | `true` to launch Chrome in headless mode (only with UniSA Credentials) |
| `export_format` | ❌ | Export format for on-demand reports in the TUI (`xlsx`/`csv`, default `xlsx`) |
| `dashboard_exception_codes` | ❌ | Codes for the "exceptions" section of the TUI dashboard, default `["ERIT", "SCN"]` |
| `dashboard_balance_codes` | ❌ | Codes for the monthly hour balance in the TUI dashboard, default `["CRE", "OE-DIU", "SCN"]` |
| `data_folder` | ❌ | Root data folder (`{data_folder}/{year}/input/output`), where `cartellino.feather` is saved. If missing, the entrypoint default is used: `data/v2` (relative to the cwd) for `cartellino_v2.py`, `~/.cartellino_unisa/data/v2` (`%LOCALAPPDATA%\cartellino_unisa\data\v2` on Windows) for `cartellino_tui.py` |
| `output_folder` | ❌ | Reports output folder, if different from `{data_folder}/{year}/output` |

Username and password are set **only** via `set_credentials` (keyring), never in `config.toml`.

All these fields (except username/password) can be edited from the TUI's **Settings** screen,
including `data_folder`/`output_folder` via a folder picker. If `data_folder` is pointed to a
folder that doesn't yet have a `cartellino.feather`, the TUI treats it as a "first run" for that
folder: it creates it and goes straight to the update screen.

### `main.py` — legacy version (`.env`)

The legacy path (`main.py`/`process.py`) still uses `.env`:

```bash
cp env.template .env
```

Edit `.env`:

```env
USERNAME=mario.rossi@unisa.it    # credentials for "UniSA Credentials" login
PASSWORD=YourPassword
CURRENT_YEAR=2025                 # year to process
MIN_DATE_RIPOSI_USATI=01-01       # date (MM-DD) from which to count SRC rest days in the card
HEADLESS=False                    # True for an invisible browser (only with UniSA Credentials)
```

| Variable | Required | Description |
|-----------|:---:|---------|
| `CURRENT_YEAR` | ✅ | Year to process |
| `MIN_DATE_RIPOSI_USATI` | ✅ | Minimum date (MM-DD) for counting already-used SRC rest days. If missing, `riposi_usati.txt` is used |
| `USERNAME` | Only with UniSA Credentials | UniSA email |
| `PASSWORD` | Only with UniSA Credentials | UniSA account password |
| `HEADLESS` | ❌ | `True` to launch Chrome in headless mode (only with UniSA Credentials) |

> `.env` remains valid for `cartellino_v2.py` too: if `config.toml` doesn't exist yet, it is used
> for the automatic one-shot migration described above (or as a pure fallback if no keyring
> backend is available either, e.g. headless Linux without Secret Service).

## 💻 Usage

### `cartellino_tui.py` — text user interface (TUI, recommended)

An interactive interface built on [Textual](https://textual.textualize.io/), with a dashboard,
guided configuration/credentials management, and on-demand reports. Data and logs are saved in a
fixed folder in the user's home directory — **not** relative to the folder the executable is
launched from (important for the standalone binary, which can be launched from anywhere: Desktop,
Downloads, etc.): `~/.cartellino_unisa/` on macOS/Linux, `%LOCALAPPDATA%\cartellino_unisa\` on
Windows. Inside: `data/v2/{year}/` (same structure as `cartellino_v2.py`, see below) and
`cartellino_tui.log`.

```bash
mise run tui
# or
uv run python cartellino_tui.py
```

Available screens:

| Screen | Shortcut | Description |
|-----------|:---:|---------|
| **Onboarding** | — | Shown automatically if `config.toml` is missing; sets the year, minimum rest date, credentials (optional here) |
| **Dashboard** | — | Home: this month's exceptions, hour balance, compensatory rest summary, used holidays/family leave, tickets to be received, last update date |
| **Update** | `r` | Choice of authentication method (UniSA Credentials/SPID/CIE, UniSA disabled outside the network) and download with real-time log |
| **Reports** | `p` | On-demand generation of compensatory rest, hour credit, statistics, daily hours, in the format chosen in Settings |
| **Project timesheet** | `t` | Selection and execution of an existing YAML file in `timesheet/` (see dedicated section below) |
| **Statistics** | `v` | On-screen display (no export) of `statistiche.xlsx` categories: meal tickets, holidays, family-related leave, late arrivals, overtime, specialist visits, sick leave — one button per category, different colors, disabled if the category has no data |
| **Settings** | `s` | Year, minimum rest date, export format, dashboard codes, data/output folder (with a picker), meal ticket start date, excluded dates management (`date_escluse.txt`); UniSA credentials editable in a dedicated screen ("Edit credentials") |

`Esc` returns to the previous screen, `q` quits the app.

### `cartellino_gui.py` — graphical interface (GUI)

A desktop interface built on [PySide6](https://doc.qt.io/qtforpython-6/), designed for those who
prefer not to use a terminal: same features as the TUI, no Python/uv required if using the
standalone executable (see below). Shares data, `config.toml`, and credentials with the TUI —
they are two frontends on the same domain layer, not two separate products: the same fixed data
folder in the user's home directory (`~/.cartellino_unisa/` on macOS/Linux,
`%LOCALAPPDATA%\cartellino_unisa\` on Windows) and the same `data/v2/{year}/`.

```bash
mise run gui
# or
uv run python cartellino_gui.py
```

Available screens (same as the TUI, navigation via buttons instead of keyboard shortcuts):

| Screen | Description |
|-----------|---------|
| **Onboarding** | Shown automatically if `config.toml` is missing; sets the year, minimum rest date, credentials (optional here) |
| **Dashboard** | Home: this month's exceptions, hour balance, compensatory rest summary, used holidays/family leave, tickets to be received, last update date |
| **Update** | Choice of authentication method (UniSA Credentials/SPID/CIE, UniSA disabled outside the network) and download with real-time log |
| **Reports** | On-demand generation of compensatory rest, hour credit, statistics, daily hours, in the format chosen in Settings |
| **Project timesheet** | Selection (or "Browse...") and execution of an existing YAML file in `timesheet/` (see dedicated section below) |
| **Statistics** | On-screen display (no export) of `statistiche.xlsx` categories: meal tickets, holidays, family-related leave, late arrivals, overtime, specialist visits, sick leave — one button per category, disabled if the category has no data |
| **Settings** | Year, minimum rest date, export format, dashboard codes, data/output folder (with a native OS picker), meal ticket start date, excluded dates management (`date_escluse.txt`); UniSA credentials editable in a dedicated window ("Edit credentials") |

Missing compared to the TUI: the "Terminal (macOS only)" field in Settings (not applicable, the
GUI is already a native window, no terminal to choose at startup).

### `cartellino_v2.py` — non-interactive CLI

Data saved in `data/v2/{year}/`.

```bash
mise run app
# or
uv run python cartellino_v2.py
```

At startup you're asked whether to download the updated attendance card. If you choose to
download, you're then asked for the authentication method:

```
Choose the authentication method:
  1. UniSA Credentials   ← available only on the university network
  2. SPID
  3. CIE
```

For SPID and CIE, the browser opens and waits for the user to manually complete the login
(10-minute timeout).

**Available options** (for non-interactive/scripted use, no prompts if specified):

```bash
# Skip the download and use the data already present
uv run python cartellino_v2.py --no-aggiorna-cartellino

# Update, choosing the authentication method without an interactive prompt
uv run python cartellino_v2.py --aggiorna-cartellino --auth-method spid

# Generate reports in CSV instead of xlsx (default: the one configured in config.toml/TUI Settings)
uv run python cartellino_v2.py --no-aggiorna-cartellino --export-format csv

# Generate only some reports (default: all)
uv run python cartellino_v2.py --no-aggiorna-cartellino --solo-report statistiche,credito

# Also generate the project timesheet (see dedicated section)
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml
```

| Option | Values | Description |
|---------|--------|-------------|
| `--aggiorna-cartellino`/`--no-aggiorna-cartellino` | flag | Download updated data or use only what's already present; if omitted, you're prompted on screen |
| `--auth-method` | `unisa`, `spid`, `cie` | Authentication method for the download; if omitted and the download is enabled, you're prompted on screen |
| `--export-format` | `xlsx`, `csv` | Format of the generated reports; if omitted, uses the configured one (default `xlsx`) |
| `--solo-report` | `cartellino`, `riposo`, `credito`, `statistiche`, `ore-giornaliere` (comma-separated) | Generates only the specified reports; if omitted, generates all of them |
| `--timesheet-progetto` | YAML file name | Also generates the project timesheet (see dedicated section) |

### `main.py` — legacy version

Data saved in `data/{year}/`. Same download logic, but the previous processing pipeline (without
statistics and daily hours).

```bash
uv run python main.py
uv run python main.py --no-aggiorna-cartellino
```

## 📁 Data structure (current version)

```
CartellinoUniSA/
├── templates/
│   └── timesheet_progetto_template.yaml  ← template for the project timesheet
├── timesheet/                            ← personal YAML files (git-ignored)
│   └── mio_progetto.yaml                 ← copy and adapt from the template
└── data/v2/
    └── {year}/
        ├── input/
        │   ├── cartellino.feather     ← downloaded by get.py (primary format, Feather/pyarrow)
        │   ├── cartellino.xlsx        ← legacy only: if present and the .feather is missing,
        │   │                            it is migrated automatically once on first run
        │   ├── date_escluse.txt       ← dates to exclude/reduce from the OE calculation
        │   ├── riposi_usati.txt       ← fallback for already-used rest days (if no MIN_DATE)
        │   └── data_ticket.txt        ← date from which tickets started being paid
        └── output/
            ├── cartellino.xlsx               ← attendance card with added Codice column
            ├── riposo_compensativo.xlsx      ← overtime hours detail and summary
            ├── riposi_compensativi.txt       ← textual rest days summary
            ├── credito_ore.xlsx              ← monthly hour credit
            ├── statistiche.xlsx              ← multiple sheets (tickets, holidays, sick leave, ...)
            ├── ore_giornaliere.xlsx          ← OO-DIU hours per day, per month
            └── ore_svolte_per_giorno/
                └── {project_name}/           ← generated by the project timesheet
                    ├── 01_gennaio.xlsx
                    ├── 02_febbraio.xlsx
                    └── ...
```

> This structure is relative to the repository folder when using `cartellino_v2.py` (CLI/dev).
> For the standalone executable (`cartellino_tui.py`), the same structure (`data/v2/` onward)
> lives inside `~/.cartellino_unisa/` (`%LOCALAPPDATA%\cartellino_unisa\` on Windows), not in the
> folder the binary is launched from.

## 📝 Input files

### `date_escluse.txt`

Dates to exclude from the overtime hours calculation. Two supported formats:

```
# Full-day exclusion (DD-MM-YYYY)
16-01-2025
17-01-2025

# Partial subtraction: subtracts HH:MM from that day's overtime hours
20-01-2025 03:30
```

### `riposi_usati.txt` *(optional)*

Used only if `MIN_DATE_RIPOSI_USATI` is not set in `.env`. List of dates on which compensatory
rest days were used:

```
2025-06-26
2025-06-27
2025-07-15
```

### `data_ticket.txt`

Date from which the meal ticket is paid by the institution (format `DD-MM-YYYY`). Used to
distinguish tickets already received from those still to be received:

```
01-01-2025
```

## 📊 Generated output

### `riposo_compensativo.xlsx`
Two sheets:
- **dettaglio** (detail): daily overtime hours with status, date, base entry, and interval (hh:mm)
- **riassunto** (summary): total overtime hours/minutes grouped by processing status

### `riposi_compensativi.txt`
Textual summary of accrued compensatory rest days, indicating the dates used and the hours still
missing to complete each one:

```
_________________________________________________
Compensatory rest 1: - used on 26-06-2025
_________________________________________________
    - 01-01-2025 -> 02:30 [OK]
    - 02-01-2025 -> 01:45 [OK]
    ...
_________________________________________________
Compensatory rest 2: - hours needed to complete: 5:42
_________________________________________________
    - 06-01-2025 -> 01:30 [OK]
_________________________________________________
```

### `credito_ore.xlsx`
Monthly hour credit by processing status, gross and net of accrued rest days.

### `statistiche.xlsx`
Multi-sheet file with:
| Sheet | Content |
|--------|-----------|
| `ticket` | Days with a meal ticket, accrued and to-be-received value |
| `statistica_ticket` | Ticket count per month and status |
| `visite_specialistiche` | Days with a specialist medical visit (VSG) |
| `straordinari` | Days with overtime (STRSOS, FSTLAV, OS-FSD) |
| `malattia` | Sick leave/hospitalization days (MAL, RIC) |
| `ferie` | Holiday/vacation days (FER, FEV, FST) |
| `vigilanza_concorsi` | Exam supervision days (VIG) |
| `permessi_gravi_motivi` | Family-related leave (PMF) |
| `entrata_ritardo` | Days with a late arrival (ERIT) |

### `ore_giornaliere.xlsx`
OO-DIU hours (ordinary hours) for each working day, organized by month in separate sheets.

## 📐 Project timesheet and report

Generates monthly project reporting sheets from the processed attendance card. Produces two
types of output in the `data/v2/{year}/output/ore_svolte_per_giorno/{project_name}/` folder:

| File | Description |
|------|-------------|
| `{MM}_{month}.xlsx` | Simplified monthly sheets (one per month) |
| `TS_{name}_{year}_{LastName}_{FirstName}.xlsx` | Formal report filled from the institutional template |

The formal report is optional: it is generated only if `template_rendiconto` is specified in the
YAML configuration.

### 1. YAML configuration

Copy the template into the `timesheet/` folder and adapt it:

```bash
cp templates/timesheet_progetto_template.yaml timesheet/mio_progetto.yaml
```

Files in the `timesheet/` folder are git-ignored (personal data). The template in `templates/`
is version-controlled instead.

Complete structure of the YAML file:

```yaml
progetto:
  nome: "PROJECT_NAME"            # name of the output subfolder
  cup: "D43C22005040001"          # project CUP (unique project code)
  codice: "PNC-E3-2022-23683267"  # project identification code
  anno: 2025                      # year to process (must match CURRENT_YEAR)

  # (optional) Institutional Excel template for the formal report.
  # If present, also generates TS_{name}_{year}_{LastName}_{FirstName}.xlsx
  template_rendiconto: "templates/TS_DHEAL_COM_2025_Nome_Cognome.xlsx"

  # (optional) Employee personal data for the report
  persona:
    figura_professionale: "Personale Tecnico Amministrativo (PTA)"
    nome: "Mario"
    cognome: "Rossi"
    codice_fiscale: "RSSMRA80A01F839X"

mesi:                        # months to include (1-12)
  - 1
  - 2
  - 3

ore_totali: 100.0            # total hours to distribute

# (optional) Day ranges in which ALL worked hours go to the project
giorni_interi:
  - da: "2025-01-15"
    a:  "2025-01-17"         # Jan 15, 16, 17: project_hours = worked_hours
  - da: "2025-03-10"
    a:  "2025-03-10"         # single day

# (optional) Fixed hours on individual days
ore_fisse:
  - data: "2025-05-05"
    ore: 3.0                 # exactly 3 hours on May 5th
  - data: "2025-06-20"
    ore: 2.5
```

### 2. Execution

```bash
# Pass just the file name: it will be looked up automatically in timesheet/
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml

# Or pass a full or relative path
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto /absolute/path/config.yaml
```

### 3. Hour distribution rules

1. The hours from `giorni_interi` (= hours actually worked that day) and `ore_fisse` are summed
   and subtracted from `ore_totali` to obtain the **remaining hours**.
2. The remaining hours are spread evenly across days with **at least 5 worked hours** that are
   not already covered by the previous points, rounded down to the nearest **half hour**.
3. Any remainder is added to the last eligible day so the total exactly equals `ore_totali`.

### 4. Output: simplified monthly sheets

Each `{MM}_{month}.xlsx` file has the format:

| | 01 | 02 | 03 | ... |
|---|---|---|---|---|
| **Day** | 01 | 02 | 03 | ... |
| **Activity performed on project CUP: …** | 2.0 | 2.0 | 0 | ... |
| **Activities performed on other projects** | 0 | 0 | 0 | ... |
| **Ordinary activity** | 6.15 | 7.0 | 0 | ... |
| **Other (Sick leave, Holidays..)** | 0 | 0 | 0 | ... |

### 5. Output: formal report (optional)

If `template_rendiconto` is set, `TS_{name}_{year}_{LastName}_{FirstName}.xlsx` is generated from
the institutional `.xlsx` template. The file is adapted to the reference year and filled in
automatically:

| Cell | Content |
|-------|-----------|
| N12 | Month name in uppercase (e.g. `FEBBRAIO`) |
| AG12 | Year |
| C15 | Project CUP |
| C16 | Project code |
| C18 | Professional role |
| C19 | First name |
| Y19 | Last name |
| C20 | Tax code |
| Y20 | Total hours reported for the month |
| C22 | `Mese di Febbraio 2026` |
| Rows 24–27 | Project/ordinary hours for each day of the month |

The following are also corrected automatically:
- **Weekend colors**: Saturdays and Sundays colored with the template's gray, Monday–Friday
  uncolored, based on the actual calendar of that year (not the original template's)
- **Summary sheet**: formula references to the monthly sheets are updated with the new names —
  the layout and logic of the summary sheet are not modified

## 📦 Standalone executables (no Python required)

Starting with v2.0.0, every `v2.*` tag automatically generates (GitHub Actions,
`.github/workflows/release.yml`) standalone executables for macOS, Windows, and Linux, attached
to the corresponding [GitHub Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest).
Starting with the desktop GUI (see `TODO_gui.md`), each package includes **two executables**:
the TUI (`cartellino-unisa`, text interface) and the GUI (`cartellino-unisa-gui`, graphical
interface), the same combined distribution. No need to install Python, `mise`, or `uv`: download
the zip for your operating system, extract it, and run your preferred binary from inside the
extracted folder — **do not move the executable out of its folder**: the supporting libraries
(Python, Textual, PySide6, pandas/pyarrow, etc.) sit right next to it and are needed for it to
work.

**Chrome remains a mandatory external dependency** (downloading the attendance card uses
Selenium, which cannot be bundled into a standalone executable): it must be installed separately,
regardless of the operating system.

### 🍎 macOS

**Recommended option — `.pkg` installer:**

1. From the [Releases](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest) page,
   download `cartellino-unisa.pkg`
2. Double-click, follow the wizard (installs into `/usr/local/cartellino-unisa`, creates the
   `cartellino-unisa`/`cartellino-unisa-gui` commands in the `PATH`, and adds two entries to
   `/Applications`: **Cartellino UniSA** and **Cartellino UniSA (Terminale)**)
3. **Graphical interface (recommended for those who don't want to use the Terminal)**: open
   **Launchpad** or **Applications** and double-click **Cartellino UniSA** — the app window
   opens directly, without going through the Terminal.
4. **Text interface (TUI)**, for those who prefer to stay on the command line: open **Launchpad**
   or **Applications** and double-click **Cartellino UniSA (Terminale)** — a terminal will open
   automatically with the TUI already started, maximized, and it will close itself when you
   exit.

   On first launch you'll be asked which terminal to use among the ones installed (native
   **Terminal**, **Ghostty**, **iTerm2** — Warp cannot be chosen: it has no automation support at
   all, so it can't be used by this launcher). The choice is remembered permanently and you can
   change it later from **Settings → Terminal (macOS only)**.

   > On first launch, macOS may ask for permission to control the chosen terminal (**System
   > Settings → Privacy & Security → Automation**): this is a standard request for any app that
   > drives another one via AppleScript, needed only the first time — grant it to continue.

   Alternatively, open the Terminal directly and run:
   ```bash
   cartellino-unisa
   ```

The `.pkg` (and both the **Cartellino UniSA**/**Cartellino UniSA (Terminale)** launchers it
contains) are **signed with a Developer ID certificate and notarized/stapled by Apple**:
Gatekeeper should not show any warning, even offline.

> **If the `cartellino-unisa` command is not found** (`command not found`): `/usr/local/bin` is
> in the default `PATH` on macOS, but if your shell profile explicitly overwrites it (instead of
> extending it), it might not be included. Add this line to your shell's configuration file, then
> open a new Terminal (or `source` the file):
> ```bash
> export PATH="/usr/local/bin:$PATH"
> ```
> - **zsh** (default shell since macOS Catalina): `~/.zshrc`
> - **bash** (if still in use, e.g. on older macOS versions or custom configurations):
>   `~/.bashrc` or `~/.bash_profile`
>
> To find out which shell you're using: `echo $SHELL`.

**Alternative option — onedir folder zip** (for those who prefer not to install anything at the
system level):

1. Download `cartellino-unisa-macos.zip`, extract it (double-click, or
   `unzip cartellino-unisa-macos.zip` from a terminal)
2. Open the Terminal, go into the extracted folder, and run the TUI:
   ```bash
   cd cartellino-unisa
   ./cartellino-unisa
   ```
   or the GUI (also with a double-click from Finder, being a windowed app):
   ```bash
   ./cartellino-unisa-gui
   ```

The executable inside the zip is also signed and notarized: if "unverified app"/"unidentified
developer" still appears (e.g. for a build without the signing secrets configured), fix it with:
right-click (or `Ctrl`+click) on the `cartellino-unisa` file → **Open**, then confirm in the
dialog (needed only the first time).

### 🪟 Windows

**Recommended option — `cartellino-unisa-setup.exe` installer:**

1. From the [Releases](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest) page,
   download `cartellino-unisa-setup.exe`
2. Double-click, follow the wizard (installs into Program Files, creates two Start Menu entries:
   **Cartellino UniSA** and **Cartellino UniSA (Terminale)**, plus an optional Desktop icon for
   the first one)
3. Launch **Cartellino UniSA** from the Start Menu (or Desktop) for the graphical interface, or
   **Cartellino UniSA (Terminale)** for the TUI (opens a terminal window, being a text-based app)

**Alternative option — onedir folder zip:**

1. Download `cartellino-unisa-windows.zip`, extract it (right-click → **Extract All...**)
2. Open PowerShell or Command Prompt, go into the extracted folder, and run the TUI:
   ```powershell
   cd cartellino-unisa
   .\cartellino-unisa.exe
   ```
   or double-click `cartellino-unisa-gui.exe` for the GUI

In both cases the binary **is not signed** (no code-signing certificate for Windows, see
`ignored/signed_windows.md` for the options evaluated), so on first launch SmartScreen shows
"Windows protected your PC": click **More info** → **Run anyway** (needed only the first time).

### 🐧 Linux

**Recommended option — `.deb`/`.rpm` package:**

1. From the [Releases](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest) page,
   download `cartellino-unisa_<version>_amd64.deb` (Debian/Ubuntu) or
   `cartellino-unisa-<version>.x86_64.rpm` (Fedora/RHEL/openSUSE)
2. Install:
   ```bash
   sudo dpkg -i cartellino-unisa_<version>_amd64.deb      # Debian/Ubuntu
   # or
   sudo rpm -i cartellino-unisa-<version>.x86_64.rpm      # Fedora/RHEL/openSUSE
   ```
3. Run the TUI from a terminal: `cartellino-unisa`, or the GUI: `cartellino-unisa-gui`
   (no application menu icon/entry yet, see `TODO_gui.md`)

**Alternative option — onedir folder zip:**

1. Download `cartellino-unisa-linux.zip`, extract it and run from a terminal:
   ```bash
   unzip cartellino-unisa-linux.zip
   cd cartellino-unisa
   ./cartellino-unisa
   ```
   If the system reports missing permissions (`Permission denied`): `chmod +x cartellino-unisa`.

In both cases, Chrome/Chromium must be installed and reachable from the `PATH` for downloading
the attendance card (Selenium/`webdriver-manager` will use it automatically). The `.deb`/`.rpm`
is built on Ubuntu (recent glibc): on very old distributions, library incompatibilities may
occur, the same implicit limitation already present for the zip.

### Common notes

> Why a folder (zip) and not a single executable: the first version used a "onefile" executable,
> which turned out to be broken on macOS (`pyarrow` failed to import on the binary downloaded
> from a browser, while working fine on a local build) — native libraries extracted at runtime
> into an unsigned temporary folder are blocked by macOS. The "onedir" (folder) mode avoids this
> runtime extraction.

To rebuild the executable locally (e.g. to verify a change before tagging a release):
```bash
uv sync --group build
uv run pyinstaller packaging/cartellino.spec
./dist/cartellino-unisa/cartellino-unisa   # .exe on Windows
```

## 🔧 Troubleshooting

**Chrome doesn't start / ChromeDriver not found**
- Make sure Google Chrome is installed
- The driver is downloaded automatically by `webdriver_manager`; check your internet connection on first run

**Timeout during SPID or CIE login**
- The browser stays open for 10 minutes waiting for login completion; complete authentication within that time

**"UniSA Credentials" not available**
- This option only appears when connected to the university network (VPN included)

**Dates not recognized in `date_escluse.txt`**
- Check the format: `DD-MM-YYYY` or `DD-MM-YYYY HH:MM`

**`MIN_DATE_RIPOSI_USATI` not recognized**
- The format is `MM-DD` (month-day), e.g. `06-01` for June 1st
- On error, the script will automatically use `riposi_usati.txt`

**Timesheet total doesn't match**
- If the hours from `giorni_interi` and `ore_fisse` exceed `ore_totali`, a warning is printed and the remaining hours are set to zero
- If the remainder to add to the last day is ≥ 30 min, a warning is printed (the total is still correct)

**The report isn't generated**
- Check that `template_rendiconto` is present in the YAML and that the `.xlsx` file exists at the given path
- The template must be an `.xlsx` file (not `.xlsm`) with the monthly sheets renamed in the format `{Month} {year}` (e.g. `Gennaio 2025`)

**`#REF!` errors in the summary sheet**
- This doesn't happen with files generated by the script, which automatically updates formula references
- It can happen if the monthly sheets are renamed manually without updating the summary sheet

## 🤝 Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/new-feature`
3. Commit: `git commit -m 'Add new feature'`
4. Push: `git push origin feature/new-feature`
5. Open a Pull Request

## 👤 Author

Open source project developed by **Andrea Bruno** — [bruand81.it](https://bruand81.it).

## 📄 License

Distributed under the GPL 3.0 license. See [LICENSE](LICENSE) for details. The source code is
publicly available on GitHub, in line with the open source nature of the project.

## ⚠️ Disclaimer

This software is provided "as is", without warranties of any kind. The authors are not
responsible for any errors in calculations or data interpretation. Always verify the results
against official data.

---

> **Security**: never share the `.env` file containing your credentials.
