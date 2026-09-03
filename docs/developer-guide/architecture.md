# Architettura (sintesi)

Questa pagina è una sintesi ad alto livello per orientarsi nel codice. Per i dettagli
implementativi completi — decisioni di design, note su packaging/CI, postmortem di bug reali,
convenzioni interne — la fonte di verità resta
[`CLAUDE.md`](https://github.com/staffDiUnisa/CartellinoUniSA/blob/master/CLAUDE.md) nel
repository: questa pagina non lo duplica, per evitare che i due documenti divergano nel tempo.

## Entry point

- **`main.py`** — CLI legacy, incatena `get.run()` e `process.run()`.
- **`cartellino_v2.py`** — CLI non interattiva corrente (pacchetto `cartellino/`).
- **`cartellino_tui.py`** — TUI Textual, entrypoint consigliato per l'uso interattivo.
- **`cartellino_gui.py`** — GUI desktop PySide6, stesso layer di dominio della TUI.

## Moduli principali (percorso legacy)

- **`get.py`** — scraper Selenium: login su `presenze.unisa.it`, navigazione, paginazione,
  salvataggio in `data/{anno}/input/cartellino.xlsx`.
- **`process.py`** — pipeline di elaborazione (`processa_dati`): esplode le "Voci Base"
  multi-valore, estrae il `Codice`, filtra per codici rilevanti, calcola ore eccedenti/riposi
  compensativi, scrive gli output.
- **`processor/cartellinoprogetto.py`** — distribuzione delle ore di progetto sui giorni
  lavorativi (`CartellinoProgetto`).
- **`model/`** — modelli Pydantic (`RiposoCompensativo`, `OreInserite`).

## Pacchetto `cartellino/` (percorso corrente)

- **`credentials.py`** — wrapper su `keyring` per le credenziali UniSA.
- **`user_config.py`** / **`config.py`** — configurazione utente (`config.toml`) e caricamento a
  runtime, con migrazione automatica da `.env` legacy.
- **`cartellino.py`** — lettura del cartellino grezzo da Feather (formato primario), con
  migrazione one-shot da xlsx legacy.
- **`ore_helpers.py`** — estrazione ore/minuti dalle "Voci Base" e calcolo del saldo con segno
  (vedi [Codici del cartellino](../reference/codes.md)).
- **`export_utils.py`** — scrittura dei report in xlsx/csv.
- **`timesheet_runner.py`** — esecuzione del timesheet di progetto, condivisa tra CLI e TUI/GUI.
- **`update_checker.py`** — controllo release GitHub per il pulsante "Controlla aggiornamenti".
- **`tui/`** — app Textual: `app.py` (routing), `screens/` (una schermata per funzionalità),
  `app.tcss` (stile e palette colori dei pulsanti).
- **`gui/`** — app PySide6, mirror concettuale della TUI: `app.py` (`MainWindow`,
  `QStackedWidget`), `screens/`, `style.qss` (stile, mirror di `app.tcss`), `workers.py`
  (download/controllo aggiornamenti in thread separati).

## Packaging

Gli eseguibili standalone sono generati con PyInstaller in modalità **onedir** (non onefile),
firmati/notarizzati su macOS, distribuiti come `.pkg`/`.exe`/`.deb`/`.rpm` oltre agli zip onedir
storici. Il dettaglio completo (inclusi i bug reali risolti nel tempo: firma, notarizzazione,
bundling di pyarrow/selenium, hang della GUI su macOS, ecc.) è documentato in `CLAUDE.md` — non
riprodotto qui perché troppo specifico per la manutenzione della sola CI/release e a rischio di
disallineamento.

## Contribuire

Vedi [Contribuire](contributing.md).
