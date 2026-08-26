# Changelog

Novità principali per ciascuna release. Le sezioni `## vX.Y.Z` (senza suffisso `-rcN`) vengono
lette automaticamente da `.github/workflows/release.yml` e usate come descrizione della GitHub
Release: aggiungi la sezione della prossima versione **prima** di taggare una release definitiva,
altrimenti la release verrà pubblicata senza descrizione delle novità (solo changelog
auto-generato da GitHub).

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
