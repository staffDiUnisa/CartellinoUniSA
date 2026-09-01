# Changelog

Novità principali per ciascuna release. Le sezioni `## vX.Y.Z` (senza suffisso `-rcN`) vengono
lette automaticamente da `.github/workflows/release.yml` e usate come descrizione della GitHub
Release: aggiungi la sezione della prossima versione **prima** di taggare una release definitiva,
altrimenti la release verrà pubblicata senza descrizione delle novità (solo changelog
auto-generato da GitHub).

## v3.0.2

- **Fix GUI macOS "non risponde" all'avvio da Finder/Launchpad** (issue #6): il launcher
  `Cartellino UniSA.app` faceva `exec` del binario installato in `/usr/local/cartellino-unisa/`,
  perdendo l'identità di bundle macOS necessaria a PySide6/Shiboken per usare la cache delle
  preferenze di sistema — ogni lookup di localizzazione durante l'avvio (migliaia di volte)
  degradava a una query lenta non cache-ata, con l'app che restava bloccata per minuti.
  L'eseguibile e le sue librerie sono ora impacchettati come un vero bundle `.app`
  (`Contents/MacOS`/`Contents/Frameworks`/`Contents/Resources`), firmato e notarizzato
  correttamente: l'avvio richiede ora circa un secondo.

## v3.0.1

- **Fix installer `.pkg` macOS**: su una macchina con una versione precedente già installata,
  il `.pkg` di v3.0.0 falliva ("The installer encountered an error that caused the installation
  to fail") perché il launcher TUI rinominato ("Cartellino UniSA (Terminale).app") aveva
  mantenuto lo stesso identificatore del vecchio "Cartellino UniSA.app": macOS tracciava
  l'aggiornamento per identificatore, non per nome file, e cercava di spostarlo nel vecchio
  percorso — collidendo con il nuovo launcher della GUI installato nello stesso pacchetto.
  Identificatore del launcher TUI cambiato per evitare l'ambiguità.

## v3.0.0

- **Nuova interfaccia grafica desktop (GUI)**, `cartellino_gui.py`, basata su
  [PySide6](https://doc.qt.io/qtforpython-6/): affianca la TUI senza sostituirla, stesse
  funzionalità (dashboard, aggiornamento con log in tempo reale, report on-demand, timesheet di
  progetto, statistiche, impostazioni, gestione date escluse e credenziali), condividendo dati,
  `config.toml` e credenziali con la TUI — sono due frontend sullo stesso strumento, non due
  prodotti separati.
- **Distribuzione combinata**: ogni pacchetto/installer per OS (`.pkg`/`.exe`/`.deb`/`.rpm` e gli
  zip onedir storici) include ora sia l'eseguibile TUI/CLI (`cartellino-unisa`) sia quello GUI
  (`cartellino-unisa-gui`).
- **macOS**: il launcher `.app` esistente per la TUI è stato rinominato **Cartellino UniSA
  (Terminale)** — il nome **Cartellino UniSA** ora appartiene al nuovo launcher della GUI,
  comportamento atteso da un doppio click da Finder/Launchpad. Entrambi firmati con certificato
  Developer ID e notarizzati/staplati da Apple.
- **Windows**: il Menu Start ha ora due voci distinte, **Cartellino UniSA** (GUI, con icona sul
  Desktop opzionale) e **Cartellino UniSA (Terminale)** (TUI).

## v2.0.5

- **Uniformità pulsanti nella TUI**: dimensioni minime e spaziatura dei pulsanti ora coerenti
  su tutte le schermate (Impostazioni, Date escluse, Credenziali, Onboarding, Aggiorna
  cartellino, Timesheet, Controllo aggiornamenti), non solo su Dashboard/Report/Statistiche
  come prima.

## v2.0.4

- **Verifica aggiornamenti dell'app**: controllo di nuove release GitHub sia on-demand
  (pulsante "Controlla aggiornamenti" in Dashboard) sia all'avvio (disattivabile da
  Impostazioni). Se trovata una versione più recente, apre la pagina della release nel browser
  per il download — l'installazione resta manuale come oggi, nessun self-update automatico.

## v2.0.3

- **Fix layout non responsivo** (Dashboard e Statistiche): le righe di pulsanti ora vanno a capo
  su più righe quando il terminale si restringe, invece di uscire dal viewport diventando
  inaccessibili.
- **Statistiche → Riposo compensativo**: nuovo pulsante per esportare i riposi compensativi in
  `riposi_compensativi.txt`, senza dover passare dalla generazione report.

## v2.0.2

- **Nuovo launcher `.app` per macOS**, incluso nello stesso installer `.pkg`: apre il terminale
  scelto dall'utente (Terminale nativo, Ghostty o iTerm2 — non Warp, privo di supporto di
  scripting) ed esegue la CLI/TUI. Al primo avvio chiede quale terminale usare, ricorda la
  scelta (cambiabile da Impostazioni), massimizza la finestra e la chiude automaticamente
  all'uscita dalla TUI.
- **Tema della TUI persistito**: il tema scelto dalla palette comandi (`^p` → Theme) viene ora
  salvato in `config.toml` e riapplicato automaticamente al successivo avvio.
- **Statistiche**: nuova vista "Riposo compensativo" con i gruppi di riposi compensativi (stesso
  contenuto di `riposi_compensativi.txt`) mostrati in un `MarkdownViewer` più leggibile del
  formato a delimitatori del file di testo.

## v2.0.1

- **Installer nativi per ciascun sistema operativo**: `.pkg` firmato/notarizzato/staplato per
  macOS, `setup.exe` (Inno Setup) per Windows, `.deb`/`.rpm` per Linux — oltre agli storici zip
  della cartella onedir. Installano l'eseguibile in un percorso fisso e aggiungono il comando
  `cartellino-unisa` al `PATH`.

## v2.0.0

Riscrittura importante del progetto (roadmap `TODO.md`), pur mantenendo intatti gli entrypoint
legacy `main.py`/`process.py`:

- **Nuovo entrypoint `cartellino_v2.py`** (CLI non interattiva) e **`cartellino_tui.py`** (TUI
  Textual con dashboard, onboarding, aggiornamento con log in tempo reale, impostazioni, report
  on-demand e timesheet di progetto).
- **Configurazione in `config.toml`** (cartella utente standard) e **credenziali nel keyring
  nativo del sistema operativo** al posto di file `.env`, con migrazione automatica one-shot dal
  vecchio formato.
- **Storage del cartellino in formato Feather** al posto di xlsx grezzo (più veloce da
  leggere/scrivere), con migrazione automatica one-shot da un `cartellino.xlsx` legacy.
- **Ambiente di sviluppo su `mise`/`uv`** al posto di `pip`/`venv`.
- **Eseguibili standalone multipiattaforma** (macOS/Windows/Linux, PyInstaller onedir) pubblicati
  automaticamente su GitHub Release ad ogni tag, con firma e notarizzazione Apple per macOS.
- Export dei report configurabile in xlsx o csv; report generabili singolarmente ("on demand")
  sia da CLI che da TUI, non più tutti insieme.
