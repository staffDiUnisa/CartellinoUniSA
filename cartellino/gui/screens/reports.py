"""Reports screen (Fase 5 TODO_gui.md), mirror di ``cartellino/tui/screens/reports.py``.

Report on-demand: nessuna scrittura automatica, un'azione per report, nel
formato scelto in Impostazioni (`Config.export_format`). Le chiamate sono
sincrone anche nella TUI (nessun worker thread): stessa scelta qui, coerente
col piano ("miglioria opzionale, non requisito").
"""

import logging

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cartellino.cartellino import Cartellino
from cartellino.credito_ore import CreditoOre
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_giornaliere import OreGiornaliere
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)


class ReportsScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = None

        layout = QVBoxLayout(self)
        self.formato_label = QLabel("")
        layout.addWidget(self.formato_label)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("⬅️ Indietro")
        self.btn_indietro.setObjectName("btn-indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        button_row = QHBoxLayout()
        self.btn_riposo = QPushButton("🛌 Riposo compensativo")
        self.btn_riposo.setObjectName("btn-riposo")
        self.btn_riposo.clicked.connect(self._genera_riposo_compensativo)
        self.btn_credito = QPushButton("🧮 Credito ore")
        self.btn_credito.setObjectName("btn-credito")
        self.btn_credito.clicked.connect(self._genera_credito_ore)
        self.btn_statistiche = QPushButton("📊 Statistiche")
        self.btn_statistiche.setObjectName("btn-statistiche")
        self.btn_statistiche.clicked.connect(self._genera_statistiche)
        self.btn_ore_giornaliere = QPushButton("🕓 Ore giornaliere")
        self.btn_ore_giornaliere.setObjectName("btn-ore-giornaliere")
        self.btn_ore_giornaliere.clicked.connect(self._genera_ore_giornaliere)
        for btn in (self.btn_riposo, self.btn_credito, self.btn_statistiche, self.btn_ore_giornaliere):
            button_row.addWidget(btn)
        layout.addLayout(button_row)

        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget, stretch=1)

    def refresh(self) -> None:
        self.config = getattr(self.window(), "config", None)
        if self.config is not None:
            self.formato_label.setText(
                f"Formato export: {self.config.export_format} (modificabile in Impostazioni)"
            )

    def _cartellino(self) -> Cartellino:
        return Cartellino.from_config(self.config)

    def _riposi_usati(self, cartellino: Cartellino) -> list[str]:
        cfg = self.config
        if cfg.min_date:
            return OreEccedenti.get_date_usate_from_src(src_df=cartellino.src, min_date=cfg.min_date)
        return OreEccedenti.get_date_usate_from_file(cfg.riposi_usati_file)

    def _run(self, azione) -> None:
        try:
            azione()
        except Exception as e:
            log.error(f"Errore nella generazione del report: {e}")
            self.log_widget.appendPlainText(f"Errore: {e}")

    def _genera_riposo_compensativo(self) -> None:
        self._run(self._do_genera_riposo_compensativo)

    def _do_genera_riposo_compensativo(self) -> None:
        cfg = self.config
        cartellino = self._cartellino()
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )
        riposi = oe_proc.raggruppa(self._riposi_usati(cartellino))
        oe_proc.salva_dettaglio(cfg.output_folder / "riposo_compensativo.xlsx", fmt=cfg.export_format)
        oe_proc.salva_testo(riposi, cfg.output_folder / "riposi_compensativi.txt")
        self.log_widget.appendPlainText(f"Riposo compensativo generato in {cfg.output_folder}")

    def _genera_credito_ore(self) -> None:
        self._run(self._do_genera_credito_ore)

    def _do_genera_credito_ore(self) -> None:
        cfg = self.config
        cartellino = self._cartellino()
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )
        oe_df = oe_proc.elabora()
        CreditoOre(
            oo_diu=cartellino.oo_diu, oe=oe_df, excluded_dates_file=cfg.excluded_dates_file
        ).salva(cfg.output_folder / "credito_ore.xlsx", fmt=cfg.export_format)
        self.log_widget.appendPlainText(f"Credito ore generato in {cfg.output_folder}")

    def _genera_statistiche(self) -> None:
        self._run(self._do_genera_statistiche)

    def _do_genera_statistiche(self) -> None:
        cfg = self.config
        cartellino = self._cartellino()
        Statistiche(cartellino=cartellino, config=cfg).salva(
            cfg.output_folder / "statistiche.xlsx", fmt=cfg.export_format
        )
        self.log_widget.appendPlainText(f"Statistiche generate in {cfg.output_folder}")

    def _genera_ore_giornaliere(self) -> None:
        self._run(self._do_genera_ore_giornaliere)

    def _do_genera_ore_giornaliere(self) -> None:
        cfg = self.config
        cartellino = self._cartellino()
        OreGiornaliere(oo_diu=cartellino.oo_diu).salva(
            cfg.output_folder / "ore_giornaliere.xlsx", fmt=cfg.export_format
        )
        self.log_widget.appendPlainText(f"Ore giornaliere generate in {cfg.output_folder}")

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_dashboard"):
            window.show_dashboard()
