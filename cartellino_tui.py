import logging
from pathlib import Path

from cartellino.tui.app import run

# Livello INFO senza handler su stdout/stderr: la TUI gira sullo schermo alternato di
# Textual, un handler console romperebbe il rendering. I log vengono mostrati tramite
# `cartellino.tui.logging_handler.RichLogHandler`, aggiunto/rimosso dagli screen che
# eseguono operazioni lunghe (es. `UpdateScreen`).
logging.getLogger().setLevel(logging.INFO)

DATA_FOLDER = Path("data/v2")

if __name__ == "__main__":
    run(data_folder=DATA_FOLDER)
