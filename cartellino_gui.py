import logging
import os
import sys
from pathlib import Path

# Va fatto PRIMA di qualunque altro import (anche prima di `import pyarrow` sotto):
# stesso identico workaround di cartellino_tui.py, vedi lì per i dettagli — su
# macOS, DYLD_LIBRARY_PATH/DYLD_FALLBACK_LIBRARY_PATH esportate da Homebrew
# possono far caricare a `dyld` una libarrow di sistema incompatibile al posto
# di quella bundled. Il fix (rilancio del processo con ambiente ripulito) non è
# stato ancora riverificato sul binario GUI (spike PyInstaller, Fase 0
# TODO_gui.md) ma è applicato preventivamente per coerenza con l'entrypoint TUI,
# che condivide la stessa dipendenza pyarrow/pandas.
if getattr(sys, "frozen", False) and (
    os.environ.get("DYLD_LIBRARY_PATH") or os.environ.get("DYLD_FALLBACK_LIBRARY_PATH")
):
    _env_pulito = dict(os.environ)
    _env_pulito.pop("DYLD_LIBRARY_PATH", None)
    _env_pulito.pop("DYLD_FALLBACK_LIBRARY_PATH", None)
    os.execve(sys.executable, sys.argv, _env_pulito)

# Import esplicito e anticipato sul thread principale, prima di avviare la GUI.
# Stesso motivo di cartellino_tui.py: pandas importa pyarrow in modo lazy solo
# alla prima chiamata reale a to_feather()/read_feather(), che nella GUI
# avverrà dentro un worker thread (Fase 4 TODO_gui.md, non ancora scritto).
import pyarrow  # noqa: F401,E402

from cartellino.gui.app import run  # noqa: E402


def _app_data_dir() -> Path:
    """Cartella fissa per dati/log della GUI, indipendente dalla cartella da cui
    viene lanciato l'eseguibile. Stessa convenzione di ``cartellino_tui.py``
    (stessa cartella ``~/.cartellino_unisa`` / ``%LOCALAPPDATA%\\cartellino_unisa``,
    non separata per prodotto: GUI e TUI condividono la stessa ``config.toml``
    e gli stessi dati, sono due frontend sullo stesso layer di dominio — vedi
    "Distribuzione combinata" in TODO_gui.md)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        return base / "cartellino_unisa"
    return Path.home() / ".cartellino_unisa"


APP_DATA_DIR = _app_data_dir()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = APP_DATA_DIR / "cartellino_gui.log"

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
root_logger.addHandler(file_handler)

DATA_FOLDER = APP_DATA_DIR / "data" / "v2"

if __name__ == "__main__":
    run(data_folder=DATA_FOLDER)
