import logging
from pathlib import Path

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
