"""Update screen (Fase 4 TODO_gui.md), mirror di ``cartellino/tui/screens/update.py``.

Aggiornamento del cartellino: mai automatico, richiede scelta esplicita del
metodo di autenticazione e avvio manuale. La parte più delicata (già
documentata nel piano): Selenium apre una finestra Chrome reale (per SPID/CIE)
mentre la GUI resta aperta, e il download va eseguito in un thread separato
(`DownloadWorker`, Fase 4 `cartellino/gui/workers.py`) per non bloccare
l'event loop di Qt fino a 10 minuti (`WebDriverWait` dentro `get.py`).
"""

import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from cartellino.gui.workers import DownloadWorker, QtLogHandler
from get import METODI_AUTENTICAZIONE, is_on_unisa_network

log = logging.getLogger(__name__)


class UpdateScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_folder = None
        self._handler: QtLogHandler | None = None
        self._worker: DownloadWorker | None = None
        self._metodo_scelto: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Scegli il metodo di autenticazione e avvia il download."))

        su_rete = is_on_unisa_network()
        self.radio_group = QButtonGroup(self)
        self.radio_buttons: list[QRadioButton] = []
        for metodo in METODI_AUTENTICAZIONE:
            disabilitato = metodo == "Credenziali UNISA" and not su_rete
            radio = QRadioButton(metodo)
            radio.setEnabled(not disabilitato)
            radio.toggled.connect(self._on_radio_toggled)
            self.radio_group.addButton(radio)
            self.radio_buttons.append(radio)
            layout.addWidget(radio)

        if not su_rete:
            nota = QLabel("Credenziali UNISA non disponibile: non sei sulla rete universitaria.")
            nota.setStyleSheet("color: gray;")
            layout.addWidget(nota)

        button_row = QHBoxLayout()
        self.btn_indietro = QPushButton("⬅️ Indietro")
        self.btn_indietro.setObjectName("btn-indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        self.btn_avvia = QPushButton("⬇️ Avvia download")
        self.btn_avvia.setObjectName("btn-avvia")
        self.btn_avvia.clicked.connect(self._avvia)
        button_row.addWidget(self.btn_indietro)
        button_row.addStretch()
        button_row.addWidget(self.btn_avvia)
        layout.addLayout(button_row)

        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget, stretch=1)

    def _on_radio_toggled(self, checked: bool) -> None:
        if not checked:
            return
        radio = self.sender()
        self._metodo_scelto = radio.text()

    def _avvia(self) -> None:
        if not self._metodo_scelto:
            self.log_widget.appendPlainText("Seleziona un metodo di autenticazione.")
            return

        data_folder = self.data_folder or getattr(self.window(), "data_folder", None)
        if data_folder is None:
            self.log_widget.appendPlainText("Cartella dati non disponibile.")
            return

        self.btn_avvia.setEnabled(False)
        self.btn_indietro.setEnabled(False)
        for radio in self.radio_buttons:
            radio.setEnabled(False)

        self._handler = QtLogHandler()
        self._handler.signals.log_line.connect(self.log_widget.appendPlainText)
        logging.getLogger().addHandler(self._handler)
        logging.getLogger().setLevel(logging.INFO)

        self._worker = DownloadWorker(data_folder, self._metodo_scelto, self)
        self._worker.finished_download.connect(self._fine_download)
        self._worker.start()

    def _fine_download(self, successo: bool) -> None:
        if self._handler is not None:
            logging.getLogger().removeHandler(self._handler)
            self._handler = None
        self.btn_avvia.setEnabled(True)
        self.btn_indietro.setEnabled(True)
        su_rete = is_on_unisa_network()
        for radio in self.radio_buttons:
            disabilitato = radio.text() == "Credenziali UNISA" and not su_rete
            radio.setEnabled(not disabilitato)
        if successo:
            # Mirror di `self.app.pop_screen()`: torna alla Dashboard, che si
            # aggiorna da sola (`MainWindow` connette questo segnale a
            # `dashboard_screen.refresh()` + routing). In caso di errore resta
            # su questa schermata così l'utente legge il log.
            window = self.window()
            if hasattr(window, "show_dashboard"):
                window.show_dashboard()

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_dashboard"):
            window.show_dashboard()
