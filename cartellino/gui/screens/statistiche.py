"""Statistiche screen (Fase 7 TODO_gui.md), mirror di ``cartellino/tui/screens/statistiche.py``.

Un pulsante per categoria (stesse 7 di `statistiche.xlsx`,
`Statistiche.calcola()`), abilitato solo se ci sono dati, che carica la
tabella corrispondente sotto. Un ottavo pulsante, "Riposo compensativo",
mostra un `QTextBrowser` in Markdown al posto della tabella (stesso motivo
della TUI: il contenuto non è tabulare).
"""

import logging

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)

# (chiave del foglio in Statistiche.calcola(), etichetta pulsante, id widget —
# stessi id della controparte TUI in cartellino/tui/screens/statistiche.py)
_CATEGORIE = [
    ("statistica_ticket", "🎫 Buoni pasto", "btn-stat-ticket"),
    ("ferie", "🏖️ Ferie", "btn-stat-ferie"),
    ("permessi_gravi_motivi", "📝 Permessi per motivi familiari", "btn-stat-pmf"),
    ("entrata_ritardo", "⏰ Entrata in ritardo", "btn-stat-erit"),
    ("straordinari", "⏱️ Straordinari", "btn-stat-straordinari"),
    ("visite_specialistiche", "🩺 Visite Specialistiche", "btn-stat-vsg"),
    ("malattia", "🤒 Malattia", "btn-stat-malattia"),
]


class _DataFrameTableModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None, parent=None) -> None:
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent=None) -> int:
        return len(self._df.index)

    def columnCount(self, parent=None) -> int:
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        return str(self._df.iat[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class StatisticheScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config: Config | None = None

        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("⬅️ Indietro")
        self.btn_indietro.setObjectName("btn-indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.info_label = QLabel("Seleziona una categoria (i pulsanti senza dati sono disabilitati).")
        layout.addWidget(self.info_label)

        self.buttons_grid = QGridLayout()
        layout.addLayout(self.buttons_grid)
        self._categoria_buttons: dict[str, QPushButton] = {}

        self.table_model = _DataFrameTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        layout.addWidget(self.table_view, stretch=1)

        self.riposi_viewer = QTextBrowser()
        self.riposi_viewer.hide()
        layout.addWidget(self.riposi_viewer, stretch=1)

        self.export_row = QHBoxLayout()
        self.btn_export_riposi = QPushButton("📤 Esporta riposi in txt")
        self.btn_export_riposi.setObjectName("btn-export-riposi")
        self.btn_export_riposi.clicked.connect(self._esporta_riposi)
        self.export_row.addWidget(self.btn_export_riposi)
        self.btn_riposo_richiesto = QPushButton("🧾 Richiedi riposo compensativo")
        self.btn_riposo_richiesto.setObjectName("btn-riposo-richiesto")
        self.btn_riposo_richiesto.clicked.connect(self._apri_riposo_richiesto)
        self.export_row.addWidget(self.btn_riposo_richiesto)
        self.export_row.addStretch()
        self._export_row_widget = QWidget()
        self._export_row_widget.setLayout(self.export_row)
        self._export_row_widget.hide()
        layout.addWidget(self._export_row_widget)

    def refresh(self) -> None:
        self.config = getattr(self.window(), "config", None)
        for i in reversed(range(self.buttons_grid.count())):
            self.buttons_grid.itemAt(i).widget().setParent(None)
        self._categoria_buttons.clear()

        try:
            sheets = self._calcola()
        except Exception as e:
            log.warning(f"Errore nel caricamento delle statistiche: {e}")
            self.info_label.setText(f"Errore nel caricamento delle statistiche: {e}")
            return

        self.info_label.setText("Seleziona una categoria (i pulsanti senza dati sono disabilitati).")
        col = 0
        for chiave, etichetta, id_bottone in _CATEGORIE:
            df = sheets.get(chiave)
            vuoto = df is None or df.empty
            btn = QPushButton(etichetta)
            btn.setObjectName(id_bottone)
            btn.setEnabled(not vuoto)
            btn.clicked.connect(lambda _checked=False, c=chiave: self._mostra(c))
            self.buttons_grid.addWidget(btn, col // 3, col % 3)
            self._categoria_buttons[chiave] = btn
            col += 1

        btn_riposi = QPushButton("🛌 Riposo compensativo")
        btn_riposi.setObjectName("btn-stat-riposi")
        btn_riposi.setEnabled(not self._senza_oe())
        btn_riposi.clicked.connect(self._mostra_riposi)
        self.buttons_grid.addWidget(btn_riposi, col // 3, col % 3)

        self.table_view.show()
        self.riposi_viewer.hide()
        self._export_row_widget.hide()

    def _calcola(self) -> dict:
        cartellino = Cartellino.from_config(self.config)
        return Statistiche(cartellino=cartellino, config=self.config).calcola()

    def _riposi(self) -> tuple[OreEccedenti, list]:
        """Stessa fonte dati di `riposi_compensativi.txt` (`OreEccedenti.raggruppa`,
        vedi `CartellinoProcessor.run`), condivisa tra la vista Markdown e l'export su file."""
        cartellino = Cartellino.from_config(self.config)
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=self.config.excluded_dates_file,
            current_year=self.config.current_year,
        )
        if self.config.min_date:
            riposi_usati = OreEccedenti.get_date_usate_from_src(
                src_df=cartellino.src, min_date=self.config.min_date
            )
        else:
            riposi_usati = OreEccedenti.get_date_usate_from_file(self.config.riposi_usati_file)
        riposi = oe_proc.raggruppa(riposi_usati)
        return oe_proc, riposi

    def _senza_oe(self) -> bool:
        try:
            return Cartellino.from_config(self.config).oe_diu.empty
        except Exception:
            return True

    def _mostra(self, chiave: str) -> None:
        self.riposi_viewer.hide()
        self._export_row_widget.hide()
        self.table_view.show()
        try:
            sheets = self._calcola()
        except Exception as e:
            log.error(f"Errore nel caricamento della statistica '{chiave}': {e}")
            return
        df = sheets.get(chiave)
        self.table_model.set_dataframe(df if df is not None else pd.DataFrame())

    def _mostra_riposi(self) -> None:
        self.table_view.hide()
        self.riposi_viewer.show()
        self._export_row_widget.show()
        try:
            oe_proc, riposi = self._riposi()
            markdown = oe_proc.riposi_markdown(riposi)
        except Exception as e:
            log.error(f"Errore nel caricamento dei riposi compensativi: {e}")
            markdown = f"Errore nel caricamento dei riposi compensativi: {e}"
        self.riposi_viewer.setMarkdown(markdown)

    def _esporta_riposi(self) -> None:
        output_file = self.config.output_folder / "riposi_compensativi.txt"
        try:
            oe_proc, riposi = self._riposi()
            oe_proc.salva_testo(riposi, output_file)
        except Exception as e:
            log.error(f"Errore nell'esportazione dei riposi compensativi: {e}")
            QMessageBox.warning(self, "Statistiche", f"Errore nell'esportazione: {e}")
            return
        QMessageBox.information(self, "Statistiche", f"Riposi compensativi esportati in {output_file}")

    def _apri_riposo_richiesto(self) -> None:
        window = self.window()
        if hasattr(window, "show_riposo_richiesto"):
            window.show_riposo_richiesto()

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_dashboard"):
            window.show_dashboard()
