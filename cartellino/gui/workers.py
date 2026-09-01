"""QObject/QThread + Signal per lavoro in background (Fase 4 TODO_gui.md).

Mirror concettuale di `cartellino/tui/logging_handler.py::RichLogHandler` (log
in tempo reale da un worker thread verso un widget) e del pattern
`@work(thread=True)` + `App.call_from_thread` usato da `UpdateScreen._scarica`
nella TUI. Qt gestisce la stessa cosa nativamente: un `Signal` emesso da un
thread diverso da quello del ricevente diventa automaticamente una
`QueuedConnection` (eseguita sul thread del ricevente), niente `call_from_thread`
esplicito da scrivere a mano.
"""

import logging

from PySide6.QtCore import QObject, QThread, Signal

from cartellino.update_checker import ReleaseInfo, check_for_update
from get import ottieni_cartellino

log = logging.getLogger(__name__)


class QtLogHandler(logging.Handler):
    """Handler di `logging` che inoltra ogni record come `Signal` Qt.

    A differenza di `RichLogHandler` (che scrive testo con markup Rich in un
    `RichLog` Textual), qui il testo è semplice: nessun equivalente del
    problema di escaping `[...]` (i widget Qt di log — `QPlainTextEdit` — non
    interpretano markup).
    """

    class _Signals(QObject):
        log_line = Signal(str)

    def __init__(self, level: int = logging.INFO) -> None:
        super().__init__(level)
        self.signals = self._Signals()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        self.signals.log_line.emit(msg)


class DownloadWorker(QThread):
    """Esegue `get.ottieni_cartellino` (Selenium, bloccante) in un thread separato.

    Mirror di `UpdateScreen._scarica` (`@work(thread=True, exclusive=True)`):
    `QThread` è di per sé "exclusive" nel senso che serve avviarne una nuova
    istanza per un nuovo download, non è pensato per essere riavviato.
    """

    finished_download = Signal(bool)

    def __init__(self, data_folder, metodo: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.data_folder = data_folder
        self.metodo = metodo

    def run(self) -> None:
        successo = False
        try:
            ottieni_cartellino(self.data_folder, metodo=self.metodo)
            successo = True
        except Exception as e:
            # log.exception scrive anche il traceback completo sul file di log
            # (cartellino_gui.log): alcuni messaggi (es. "Import pyarrow
            # failed" di pandas) nascondono la vera eccezione originale dietro
            # un messaggio amichevole generico, stesso motivo già documentato
            # per l'entrypoint TUI.
            log.exception(f"Download fallito: {e}")
        finally:
            self.finished_download.emit(successo)


class UpdateCheckWorker(QThread):
    """Controllo aggiornamenti dell'app (`update_checker.check_for_update`) in
    thread separato. Mirror di `_check_update_worker` (`@work(thread=True)`),
    condiviso tra il pulsante "Controlla aggiornamenti" della Dashboard (Fase
    3) e il controllo automatico all'avvio (Fase 11, `MainWindow.on_mount`)."""

    finished_ok = Signal(object)  # ReleaseInfo | None
    failed = Signal(str)

    def __init__(self, current_version: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.current_version = current_version

    def run(self) -> None:
        try:
            release: ReleaseInfo | None = check_for_update(self.current_version)
        except Exception as e:
            self.failed.emit(str(e))
            return
        self.finished_ok.emit(release)
