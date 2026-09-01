"""Date escluse screen (Fase 9 TODO_gui.md), mirror di
``cartellino/tui/screens/date_escluse.py``.

Gestione di `date_escluse.txt`: una riga `DD-MM-YYYY` esclude l'intera
giornata dal calcolo delle ore eccedenti (OE-DIU); una riga
`DD-MM-YYYY HH:MM` sottrae solo quell'orario dalle ore eccedenti del giorno
(vedi `OreEccedenti._elabora`/CLAUDE.md). Stesso formato file, `QTableWidget`
con add/remove riga al posto della lista di `Horizontal` Textual.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)

_DATA_REGEX = r"\d{0,2}-?\d{0,2}-?\d{0,4}"
_ORA_REGEX = r"\d{0,2}:?\d{0,2}"


@dataclass
class _VoceEsclusa:
    data: str  # DD-MM-YYYY
    ora: str | None  # HH:MM, oppure None per l'esclusione dell'intera giornata

    def to_line(self) -> str:
        return f"{self.data} {self.ora}" if self.ora else self.data


def _parse_riga(riga: str) -> "_VoceEsclusa | None":
    riga = riga.strip()
    if not riga:
        return None
    parti = riga.split(" ", 1)
    if len(parti) == 2:
        return _VoceEsclusa(data=parti[0], ora=parti[1])
    return _VoceEsclusa(data=parti[0], ora=None)


class DateEscluseScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = None

        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("Indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        layout.addWidget(
            QLabel(
                "Date da escludere (giornata intera) o orari da sottrarre dal calcolo "
                "delle ore eccedenti (OE-DIU)."
            )
        )

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Data", ""])
        self.table.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self.table, stretch=1)

        add_row = QHBoxLayout()
        self.input_nuova_data = QLineEdit()
        self.input_nuova_data.setPlaceholderText("DD-MM-YYYY")
        self.input_nuova_data.setValidator(QRegularExpressionValidator(_DATA_REGEX))
        self.input_nuova_ora = QLineEdit()
        self.input_nuova_ora.setPlaceholderText("HH:MM (opzionale)")
        self.input_nuova_ora.setValidator(QRegularExpressionValidator(_ORA_REGEX))
        self.btn_aggiungi = QPushButton("Aggiungi")
        self.btn_aggiungi.clicked.connect(self._aggiungi)
        add_row.addWidget(self.input_nuova_data)
        add_row.addWidget(self.input_nuova_ora)
        add_row.addWidget(self.btn_aggiungi)
        layout.addLayout(add_row)

        self.errore_label = QLabel("")
        self.errore_label.setStyleSheet("color: red;")
        layout.addWidget(self.errore_label)

    def refresh(self) -> None:
        self.config = getattr(self.window(), "config", None)
        self.errore_label.setText("")
        self._aggiorna_lista()

    # ------------------------------------------------------------------

    def _file(self) -> Path:
        return self.config.excluded_dates_file

    def _leggi(self) -> list[_VoceEsclusa]:
        voci = []
        for riga in self._file().read_text().splitlines():
            voce = _parse_riga(riga)
            if voce is not None:
                voci.append(voce)
        return voci

    def _scrivi(self, voci: list[_VoceEsclusa]) -> None:
        contenuto = "\n".join(v.to_line() for v in voci)
        self._file().write_text(contenuto + ("\n" if contenuto else ""))

    def _aggiorna_lista(self) -> None:
        voci = self._leggi()
        self.table.setRowCount(len(voci))
        for i, voce in enumerate(voci):
            testo = voce.data + (f" — sottrae {voce.ora}" if voce.ora else " — giornata intera")
            self.table.setItem(i, 0, QTableWidgetItem(testo))
            btn_rimuovi = QPushButton("Rimuovi")
            btn_rimuovi.clicked.connect(lambda _checked=False, idx=i: self._rimuovi(idx))
            self.table.setCellWidget(i, 1, btn_rimuovi)
        self.table.resizeColumnsToContents()

    # ------------------------------------------------------------------

    def _aggiungi(self) -> None:
        data_valore = self.input_nuova_data.text().strip()
        if not data_valore:
            self.errore_label.setText("Data non valida (formato DD-MM-YYYY).")
            return
        try:
            datetime.strptime(data_valore, "%d-%m-%Y")
        except ValueError:
            self.errore_label.setText("Data non valida.")
            return

        ora_valore = self.input_nuova_ora.text().strip()
        if ora_valore:
            try:
                datetime.strptime(ora_valore, "%H:%M")
            except ValueError:
                self.errore_label.setText("Orario non valido (formato HH:MM).")
                return

        nuova = _VoceEsclusa(data=data_valore, ora=ora_valore or None)
        voci = self._leggi()
        voci.append(nuova)
        self._scrivi(voci)
        log.info(f"Aggiunta data esclusa: {nuova.to_line()}")

        self.input_nuova_data.setText("")
        self.input_nuova_ora.setText("")
        self.errore_label.setText("")
        self._aggiorna_lista()

    def _rimuovi(self, indice: int) -> None:
        voci = self._leggi()
        if 0 <= indice < len(voci):
            rimossa = voci.pop(indice)
            self._scrivi(voci)
            log.info(f"Rimossa data esclusa: {rimossa.to_line()}")
        self._aggiorna_lista()

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_settings"):
            window.show_settings()
