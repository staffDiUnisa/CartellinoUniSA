# 📊 Elaborazione Cartellino UniSA

![Release](https://img.shields.io/github/v/release/staffDiUnisa/CartellinoUniSA?include_prereleases&label=release&style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL_3.0-blue?style=for-the-badge&logo=gnu&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Textual](https://img.shields.io/badge/TUI-Textual-8A2BE2?style=for-the-badge)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

![macOS](https://img.shields.io/badge/macOS-firmato%20%26%20notarizzato-success?style=flat-square&logo=apple&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-supportato-blue?style=flat-square&logo=windowsterminal&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-supportato-blue?style=flat-square&logo=linux&logoColor=white)

Strumento Python per il download automatico e l'elaborazione del cartellino presenze da [presenze.unisa.it](https://presenze.unisa.it). Calcola ore eccedenti, riposi compensativi, credito ore mensile e genera timesheet per progetti di ricerca. Disponibile sia come **TUI** (interfaccia testuale interattiva) sia come **CLI** scriptabile, entrambe scaricabili come eseguibile standalone senza installare Python.

## 🎯 Funzionalità

- **Download automatico** del cartellino da `presenze.unisa.it` tramite Selenium
- **Autenticazione** con Credenziali UNISA, SPID o CIE
- **Ore eccedenti** (OE-DIU): calcolo con esclusione date configurabili, anche con sottrazione parziale
- **Riposi compensativi**: raggruppamento automatico (soglia: 7h 12m per riposo) e correlazione con i riposi già fruiti
- **Credito ore** mensile per stato di elaborazione (OO-DIU)
- **Statistiche** multi-foglio: ticket mensa, visite specialistiche, straordinari, malattia, ferie, vigilanza concorsi, permessi gravi motivi, entrata in ritardo
- **Ore giornaliere** lavorate per mese
- **Timesheet di progetto**: distribuzione configurabile delle ore su mesi selezionati, con giorni interi e ore fisse, output in Excel mensile per subfolder di progetto
- **Rendiconto formale**: compilazione automatica del template Excel istituzionale (`TS_*.xlsx`) con dati anagrafici, ore per giorno, colori weekend aggiornati all'anno corretto e aggiornamento dei riferimenti nel foglio Riassuntivo

## 📋 Prerequisiti

- [`mise`](https://mise.jdx.dev/) (gestisce la versione di Python e installa `uv`)
- [`uv`](https://docs.astral.sh/uv/) (gestione dipendenze e virtualenv) — installato automaticamente da `mise`
- Google Chrome installato (ChromeDriver gestito automaticamente)
- Connessione alla rete universitaria **solo** per il metodo "Credenziali UNISA" (SPID e CIE funzionano anche da fuori rete)
- Account UniSA valido

## 🚀 Installazione

```bash
git clone https://github.com/staffDiUnisa/CartellinoUniSA.git
cd CartellinoUniSA

mise install       # installa Python 3.12 e uv (versioni pinnate in .mise.toml)
mise run install   # equivalente a: uv sync (installa le dipendenze da pyproject.toml/uv.lock)
```

## ⚙️ Configurazione

### `cartellino_v2.py` — credenziali nel keyring del SO + `config.toml`

A partire dalla v2.0.0, `cartellino_v2.py` non usa più `.env`: la configurazione è salvata in un
file `config.toml` nella cartella di configurazione standard del sistema operativo (via
`platformdirs`), e le credenziali UniSA nel **keyring nativo del SO** (Keychain su macOS,
Credential Manager su Windows, Secret Service/kwallet su Linux).

**Se hai già un `.env` da una versione precedente**, non serve fare nulla: al primo avvio di
`cartellino_v2.py` (o `get.py`) viene eseguita una **migrazione automatica one-shot** che crea
`config.toml`, salva le credenziali nel keyring, e stampa un messaggio che conferma la migrazione
e consiglia di eliminare il vecchio `.env`.

**Per una configurazione da zero**, senza `.env`, puoi creare `config.toml` e le credenziali
programmaticamente:

```bash
uv run python -c "
from cartellino.user_config import UserConfig
from cartellino.credentials import set_credentials

UserConfig(current_year=2025, min_date_riposi_usati='01-01', headless=False).save()
set_credentials('mario.rossi@unisa.it', 'TuaPassword')
"
```

(in alternativa, la TUI — vedi sotto — ha una schermata di Onboarding che fa questo passo in modo
interattivo, senza bisogno di eseguire codice a mano)

Campi di `config.toml`:

| Campo | Obbligatorio | Descrizione |
|-------|:---:|---------|
| `current_year` | ✅ | Anno di elaborazione |
| `min_date_riposi_usati` | ❌ | Data minima (`MM-DD`) per contare i riposi SRC già fruiti. Se mancante viene usato `riposi_usati.txt` |
| `headless` | ❌ | `true` per avviare Chrome in modalità headless (solo con Credenziali UNISA) |
| `export_format` | ❌ | Formato di export dei report on-demand nella TUI (`xlsx`/`csv`, default `xlsx`) |
| `dashboard_exception_codes` | ❌ | Codici per la sezione "eccezioni" della dashboard TUI, default `["ERIT", "SCN"]` |
| `dashboard_balance_codes` | ❌ | Codici per il saldo ore mensile della dashboard TUI, default `["CRE", "OE-DIU", "SCN"]` |
| `data_folder` | ❌ | Cartella radice dei dati (`{data_folder}/{anno}/input/output`), dove viene salvato `cartellino.feather`. Se mancante viene usato il default dell'entrypoint: `data/v2` (relativo alla cwd) per `cartellino_v2.py`, `~/.cartellino_unisa/data/v2` (`%LOCALAPPDATA%\cartellino_unisa\data\v2` su Windows) per `cartellino_tui.py` |
| `output_folder` | ❌ | Cartella di output dei report, se diversa da `{data_folder}/{anno}/output` |

Username e password si impostano **solo** tramite `set_credentials` (keyring), non in `config.toml`.

Tutti questi campi (tranne username/password) sono modificabili dalla schermata **Impostazioni** della TUI, comprese `data_folder`/`output_folder` tramite un selettore di cartelle. Se si punta `data_folder` a una cartella senza ancora un `cartellino.feather`, la TUI la tratta come "primo avvio" per quella cartella: la crea e passa direttamente alla schermata di aggiornamento.

### `main.py` — versione legacy (`.env`)

Il percorso legacy (`main.py`/`process.py`) continua a usare `.env`:

```bash
cp env.template .env
```

Modifica `.env`:

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

> `.env` resta valido anche per `cartellino_v2.py`: se non esiste ancora `config.toml`, viene
> usato per la migrazione automatica one-shot descritta sopra (o come fallback puro se manca
> anche un backend keyring disponibile, es. Linux headless senza Secret Service).

## 💻 Utilizzo

### `cartellino_tui.py` — interfaccia testuale (TUI, consigliata)

Interfaccia interattiva basata su [Textual](https://textual.textualize.io/), con dashboard,
gestione guidata di config/credenziali e report on-demand. Dati e log salvati in una cartella
fissa nella home dell'utente — **non** relativa alla cartella da cui si lancia l'eseguibile
(importante per il binario standalone, lanciabile da qualunque posizione: Desktop, Downloads,
ecc.): `~/.cartellino_unisa/` su macOS/Linux, `%LOCALAPPDATA%\cartellino_unisa\` su Windows.
Dentro: `data/v2/{anno}/` (stessa struttura di `cartellino_v2.py`, vedi sotto) e
`cartellino_tui.log`.

```bash
mise run tui
# oppure
uv run python cartellino_tui.py
```

Schermate disponibili:

| Schermata | Scorciatoia | Descrizione |
|-----------|:---:|---------|
| **Onboarding** | — | Mostrata automaticamente se manca `config.toml`; imposta anno, data minima riposi, credenziali (opzionali qui) |
| **Dashboard** | — | Home: eccezioni del mese, saldo ore, riepilogo riposi compensativi, ferie/PMF usati, ticket da ricevere, data ultimo aggiornamento |
| **Aggiornamento** | `r` | Scelta del metodo di autenticazione (Credenziali UNISA/SPID/CIE, UNISA disabilitata fuori rete) e download con log in tempo reale |
| **Report** | `p` | Generazione on-demand di riposo compensativo, credito ore, statistiche, ore giornaliere, nel formato scelto in Impostazioni |
| **Timesheet progetto** | `t` | Selezione ed esecuzione di uno YAML esistente in `timesheet/` (vedi sezione dedicata più sotto) |
| **Statistiche** | `v` | Visualizzazione a schermo (non export) delle categorie di `statistiche.xlsx`: Buoni pasto, Ferie, Permessi per motivi familiari, Entrata in ritardo, Straordinari, Visite Specialistiche, Malattia — un pulsante per categoria, colori diversi, disabilitato se la categoria non ha dati |
| **Impostazioni** | `s` | Anno, data minima riposi, formato export, codici dashboard, cartella dati/output (con selettore), data ticket mensa, gestione date escluse (`date_escluse.txt`); credenziali UniSA modificabili in una schermata dedicata ("Modifica credenziali") |

`Esc` torna alla schermata precedente, `q` esce dall'app.

### `cartellino_v2.py` — CLI non interattiva

Dati salvati in `data/v2/{anno}/`.

```bash
mise run app
# oppure
uv run python cartellino_v2.py
```

All'avvio viene chiesto se scaricare il cartellino aggiornato. Se si sceglie il download, viene poi chiesto il metodo di autenticazione:

```
Scegli il metodo di autenticazione:
  1. Credenziali UNISA   ← disponibile solo sulla rete universitaria
  2. SPID
  3. CIE
```

Per SPID e CIE il browser si apre e attende che l'utente completi manualmente il login (timeout 10 minuti).

**Opzioni disponibili** (uso non interattivo/scriptato, nessun prompt se specificate):

```bash
# Salta il download e usa i dati già presenti
uv run python cartellino_v2.py --no-aggiorna-cartellino

# Aggiorna scegliendo il metodo di autenticazione senza prompt interattivo
uv run python cartellino_v2.py --aggiorna-cartellino --auth-method spid

# Genera i report in CSV invece di xlsx (default: quello configurato in config.toml/Impostazioni TUI)
uv run python cartellino_v2.py --no-aggiorna-cartellino --export-format csv

# Genera solo alcuni report (default: tutti)
uv run python cartellino_v2.py --no-aggiorna-cartellino --solo-report statistiche,credito

# Genera anche il timesheet di progetto (vedi sezione dedicata)
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml
```

| Opzione | Valori | Descrizione |
|---------|--------|-------------|
| `--aggiorna-cartellino`/`--no-aggiorna-cartellino` | flag | Scarica i dati aggiornati oppure usa solo quelli già presenti; se omesso, viene chiesto a schermo |
| `--auth-method` | `unisa`, `spid`, `cie` | Metodo di autenticazione per il download; se omesso e il download è attivo, viene chiesto a schermo |
| `--export-format` | `xlsx`, `csv` | Formato dei report generati; se omesso usa quello configurato (default `xlsx`) |
| `--solo-report` | `cartellino`, `riposo`, `credito`, `statistiche`, `ore-giornaliere` (separati da virgola) | Genera solo i report indicati; se omesso li genera tutti |
| `--timesheet-progetto` | nome file YAML | Genera anche il timesheet di progetto (vedi sezione dedicata) |

### `main.py` — versione legacy

Dati salvati in `data/{anno}/`. Stessa logica di download, ma pipeline di elaborazione precedente (senza statistiche e ore giornaliere).

```bash
uv run python main.py
uv run python main.py --no-aggiorna-cartellino
```

## 📁 Struttura dati (versione corrente)

```
CartellinoUniSA/
├── templates/
│   └── timesheet_progetto_template.yaml  ← template per il timesheet di progetto
├── timesheet/                            ← YAML personali (ignorati da git)
│   └── mio_progetto.yaml                 ← copia e adatta dal template
└── data/v2/
    └── {anno}/
        ├── input/
        │   ├── cartellino.feather     ← scaricato da get.py (formato primario, Feather/pyarrow)
        │   ├── cartellino.xlsx        ← solo legacy: se presente e manca il .feather, viene
        │   │                            migrato automaticamente una tantum al primo avvio
        │   ├── date_escluse.txt       ← date da escludere/ridurre dal calcolo OE
        │   ├── riposi_usati.txt       ← fallback per riposi già fruiti (se no MIN_DATE)
        │   └── data_ticket.txt        ← data da cui i ticket sono stati pagati
        └── output/
            ├── cartellino.xlsx               ← cartellino con colonna Codice aggiunta
            ├── riposo_compensativo.xlsx      ← dettaglio e riassunto ore eccedenti
            ├── riposi_compensativi.txt       ← riepilogo testuale riposi
            ├── credito_ore.xlsx              ← credito ore mensile
            ├── statistiche.xlsx              ← più fogli (ticket, ferie, malattia, ...)
            ├── ore_giornaliere.xlsx          ← ore OO-DIU per giorno, per mese
            └── ore_svolte_per_giorno/
                └── {nome_progetto}/          ← generato dal timesheet di progetto
                    ├── 01_gennaio.xlsx
                    ├── 02_febbraio.xlsx
                    └── ...
```

> Questa struttura è relativa alla cartella del repository quando si usa `cartellino_v2.py`
> (CLI/dev). Per l'eseguibile standalone (`cartellino_tui.py`), la stessa struttura (`data/v2/`
> in poi) vive dentro `~/.cartellino_unisa/` (`%LOCALAPPDATA%\cartellino_unisa\` su Windows), non
> nella cartella da cui si lancia il binario.

## 📝 File di input

### `date_escluse.txt`

Date da escludere dal calcolo delle ore eccedenti. Due formati supportati:

```
# Esclusione completa della giornata (DD-MM-YYYY)
16-01-2025
17-01-2025

# Sottrazione parziale: sottrae HH:MM dalle ore eccedenti di quel giorno
20-01-2025 03:30
```

### `riposi_usati.txt` *(opzionale)*

Usato solo se `MIN_DATE_RIPOSI_USATI` non è impostato nel `.env`. Elenco delle date in cui sono stati fruiti riposi compensativi:

```
2025-06-26
2025-06-27
2025-07-15
```

### `data_ticket.txt`

Data da cui il ticket mensa viene pagato dall'ente (formato `DD-MM-YYYY`). Usato per distinguere i ticket già ricevuti da quelli ancora da ricevere:

```
01-01-2025
```

## 📊 Output generati

### `riposo_compensativo.xlsx`
Due fogli:
- **dettaglio**: ore eccedenti giornaliere con stato, data, voce base e intervallo (hh:mm)
- **riassunto**: totale ore/minuti eccedenti raggruppati per stato di elaborazione

### `riposi_compensativi.txt`
Riepilogo testuale dei riposi compensativi maturati, con indicazione delle date utilizzate e delle ore mancanti al completamento:

```
_________________________________________________
Riposo compensativo 1: - usato per il 26-06-2025
_________________________________________________
    - 01-01-2025 -> 02:30 [OK]
    - 02-01-2025 -> 01:45 [OK]
    ...
_________________________________________________
Riposo compensativo 2: - ore necessarie al completamento: 5:42
_________________________________________________
    - 06-01-2025 -> 01:30 [OK]
_________________________________________________
```

### `credito_ore.xlsx`
Credito ore mensile per stato di elaborazione, con e al netto dei riposi maturati.

### `statistiche.xlsx`
File multi-foglio con:
| Foglio | Contenuto |
|--------|-----------|
| `ticket` | Giorni con ticket mensa, valore maturato e da ricevere |
| `statistica_ticket` | Conteggio ticket per mese e stato |
| `visite_specialistiche` | Giornate con visita specialistica (VSG) |
| `straordinari` | Giornate con straordinario (STRSOS, FSTLAV, OS-FSD) |
| `malattia` | Giornate di malattia/ricovero (MAL, RIC) |
| `ferie` | Giornate di ferie/festività (FER, FEV, FST) |
| `vigilanza_concorsi` | Giornate di vigilanza concorsi (VIG) |
| `permessi_gravi_motivi` | Permessi per gravi motivi (PMF) |
| `entrata_ritardo` | Giornate con entrata in ritardo (ERIT) |

### `ore_giornaliere.xlsx`
Ore OO-DIU (ore ordinarie) per ogni giornata lavorativa, organizzate per mese in fogli separati.

## 📐 Timesheet e rendiconto di progetto

Genera i fogli di rendicontazione mensile del progetto a partire dal cartellino elaborato. Produce due tipologie di output nella cartella `data/v2/{anno}/output/ore_svolte_per_giorno/{nome_progetto}/`:

| File | Descrizione |
|------|-------------|
| `{MM}_{mese}.xlsx` | Fogli mensili semplificati (uno per mese) |
| `TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx` | Rendiconto formale compilato dal template istituzionale |

Il rendiconto formale è opzionale: viene generato solo se si specifica `template_rendiconto` nella configurazione YAML.

### 1. Configurazione YAML

Copia il template nella cartella `timesheet/` e adattalo:

```bash
cp templates/timesheet_progetto_template.yaml timesheet/mio_progetto.yaml
```

I file nella cartella `timesheet/` sono ignorati da git (dati personali). Il template in `templates/` è invece versionato.

Struttura completa del file YAML:

```yaml
progetto:
  nome: "NOME_PROGETTO"           # nome della sottocartella di output
  cup: "D43C22005040001"          # CUP del progetto
  codice: "PNC-E3-2022-23683267"  # codice identificativo del progetto
  anno: 2025                      # anno da elaborare (deve coincidere con CURRENT_YEAR)

  # (opzionale) Template Excel istituzionale per il rendiconto formale.
  # Se presente, genera anche TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx
  template_rendiconto: "templates/TS_DHEAL_COM_2025_Nome_Cognome.xlsx"

  # (opzionale) Dati anagrafici del dipendente per il rendiconto
  persona:
    figura_professionale: "Personale Tecnico Amministrativo (PTA)"
    nome: "Mario"
    cognome: "Rossi"
    codice_fiscale: "RSSMRA80A01F839X"

mesi:                        # mesi da includere (1-12)
  - 1
  - 2
  - 3

ore_totali: 100.0            # ore totali da distribuire

# (opzionale) Intervalli di giorni in cui TUTTE le ore lavorate vanno al progetto
giorni_interi:
  - da: "2025-01-15"
    a:  "2025-01-17"         # 15, 16, 17 gennaio: ore_progetto = ore_svolte
  - da: "2025-03-10"
    a:  "2025-03-10"         # singolo giorno

# (opzionale) Ore fisse su singole giornate
ore_fisse:
  - data: "2025-05-05"
    ore: 3.0                 # 3 ore esatte il 5 maggio
  - data: "2025-06-20"
    ore: 2.5
```

### 2. Esecuzione

```bash
# Passa solo il nome del file: viene cercato automaticamente in timesheet/
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml

# Oppure passa un percorso completo o relativo
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto /percorso/assoluto/config.yaml
```

### 3. Regole di distribuzione delle ore

1. Le ore dei `giorni_interi` (= ore effettivamente lavorate quel giorno) e delle `ore_fisse` vengono sommate e sottratte da `ore_totali` per ottenere le **ore residue**.
2. Le ore residue vengono spalmate equamente sulle giornate con **almeno 5 ore lavorate** che non rientrano nei punti precedenti, arrotondando alla **mezz'ora inferiore**.
3. L'eventuale resto viene sommato all'ultimo giorno idoneo in modo che il totale sia esattamente uguale a `ore_totali`.

### 4. Output: fogli mensili semplificati

Ogni file `{MM}_{mese}.xlsx` ha il formato:

| | 01 | 02 | 03 | ... |
|---|---|---|---|---|
| **Giorno** | 01 | 02 | 03 | ... |
| **Attività svolta sul progetto CUP: …** | 2.0 | 2.0 | 0 | ... |
| **Attività svolte su altri progetti** | 0 | 0 | 0 | ... |
| **Attività ordinaria** | 6.15 | 7.0 | 0 | ... |
| **Altro (Malattia, Ferie..)** | 0 | 0 | 0 | ... |

### 5. Output: rendiconto formale (opzionale)

Se `template_rendiconto` è impostato, viene generato `TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx` a partire dal template istituzionale `.xlsx`. Il file viene adattato all'anno di riferimento e compilato automaticamente:

| Cella | Contenuto |
|-------|-----------|
| N12 | Nome del mese in maiuscolo (es. `FEBBRAIO`) |
| AG12 | Anno |
| C15 | CUP del progetto |
| C16 | Codice del progetto |
| C18 | Figura professionale |
| C19 | Nome |
| Y19 | Cognome |
| C20 | Codice fiscale |
| Y20 | Ore totali rendicontate nel mese |
| C22 | `Mese di Febbraio 2026` |
| Righe 24–27 | Ore progetto/ordinarie per ogni giorno del mese |

Vengono inoltre corretti automaticamente:
- **Colori weekend**: sabati e domeniche colorati con il grigio del template, lunedì–venerdì senza colore, in base al calendario effettivo dell'anno (non del template originale)
- **Fogli Riassuntivo**: i riferimenti formula ai fogli mensili vengono aggiornati con i nuovi nomi — il layout e la logica del Riassuntivo non vengono modificati

## 📦 Eseguibili standalone (senza Python)

A partire dalla v2.0.0, ogni tag `v2.*` genera automaticamente (GitHub Actions,
`.github/workflows/release.yml`) un eseguibile standalone della TUI per macOS, Windows e Linux,
allegato alla relativa [GitHub Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest).
Non serve installare Python, `mise` o `uv`: si scarica lo zip del proprio sistema operativo, si
estrae e si esegue il binario dentro la cartella estratta — **non spostare l'eseguibile fuori
dalla sua cartella**: le librerie di supporto (Python, Textual, pandas/pyarrow, ecc.) stanno lì
accanto, servono per farlo funzionare.

**Chrome resta comunque una dipendenza esterna obbligatoria** (il download del cartellino usa
Selenium, che non è imbottigliabile in un eseguibile standalone): va installato separatamente,
qualunque sia il sistema operativo.

### 🍎 macOS

**Opzione consigliata — installer `.pkg`:**

1. Dalla pagina delle [Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest),
   scarica `cartellino-unisa.pkg`
2. Doppio click, segui la procedura guidata (installa in `/usr/local/cartellino-unisa`, crea il
   comando `cartellino-unisa` nel `PATH`)
3. Apri il Terminale ed esegui semplicemente:
   ```bash
   cartellino-unisa
   ```

Il `.pkg` è **firmato con certificato Developer ID Installer e notarizzato/staplato da Apple**:
Gatekeeper non dovrebbe mostrare alcun avviso, nemmeno offline.

**Opzione alternativa — zip della cartella onedir** (per chi preferisce non installare nulla a
livello di sistema):

1. Scarica `cartellino-unisa-macos.zip`, estrai (doppio click, oppure
   `unzip cartellino-unisa-macos.zip` da terminale)
2. Apri il Terminale, entra nella cartella estratta ed esegui:
   ```bash
   cd cartellino-unisa
   ./cartellino-unisa
   ```

L'eseguibile dentro lo zip è anch'esso firmato e notarizzato: se comparisse comunque "app non
verificata"/"sviluppatore non identificato" (es. per una build senza i secrets di firma
configurati), risolvi con: click destro (o `Ctrl`+click) sul file `cartellino-unisa` → **Apri**,
poi conferma nel dialogo (necessario solo la prima volta).

### 🪟 Windows

**Opzione consigliata — installer `cartellino-unisa-setup.exe`:**

1. Dalla pagina delle [Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest),
   scarica `cartellino-unisa-setup.exe`
2. Doppio click, segui la procedura guidata (installa in Program Files, crea una voce nel Menu
   Start)
3. Avvia "Cartellino UniSA" dal Menu Start (apre una finestra terminale, essendo un'app testuale)

**Opzione alternativa — zip della cartella onedir:**

1. Scarica `cartellino-unisa-windows.zip`, estrai (click destro → **Estrai tutto...**)
2. Apri PowerShell o il Prompt dei comandi, entra nella cartella estratta ed esegui:
   ```powershell
   cd cartellino-unisa
   .\cartellino-unisa.exe
   ```

In entrambi i casi il binario **non è firmato** (nessun certificato di firma codice per Windows,
vedi `ignored/signed_windows.md` per le opzioni valutate), quindi al primo avvio SmartScreen mostra
"Windows ha protetto il PC": clicca **Ulteriori informazioni** → **Esegui comunque** (necessario
solo la prima volta).

### 🐧 Linux

**Opzione consigliata — pacchetto `.deb`/`.rpm`:**

1. Dalla pagina delle [Release](https://github.com/staffDiUnisa/CartellinoUniSA/releases/latest),
   scarica `cartellino-unisa_<versione>_amd64.deb` (Debian/Ubuntu) o
   `cartellino-unisa-<versione>.x86_64.rpm` (Fedora/RHEL/openSUSE)
2. Installa:
   ```bash
   sudo dpkg -i cartellino-unisa_<versione>_amd64.deb      # Debian/Ubuntu
   # oppure
   sudo rpm -i cartellino-unisa-<versione>.x86_64.rpm      # Fedora/RHEL/openSUSE
   ```
3. Esegui da terminale: `cartellino-unisa`

**Opzione alternativa — zip della cartella onedir:**

1. Scarica `cartellino-unisa-linux.zip`, estrai ed esegui da terminale:
   ```bash
   unzip cartellino-unisa-linux.zip
   cd cartellino-unisa
   ./cartellino-unisa
   ```
   Se il sistema segnala permessi mancanti (`Permission denied`): `chmod +x cartellino-unisa`.

In entrambi i casi, Chrome/Chromium deve essere installato e raggiungibile dal `PATH` per il
download del cartellino (Selenium/`webdriver-manager` lo useranno automaticamente). Il `.deb`/
`.rpm` è costruito su Ubuntu (glibc recente): su distro molto datate potrebbero presentarsi
incompatibilità di libreria, stesso limite implicito già presente per lo zip.

### Note comuni

> Perché una cartella (zip) e non un singolo eseguibile: la prima versione usava un eseguibile
> "onefile", che su macOS si è rivelato rotto (`pyarrow` falliva l'import sul binario scaricato,
> pur funzionando su una build locale) — le librerie native estratte a runtime in una cartella
> temporanea non firmata vengono bloccate da macOS. La modalità "onedir" (cartella) evita questa
> estrazione runtime.

Per rigenerare l'eseguibile localmente (es. per verificare una modifica prima di taggare una
release):
```bash
uv sync --group build
uv run pyinstaller packaging/cartellino.spec
./dist/cartellino-unisa/cartellino-unisa   # .exe su Windows
```

## 🔧 Troubleshooting

**Chrome non si avvia / ChromeDriver non trovato**
- Assicurarsi che Google Chrome sia installato
- Il driver viene scaricato automaticamente da `webdriver_manager`; verificare la connessione internet al primo avvio

**Timeout durante il login con SPID o CIE**
- Il browser rimane aperto per 10 minuti in attesa del completamento del login; completare l'autenticazione entro quel tempo

**"Credenziali UNISA" non disponibile**
- L'opzione compare solo se si è connessi alla rete universitaria (VPN compresa)

**Date non riconosciute in `date_escluse.txt`**
- Verificare il formato: `DD-MM-YYYY` oppure `DD-MM-YYYY HH:MM`

**`MIN_DATE_RIPOSI_USATI` non riconosciuta**
- Il formato è `MM-DD` (mese-giorno), es. `06-01` per il 1° giugno
- In caso di errore, lo script userà automaticamente `riposi_usati.txt`

**Totale timesheet non corrisponde**
- Se le ore dei `giorni_interi` e `ore_fisse` superano `ore_totali`, viene stampato un avviso e le ore residue sono azzerate
- Se il resto da aggiungere all'ultimo giorno è ≥ 30 min, viene stampato un avviso (il totale è comunque corretto)

**Il rendiconto non viene generato**
- Verificare che `template_rendiconto` sia presente nel YAML e che il file `.xlsx` esista al percorso indicato
- Il template deve essere un file `.xlsx` (non `.xlsm`) con i fogli mensili rinominati nel formato `{Mese} {anno}` (es. `Gennaio 2025`)

**Errori `#REF!` nel foglio Riassuntivo**
- Non si verifica con i file generati dallo script, che aggiorna automaticamente i riferimenti formula
- Può accadere se si rinominano manualmente i fogli mensili senza aggiornare il Riassuntivo

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch: `git checkout -b feature/nuova-funzionalita`
3. Commit: `git commit -m 'Aggiunta nuova funzionalità'`
4. Push: `git push origin feature/nuova-funzionalita`
5. Apri una Pull Request

## 📄 Licenza

Distribuito sotto licenza GPL 3.0. Vedi [LICENSE](LICENSE) per i dettagli.

## ⚠️ Disclaimer

Questo software è fornito "così com'è", senza garanzie di alcun tipo. Gli autori non sono responsabili per eventuali errori nei calcoli o nell'interpretazione dei dati. Verificare sempre i risultati con i dati ufficiali.

---

> **Sicurezza**: non condividere mai il file `.env` contenente le credenziali.
