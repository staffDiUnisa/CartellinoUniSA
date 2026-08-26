import logging

from textual.app import App
from textual.widgets import RichLog


class RichLogHandler(logging.Handler):
    """Inoltra i record di logging a un widget `RichLog`.

    Pensato per operazioni lunghe lanciate in un worker thread (es. il download
    Selenium in `get.ottieni_cartellino`): usa `App.call_from_thread` per restare
    thread-safe, con fallback a scrittura diretta se già sul thread dell'app.
    """

    def __init__(self, app: App, richlog: RichLog, level: int = logging.INFO) -> None:
        super().__init__(level)
        self._app = app
        self._richlog = richlog

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        try:
            self._app.call_from_thread(self._richlog.write, msg)
        except RuntimeError:
            self._richlog.write(msg)
