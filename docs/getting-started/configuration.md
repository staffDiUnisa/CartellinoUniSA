# Configurazione

## `cartellino_v2.py`/TUI/GUI — keyring del SO + `config.toml`

A partire dalla v2.0.0, l'applicazione non usa più `.env`: la configurazione è salvata in un
file `config.toml` nella cartella di configurazione standard del sistema operativo (via
`platformdirs`), e le credenziali UniSA nel **keyring nativo del SO** (Keychain su macOS,
Credential Manager su Windows, Secret Service/kwallet su Linux).

**Se hai già un `.env` da una versione precedente**, non serve fare nulla: al primo avvio viene
eseguita una **migrazione automatica one-shot** che crea `config.toml`, salva le credenziali nel
keyring, e stampa un messaggio che conferma la migrazione (consiglia poi di eliminare il vecchio
`.env`).

**Per una configurazione da zero**, senza `.env`: la TUI e la GUI hanno una schermata di
Onboarding che guida la creazione, oppure si può fare programmaticamente:

```bash
uv run python -c "
from cartellino.user_config import UserConfig
from cartellino.credentials import set_credentials

UserConfig(current_year=2025, min_date_riposi_usati='01-01', headless=False).save()
set_credentials('mario.rossi@unisa.it', 'TuaPassword')
"
```

### Campi di `config.toml`

| Campo | Obbligatorio | Descrizione |
|-------|:---:|---------|
| `current_year` | ✅ | Anno di elaborazione |
| `min_date_riposi_usati` | ❌ | Data minima (`MM-DD`) per contare i riposi SRC già fruiti. Se mancante viene usato `riposi_usati.txt` |
| `headless` | ❌ | `true` per avviare Chrome in modalità headless (solo con Credenziali UNISA) |
| `export_format` | ❌ | Formato di export dei report on-demand (`xlsx`/`csv`, default `xlsx`) |
| `dashboard_exception_codes` | ❌ | Codici per la sezione "eccezioni" della dashboard, default `["ERIT", "SCN"]` |
| `dashboard_balance_codes` | ❌ | Codici per il saldo ore mensile della dashboard, default `["CRE", "OE-DIU", "SCN"]` — vedi [Codici del cartellino](../reference/codes.md) |
| `data_folder` | ❌ | Cartella radice dei dati (`{data_folder}/{anno}/input/output`). Default: `data/v2` (relativo alla cwd) per la CLI, `~/.cartellino_unisa/data/v2` (`%LOCALAPPDATA%\cartellino_unisa\data\v2` su Windows) per TUI/GUI |
| `output_folder` | ❌ | Cartella di output dei report, se diversa da `{data_folder}/{anno}/output` |

Username e password si impostano **solo** tramite `set_credentials` (keyring), non in
`config.toml`. Tutti gli altri campi sono modificabili dalla schermata **Impostazioni** di
TUI/GUI.

## `main.py` — versione legacy (`.env`)

Il percorso legacy (`main.py`/`process.py`) continua a usare `.env`:

```bash
cp env.template .env
```

```env
USERNAME=mario.rossi@unisa.it    # credenziali per login "Credenziali UNISA"
PASSWORD=TuaPassword
CURRENT_YEAR=2025                 # anno da elaborare
MIN_DATE_RIPOSI_USATI=01-01       # data (MM-DD) da cui considerare i riposi SRC nel cartellino
HEADLESS=False                    # True per browser invisibile (solo con Credenziali UNISA)
```

| Variabile | Obbligatoria | Descrizione |
|-----------|:---:|---------|
| `CURRENT_YEAR` | ✅ | Anno di elaborazione |
| `MIN_DATE_RIPOSI_USATI` | ✅ | Data minima (MM-DD) per contare i riposi SRC già fruiti. Se mancante viene usato `riposi_usati.txt` |
| `USERNAME` | Solo con Credenziali UNISA | Email UniSA |
| `PASSWORD` | Solo con Credenziali UNISA | Password account UniSA |
| `HEADLESS` | ❌ | `True` per avviare Chrome in modalità headless (solo con Credenziali UNISA) |

`.env` resta valido anche per il percorso `v2`: se non esiste ancora `config.toml`, viene usato
per la migrazione automatica one-shot descritta sopra (o come fallback puro se manca anche un
backend keyring disponibile, es. Linux headless senza Secret Service).

!!! warning "Sicurezza"
    Non condividere mai il file `.env` contenente le credenziali.
