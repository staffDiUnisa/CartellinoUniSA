"""Timesheet screen (Fase 6 TODO_gui.md), mirror di ``cartellino/tui/screens/timesheet.py``.

Selezione di uno YAML esistente in `timesheet/` e generazione del timesheet
mensile (+ rendiconto Excel, se configurato). Niente wizard di creazione YAML
da zero: resta un'operazione manuale sul filesystem, come nella TUI.
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cartellino.timesheet_runner import esegui_timesheet_progetto

log = logging.getLogger(__name__)

TIMESHEET_FOLDER = Path("timesheet")


class TimesheetScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = None

        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("⬅️ Indietro")
        self.btn_indietro.setObjectName("btn-indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.combo_timesheet = QComboBox()
        layout.addWidget(self.combo_timesheet)

        button_row = QHBoxLayout()
        self.btn_sfoglia = QPushButton("📁 Sfoglia...")
        self.btn_sfoglia.setObjectName("btn-sfoglia")
        self.btn_sfoglia.clicked.connect(self._sfoglia)
        self.btn_genera = QPushButton("📐 Genera")
        self.btn_genera.setObjectName("btn-genera")
        self.btn_genera.clicked.connect(self._genera)
        button_row.addWidget(self.btn_sfoglia)
        button_row.addStretch()
        button_row.addWidget(self.btn_genera)
        layout.addLayout(button_row)

        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget, stretch=1)

    def refresh(self) -> None:
        self.config = getattr(self.window(), "config", None)
        self.combo_timesheet.clear()

        yaml_files = sorted(TIMESHEET_FOLDER.glob("*.yaml")) if TIMESHEET_FOLDER.exists() else []
        if not yaml_files:
            self.info_label.setText(
                f"Nessun file YAML trovato in '{TIMESHEET_FOLDER}'. "
                "Crea un file di configurazione (vedi "
                "templates/timesheet_progetto_template.yaml) o usa 'Sfoglia...'."
            )
        else:
            self.info_label.setText("Seleziona un timesheet di progetto:")
            for f in yaml_files:
                self.combo_timesheet.addItem(f.name, str(f))

    def _sfoglia(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(self, "Seleziona timesheet YAML", "", "YAML (*.yaml *.yml)")
        if not path_str:
            return
        path = Path(path_str)
        self.combo_timesheet.addItem(path.name, str(path))
        self.combo_timesheet.setCurrentIndex(self.combo_timesheet.count() - 1)

    def _genera(self) -> None:
        if self.combo_timesheet.count() == 0:
            self.log_widget.appendPlainText("Seleziona un file YAML.")
            return

        ts_path = Path(self.combo_timesheet.currentData())
        try:
            ts_config = esegui_timesheet_progetto(self.config, ts_path)
            self.log_widget.appendPlainText(f"Timesheet '{ts_config.nome}' generato in {self.config.output_folder}")
        except Exception as e:
            log.error(f"Errore nella generazione del timesheet: {e}")
            self.log_widget.appendPlainText(f"Errore: {e}")

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_dashboard"):
            window.show_dashboard()
