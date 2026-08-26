import logging
import os
import sys
from pathlib import Path

# Va fatto PRIMA di qualunque altro import (anche prima di `import pyarrow` sotto):
# su macOS, Homebrew esporta spesso DYLD_LIBRARY_PATH/DYLD_FALLBACK_LIBRARY_PATH
# puntando a /opt/homebrew/lib. Se l'utente ha anche un pacchetto come
# `apache-arrow` installato via brew, queste variabili possono far sì che `dyld`
# carichi la libreria di sistema (stesso nome/versione nominale, ma compilata con
# una versione diversa di Abseil) al posto di quella inclusa nel bundle accanto
# all'eseguibile — riscontrato in produzione e riprodotto in locale:
# `ImportError: ... Symbol not found: __ZN4absl...` risolvendo
# `libarrow_substrait.dylib` verso /opt/homebrew/Cellar/apache-arrow/.../
# libarrow.dylib invece del file bundled.
#
# `os.environ.pop(...)` da solo NON basta: dyld legge/fissa queste variabili
# all'avvio del processo, una modifica di `os.environ` fatta da Python dopo non
# ha effetto retroattivo sulle risoluzioni di libreria per QUESTO processo
# (verificato: stesso identico errore anche con il pop). Serve rilanciare il
# processo (os.execve) con un ambiente ripulito PRIMA che dyld/pyarrow vengano
# toccati di nuovo — dyld del nuovo processo parte così senza queste variabili
# fin dall'inizio.
if getattr(sys, "frozen", False) and (
    os.environ.get("DYLD_LIBRARY_PATH") or os.environ.get("DYLD_FALLBACK_LIBRARY_PATH")
):
    _env_pulito = dict(os.environ)
    _env_pulito.pop("DYLD_LIBRARY_PATH", None)
    _env_pulito.pop("DYLD_FALLBACK_LIBRARY_PATH", None)
    os.execve(sys.executable, sys.argv, _env_pulito)

# Import esplicito e ANTICIPATO sul thread principale, prima di avviare la TUI.
# `pandas` importa `pyarrow` in modo lazy solo alla prima chiamata reale a
# to_feather()/read_feather() (import_optional_dependency): nella TUI la prima
# di queste chiamate avviene dentro il worker thread del download
# (UpdateScreen._scarica, @work(thread=True)), non sul thread principale.
# Riscontrato in produzione (binario PyInstaller firmato/notarizzato su macOS):
# il primo import di pyarrow da un thread diverso da quello principale falliva
# con "Import pyarrow failed", pur essendo il pacchetto correttamente
# impacchettato (verificato con test isolati sullo stesso binario). Importarlo
# qui lo inizializza una volta sola sul thread principale: le importazioni
# successive da qualunque thread riusano il modulo già in sys.modules.
import pyarrow  # noqa: F401

from cartellino.tui.app import run


def _app_data_dir() -> Path:
    """Cartella fissa per dati/log della TUI, indipendente dalla cartella da cui
    viene lanciato l'eseguibile (importante per il binario standalone: un utente
    può lanciarlo dal Desktop, da Downloads, ecc. — percorsi relativi alla cwd
    finirebbero per creare file in posizioni imprevedibili e diverse ad ogni
    avvio). Non usa `platformdirs` (già impiegato per `config.toml`, cartella
    "Application Support"-style, pensata per app GUI): qui si preferisce la
    convenzione da tool a riga di comando, una singola cartella nota nella home
    dell'utente.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        return base / "cartellino_unisa"
    return Path.home() / ".cartellino_unisa"


APP_DATA_DIR = _app_data_dir()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = APP_DATA_DIR / "cartellino_tui.log"

# Livello INFO senza handler su stdout/stderr: la TUI gira sullo schermo alternato di
# Textual, un handler console romperebbe il rendering. I log vengono mostrati a schermo
# tramite `cartellino.tui.logging_handler.RichLogHandler`, aggiunto/rimosso dagli screen
# che eseguono operazioni lunghe (es. `UpdateScreen`); in più, tutto va sempre anche su
# file per poter diagnosticare un crash dopo che la TUI si è chiusa.
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
root_logger.addHandler(file_handler)

DATA_FOLDER = APP_DATA_DIR / "data" / "v2"

if __name__ == "__main__":
    run(data_folder=DATA_FOLDER)
