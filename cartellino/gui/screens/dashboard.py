"""Dashboard screen (Fase 3 TODO_gui.md), mirror di ``cartellino/tui/screens/dashboard.py``.

Sola lettura + navigazione. Le sezioni informative e i loro calcoli sono
riusati identici dalla TUI (stesso layer di dominio: `Cartellino`,
`OreEccedenti`, `Statistiche`, `somma_ore_per_codici`). I pulsanti di
navigazione sono tutti collegati (cablati da `MainWindow` una volta scritte le
rispettive schermate, Fasi 5-9).

Il testo delle sezioni (`sections_label`) è avvolto in un `QScrollArea`
separato dalla riga dei pulsanti (Fase 14, QA): un anno con molti riposi
compensativi può produrre un testo lungo, e senza scroll la finestra veniva
costretta a crescere oltre lo schermo pur di mostrare tutto — i pulsanti
restano invece sempre visibili, non scorrono via col testo.
"""

import logging
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cartellino.cartellino import Cartellino
from cartellino.gui.workers import UpdateCheckWorker
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_helpers import calcola_saldo_minuti, somma_ore_per_codici
from cartellino.statistiche import Statistiche
from cartellino.update_checker import ReleaseInfo

log = logging.getLogger(__name__)


def _categorizza_riposo(riposo) -> tuple[str, str]:
    """Categorizzazione dei riposi compensativi per la dashboard, vedi TODO.md
    § "Note tecniche sulla categorizzazione dei riposi compensativi"."""
    if riposo.data:
        return "USATO", f"il {riposo.data}"
    if riposo.ore_mancanti() <= timedelta(0):
        confermato = all(o.stato == "ELAB P1" for o in riposo.ore_inserite)
        stato = "COMPLETO E CONFERMATO" if confermato else "COMPLETO NON CONFERMATO"
        return stato, ""
    mancanti = riposo.ore_mancanti()
    ore = mancanti.seconds // 3600
    minuti = (mancanti.seconds // 60) % 60
    return "DA COMPLETARE", f"mancano {ore}:{minuti:02}"


class DashboardScreen(QWidget):
    request_aggiorna_cartellino = Signal()
    """Mirror di ``action_aggiorna_cartellino``: la MainWindow ascolta e mostra
    l'Update screen (già instradabile, anche se ancora placeholder — Fase 4)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = None
        self._update_worker: UpdateCheckWorker | None = None

        self._layout = QVBoxLayout(self)
        self.sections_label = QLabel("")
        self.sections_label.setWordWrap(True)
        self.sections_label.setTextFormat(Qt.TextFormat.RichText)
        self.sections_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sections_label)
        self._layout.addWidget(scroll, stretch=1)

        buttons = QGridLayout()
        self.btn_aggiorna = QPushButton("Aggiorna cartellino")
        self.btn_aggiorna.clicked.connect(self.request_aggiorna_cartellino.emit)
        self.btn_report = QPushButton("Genera report")
        self.btn_timesheet = QPushButton("Genera timesheet")
        self.btn_statistiche = QPushButton("Statistiche")
        self.btn_impostazioni = QPushButton("Impostazioni")
        self.btn_controlla_aggiornamenti = QPushButton("Controlla aggiornamenti")
        self.btn_controlla_aggiornamenti.clicked.connect(self._controlla_aggiornamenti)

        for btn in (self.btn_report, self.btn_timesheet, self.btn_statistiche, self.btn_impostazioni):
            btn.setEnabled(False)
            btn.setToolTip("Non ancora implementato in GUI (vedi TODO_gui.md)")

        buttons.addWidget(self.btn_aggiorna, 0, 0)
        buttons.addWidget(self.btn_report, 0, 1)
        buttons.addWidget(self.btn_timesheet, 0, 2)
        buttons.addWidget(self.btn_statistiche, 1, 0)
        buttons.addWidget(self.btn_impostazioni, 1, 1)
        buttons.addWidget(self.btn_controlla_aggiornamenti, 1, 2)
        self._layout.addLayout(buttons)
        self._layout.addStretch()

    def refresh(self) -> None:
        """Ricostruisce il contenuto informativo. Mirror di `on_screen_resume` della
        TUI: qui basta riassegnare il testo, non serve ricostruire i widget."""
        window = self.window()
        config = getattr(window, "config", None)
        self.config = config
        self.sections_label.setText(self._build_html(config))

    # ------------------------------------------------------------------

    def _build_html(self, config) -> str:
        if config is None:
            return "Configurazione non disponibile."

        feather_path = config.input_folder / "cartellino.feather"
        if not feather_path.exists():
            return (
                f"Nessun cartellino scaricato ancora per l'anno {config.current_year}.<br><br>"
                "Premi 'Aggiorna cartellino' per avviare il primo download."
            )

        try:
            cartellino = Cartellino.from_config(config)
        except Exception as e:
            return f"<span style='color:red'>Errore nella lettura del cartellino: {e}</span>"

        now = datetime.now()
        sezioni = [
            ("Eccezioni/saldo mese", lambda: self._sezione_eccezioni(cartellino, config, now)),
            ("Saldo mensile", lambda: self._sezione_saldo(cartellino, config, now)),
            ("Riposi compensativi", lambda: self._sezione_riposi(cartellino, config)),
            ("Ferie/PMF", lambda: self._sezione_ferie_pmf(cartellino)),
            ("Ticket da ricevere", lambda: self._sezione_ticket(cartellino, config)),
            ("Ultimo aggiornamento", lambda: self._sezione_aggiornamento(feather_path)),
        ]

        blocchi = []
        for nome, build in sezioni:
            try:
                blocchi.append(build())
            except Exception as e:
                log.warning(f"Errore nella sezione dashboard '{nome}': {e}")
                blocchi.append(f"<b>{nome}</b><br><span style='color:red'>Errore: {e}</span>")
        return "<br><br>".join(blocchi)

    @staticmethod
    def _sezione_eccezioni(cartellino: Cartellino, config, now: datetime) -> str:
        codici = config.dashboard_exception_codes
        df = somma_ore_per_codici(cartellino.df, codici)
        df = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
        if df.empty:
            righe = "nessuna"
        else:
            righe = "<br>".join(
                f"&nbsp;&nbsp;- {row['date'].strftime('%d/%m/%Y')}: {row['Codice']} {row['ore']:02}:{row['minuti']:02}"
                for _, row in df.iterrows()
            )
        return f"<b>Eccezioni del mese ({', '.join(codici)})</b><br>{righe}"

    @staticmethod
    def _sezione_saldo(cartellino: Cartellino, config, now: datetime) -> str:
        codici = config.dashboard_balance_codes
        df = cartellino.df[
            (cartellino.df["date"].dt.month == now.month) & (cartellino.df["date"].dt.year == now.year)
        ]
        totale_minuti = calcola_saldo_minuti(df, codici)
        ore, minuti = divmod(abs(totale_minuti), 60)
        if totale_minuti < 0:
            colore, segno = "red", "-"
        elif totale_minuti > 0:
            colore, segno = "green", ""
        else:
            colore, segno = "blue", ""
        return (
            f"<b>Saldo ore del mese ({', '.join(codici)})</b><br>"
            f"&nbsp;&nbsp;<span style='color:{colore}'>{segno}{ore:02}:{minuti:02}</span>"
        )

    @staticmethod
    def _sezione_riposi(cartellino: Cartellino, config) -> str:
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=config.excluded_dates_file,
            current_year=config.current_year,
        )
        if config.min_date:
            riposi_usati = OreEccedenti.get_date_usate_from_src(
                src_df=cartellino.src, min_date=config.min_date
            )
        else:
            riposi_usati = OreEccedenti.get_date_usate_from_file(config.riposi_usati_file)

        riposi = oe_proc.raggruppa(riposi_usati)
        righe = []
        for riposo in riposi:
            stato, dettaglio = _categorizza_riposo(riposo)
            righe.append(f"&nbsp;&nbsp;- Riposo {riposo.id}: {stato}" + (f" ({dettaglio})" if dettaglio else ""))
        return "<b>Riposi compensativi</b><br>" + ("<br>".join(righe) if righe else "&nbsp;&nbsp;nessuno")

    @staticmethod
    def _sezione_ferie_pmf(cartellino: Cartellino) -> str:
        return (
            "<b>Ferie e permessi (anno corrente)</b><br>"
            f"&nbsp;&nbsp;Ferie usate: {len(cartellino.ferie)}<br>"
            f"&nbsp;&nbsp;Permessi gravi motivi familiari usati: {len(cartellino.permesso_gravi_motivi)}"
        )

    @staticmethod
    def _sezione_ticket(cartellino: Cartellino, config) -> str:
        sheets = Statistiche(cartellino=cartellino, config=config).calcola()
        ticket_df = sheets.get("ticket")
        if ticket_df is None:
            return (
                "<b>Ticket da ricevere</b><br>"
                "&nbsp;&nbsp;data ticket non impostata (Impostazioni → Buoni pasto accreditati fino al)"
            )
        da_ricevere = ticket_df[ticket_df["Da ricevere"] == 1]
        if da_ricevere.empty:
            return "<b>Ticket da ricevere</b><br>&nbsp;&nbsp;nessuno"
        valore = da_ricevere["Valore da ricevere"].sum()
        return f"<b>Ticket da ricevere</b><br>&nbsp;&nbsp;{len(da_ricevere)} (valore: {valore:.2f}€)"

    @staticmethod
    def _sezione_aggiornamento(feather_path) -> str:
        mtime = datetime.fromtimestamp(feather_path.stat().st_mtime)
        return f"<b>Ultimo aggiornamento</b><br>&nbsp;&nbsp;{mtime.strftime('%d/%m/%Y %H:%M')}"

    # ------------------------------------------------------------------

    def _controlla_aggiornamenti(self) -> None:
        from cartellino.gui.app import _app_version

        self.btn_controlla_aggiornamenti.setEnabled(False)
        self._update_worker = UpdateCheckWorker(_app_version(), self)
        self._update_worker.finished_ok.connect(self._mostra_esito_aggiornamento)
        self._update_worker.failed.connect(self._mostra_errore_aggiornamento)
        self._update_worker.start()

    def _mostra_esito_aggiornamento(self, release: ReleaseInfo | None) -> None:
        from cartellino.gui.app import _app_version
        from cartellino.gui.screens.app_update import AppUpdateDialog

        self.btn_controlla_aggiornamenti.setEnabled(True)
        AppUpdateDialog(_app_version(), release, self).exec()

    def _mostra_errore_aggiornamento(self, errore: str) -> None:
        self.btn_controlla_aggiornamenti.setEnabled(True)
        log.warning(f"Controllo aggiornamenti fallito: {errore}")
        QMessageBox.warning(self, "Controllo aggiornamenti", f"Controllo fallito: {errore}")
