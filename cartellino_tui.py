import logging
from pathlib import Path

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

LOG_FILE = Path("cartellino_tui.log")

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

DATA_FOLDER = Path("data/v2")

if __name__ == "__main__":
    run(data_folder=DATA_FOLDER)
