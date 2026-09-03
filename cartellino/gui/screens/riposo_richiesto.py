"""Schermata "Riposo compensativo richiesto" (issue #7, vedi
TODO_riposo_richiesto.md Fase 5).

Solo GUI, come richiesto nell'issue. Mostra le richieste pendenti (PDF già
generati per un riposo compensativo completo, in attesa dell'uso confermato
via `riposi_usati.txt`/`SRC` — meccanismo esistente, non toccato) e un solo
pulsante "Richiedi il prossimo disponibile", coerente con l'uso rigorosamente
sequenziale deciso con l'utente (nessun selettore). Annullare una richiesta
tronca anche tutte quelle successive già in coda, incluso l'eliminazione dei
PDF già generati (`cartellino.riposo_richiesto.annulla_richiesta_da`).
"""

import logging
from pathlib import Path

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.pdf_riposo import RiposoPdfError, genera_pdf_richiesta
from cartellino.riposo_richiesto import (
    RichiestaRiposo,
    annulla_richiesta_da,
    applica_richieste,
    carica_richieste,
    prossimo_riposo_disponibile,
    salva_richieste,
)
log = logging.getLogger(__name__)


class RichiestaRiposoDialog(QDialog):
    """Mirror di `CredentialsDialog`: singolo campo data richiesta (DD-MM-YYYY)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Richiedi riposo compensativo")
        self.data_richiesta: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Data per cui richiedere il riposo compensativo"))
        self.input_data = QDateEdit()
        self.input_data.setCalendarPopup(True)
        self.input_data.setDisplayFormat("dd-MM-yyyy")
        self.input_data.setDate(QDate.currentDate())
        layout.addWidget(self.input_data)

        layout.addStretch()
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.btn_annulla = QPushButton("✖️ Annulla")
        self.btn_annulla.setObjectName("btn-annulla")
        self.btn_annulla.clicked.connect(self.reject)
        self.btn_salva = QPushButton("🧾 Richiedi")
        self.btn_salva.setObjectName("btn-richiedi-conferma")
        self.btn_salva.clicked.connect(self._conferma)
        button_row.addWidget(self.btn_annulla)
        button_row.addWidget(self.btn_salva)
        layout.addLayout(button_row)

    def _conferma(self) -> None:
        self.data_richiesta = self.input_data.date().toString("dd-MM-yyyy")
        self.accept()


class RiposoRichiestoScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config: Config | None = None
        self._prossimo_riposo = None

        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("⬅️ Indietro")
        self.btn_indietro.setObjectName("btn-indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Data richiesta", "PDF", "", ""])
        # Columns che contengono solo pulsanti (nessun QTableWidgetItem) non
        # vengono dimensionate correttamente da un `resizeColumnsToContents()`
        # una tantum (calcolato prima che i cell widget abbiano una geometria
        # stabile) — risultato: colonne troppo strette con i pulsanti
        # sovrapposti visivamente. ResizeToContents sull'header le ridimensiona
        # in continuo in base al sizeHint reale dei widget, non solo del testo.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # L'ultima colonna (pulsante "Annulla") si allarga per riempire lo
        # spazio residuo invece di restare tagliata al bordo destro della
        # tabella quando la finestra è più larga del contenuto minimo.
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)

        self.prossimo_label = QLabel("")
        layout.addWidget(self.prossimo_label)

        azioni_row = QHBoxLayout()
        self.btn_richiedi = QPushButton("🧾 Richiedi il prossimo disponibile")
        self.btn_richiedi.setObjectName("btn-richiedi")
        self.btn_richiedi.setEnabled(False)
        self.btn_richiedi.clicked.connect(self._richiedi_prossimo)
        azioni_row.addWidget(self.btn_richiedi)
        azioni_row.addStretch()
        layout.addLayout(azioni_row)

        self.errore_label = QLabel("")
        self.errore_label.setStyleSheet("color: red;")
        layout.addWidget(self.errore_label)

    def refresh(self) -> None:
        self.config = getattr(self.window(), "config", None)
        self.errore_label.setText("")
        self._aggiorna()

    # ------------------------------------------------------------------

    def _riposi(self) -> list:
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
        return oe_proc.raggruppa(riposi_usati)

    def _output_folder(self) -> Path:
        return self.config.output_folder / "richieste_riposo"

    def _aggiorna(self) -> None:
        richieste = carica_richieste(self.config.riposi_richiesti_file)
        self.table.setRowCount(len(richieste))
        for i, richiesta in enumerate(richieste):
            item_data = QTableWidgetItem(richiesta.data_richiesta)
            self.table.setItem(i, 0, item_data)
            item_pdf = QTableWidgetItem(Path(richiesta.pdf_path).name)
            item_pdf.setToolTip(richiesta.pdf_path)
            self.table.setItem(i, 1, item_pdf)
            btn_scarica = QPushButton("🧾 Scarica PDF")
            btn_scarica.setObjectName("btn-scarica")
            btn_scarica.clicked.connect(lambda _checked=False, p=richiesta.pdf_path: self._scarica_pdf(p))
            self.table.setCellWidget(i, 2, btn_scarica)
            btn_annulla = QPushButton("✖️ Annulla (e successive)")
            btn_annulla.setObjectName("btn-annulla-successive")
            btn_annulla.clicked.connect(lambda _checked=False, idx=i: self._annulla_da(idx))
            self.table.setCellWidget(i, 3, btn_annulla)

        try:
            riposi = self._riposi()
        except Exception as e:
            log.warning(f"Errore nel caricamento dei riposi compensativi: {e}")
            self.info_label.setText(f"Errore nel caricamento dei riposi compensativi: {e}")
            self.btn_richiedi.setEnabled(False)
            return

        riposi_aggiornati = applica_richieste(riposi, richieste)
        prossimo = prossimo_riposo_disponibile(riposi_aggiornati)
        self.info_label.setText(f"Richieste pendenti: {len(richieste)}")
        if prossimo is None:
            self.prossimo_label.setText("Nessun riposo compensativo completo disponibile da richiedere.")
            self.btn_richiedi.setEnabled(False)
        else:
            self.prossimo_label.setText(
                f"Prossimo disponibile: riposo compensativo {prossimo.id} "
                f"({len(prossimo.ore_inserite)} giornate contribuenti)."
            )
            self.btn_richiedi.setEnabled(True)
        self._prossimo_riposo = prossimo

    def _richiedi_prossimo(self) -> None:
        self.errore_label.setText("")
        if self._prossimo_riposo is None:
            return

        if not self.config.template_riposo_file.exists():
            QMessageBox.warning(
                self,
                "Riposo compensativo",
                "Carica prima il template PDF in Impostazioni (\"Template PDF richiesta "
                "riposo compensativo\").",
            )
            return

        dialog = RichiestaRiposoDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            pdf_path = genera_pdf_richiesta(
                template_path=self.config.template_riposo_file,
                riposo=self._prossimo_riposo,
                data_richiesta=dialog.data_richiesta,
                current_year=self.config.current_year,
                output_folder=self._output_folder(),
            )
        except RiposoPdfError as e:
            self.errore_label.setText(str(e))
            return

        richieste = carica_richieste(self.config.riposi_richiesti_file)
        richieste.append(RichiestaRiposo(data_richiesta=dialog.data_richiesta, pdf_path=str(pdf_path)))
        salva_richieste(self.config.riposi_richiesti_file, richieste)
        log.info(f"Richiesta riposo compensativo {self._prossimo_riposo.id} generata: '{pdf_path}'")
        self._aggiorna()

    def _scarica_pdf(self, pdf_path: str) -> None:
        path = Path(pdf_path)
        if not path.exists():
            QMessageBox.warning(self, "Riposo compensativo", f"Il PDF '{path}' non esiste più.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _annulla_da(self, indice: int) -> None:
        risposta = QMessageBox.question(
            self,
            "Annulla richiesta",
            "Annullare questa richiesta eliminerà anche tutte quelle successive già in "
            "coda, insieme ai relativi PDF già generati. Continuare?",
        )
        if risposta != QMessageBox.StandardButton.Yes:
            return
        annulla_richiesta_da(self.config.riposi_richiesti_file, indice)
        log.info(f"Richieste riposo compensativo troncate dall'indice {indice}.")
        self._aggiorna()

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_statistiche"):
            window.show_statistiche()
