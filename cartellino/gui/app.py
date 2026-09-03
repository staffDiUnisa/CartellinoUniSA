"""Applicazione GUI desktop (PySide6), mirror di ``cartellino/tui/app.py``.

Fase 1 (TODO_gui.md): scaffolding — ``QStackedWidget`` per le schermate
primarie e routing iniziale (Onboarding/Update/Dashboard), mirror di
``CartellinoApp.reload_config_and_route()``. Le schermate vere e proprie
(contenuto, non solo il placeholder) arrivano nelle fasi successive: questa
fase fissa solo il pattern di navigazione, perché un errore di design qui si
propagherebbe a tutte le schermate seguenti (vedi rischio principale della
Fase 1 nel piano).
"""

import logging
import sys
import tomllib
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from cartellino.config import Config
from cartellino.gui.screens.app_update import AppUpdateDialog
from cartellino.gui.screens.dashboard import DashboardScreen
from cartellino.gui.screens.date_escluse import DateEscluseScreen
from cartellino.gui.screens.onboarding import OnboardingScreen
from cartellino.gui.screens.reports import ReportsScreen
from cartellino.gui.screens.riposo_richiesto import RiposoRichiestoScreen
from cartellino.gui.screens.settings import SettingsScreen
from cartellino.gui.screens.statistiche import StatisticheScreen
from cartellino.gui.screens.timesheet import TimesheetScreen
from cartellino.gui.screens.update import UpdateScreen
from cartellino.gui.workers import UpdateCheckWorker

log = logging.getLogger(__name__)

DATA_FOLDER = Path("data/v2")


def _bundle_base() -> Path:
    """Cartella da cui leggere risorse bundled (pyproject.toml, style.qss) quando
    "frozen". Stesso schema di ``cartellino/tui/app.py::_bundle_base``."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def _app_version() -> str:
    pyproject_path = _bundle_base() / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (OSError, KeyError):
        return "dev"


def _load_stylesheet() -> str:
    qss_path = Path(__file__).resolve().parent / "style.qss"
    try:
        return qss_path.read_text(encoding="utf-8")
    except OSError:
        return ""


class MainWindow(QMainWindow):
    """Finestra principale/router, mirror di ``CartellinoApp``.

    A differenza della TUI (che usa uno screen stack di Textual, con push/pop
    per i modali), qui le schermate primarie (Onboarding/Update/Dashboard)
    vivono in un unico ``QStackedWidget`` e la navigazione tra loro avviene
    cambiando pagina, non impilando finestre. I popup con valore di ritorno
    (Credentials, Fase 10) useranno invece ``QDialog`` modali separati, non
    lo stack — stessa distinzione descritta nel piano.
    """

    def __init__(self, data_folder: Path = DATA_FOLDER) -> None:
        super().__init__()
        self.data_folder = data_folder
        self.config: Config | None = None
        self._startup_update_worker: UpdateCheckWorker | None = None

        self.setWindowTitle(f"Cartellino UniSA v{_app_version()}")
        self.resize(900, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.onboarding_screen = OnboardingScreen()
        self.onboarding_screen.saved.connect(self.reload_config_and_route)
        self.update_screen = UpdateScreen()
        self.update_screen.data_folder = self.data_folder
        self.dashboard_screen = DashboardScreen()
        self.dashboard_screen.request_aggiorna_cartellino.connect(
            lambda: self.stack.setCurrentWidget(self.update_screen)
        )
        self.reports_screen = ReportsScreen()
        self.dashboard_screen.btn_report.setEnabled(True)
        self.dashboard_screen.btn_report.setToolTip("")
        self.dashboard_screen.btn_report.clicked.connect(self.show_reports)
        self.timesheet_screen = TimesheetScreen()
        self.dashboard_screen.btn_timesheet.setEnabled(True)
        self.dashboard_screen.btn_timesheet.setToolTip("")
        self.dashboard_screen.btn_timesheet.clicked.connect(self.show_timesheet)
        self.statistiche_screen = StatisticheScreen()
        self.dashboard_screen.btn_statistiche.setEnabled(True)
        self.dashboard_screen.btn_statistiche.setToolTip("")
        self.dashboard_screen.btn_statistiche.clicked.connect(self.show_statistiche)
        self.settings_screen = SettingsScreen()
        self.dashboard_screen.btn_impostazioni.setEnabled(True)
        self.dashboard_screen.btn_impostazioni.setToolTip("")
        self.dashboard_screen.btn_impostazioni.clicked.connect(self.show_settings)
        self.date_escluse_screen = DateEscluseScreen()
        self.settings_screen.btn_date_escluse.setEnabled(True)
        self.settings_screen.btn_date_escluse.setToolTip("")
        self.settings_screen.btn_date_escluse.clicked.connect(self.show_date_escluse)
        self.riposo_richiesto_screen = RiposoRichiestoScreen()
        for screen in (
            self.onboarding_screen,
            self.update_screen,
            self.dashboard_screen,
            self.reports_screen,
            self.timesheet_screen,
            self.statistiche_screen,
            self.settings_screen,
            self.date_escluse_screen,
            self.riposo_richiesto_screen,
        ):
            self.stack.addWidget(screen)

        self.reload_config_and_route()

    def reload_config_and_route(self) -> None:
        """Ricarica `Config` da disco e mostra la schermata iniziale corretta.

        Mirror di ``CartellinoApp.reload_config_and_route``: stessa logica di
        instradamento (Onboarding se manca `config.toml`, Update se manca
        ancora `cartellino.feather` per la cartella dati configurata,
        altrimenti Dashboard), riusata così com'è dal layer di dominio senza
        modifiche.
        """
        try:
            config = Config.load(data_folder=self.data_folder)
        except Exception:
            config = None

        self.config = config

        if config is None:
            self.stack.setCurrentWidget(self.onboarding_screen)
        elif not (config.input_folder / "cartellino.feather").exists():
            self.stack.setCurrentWidget(self.update_screen)
        else:
            self.dashboard_screen.refresh()
            self.stack.setCurrentWidget(self.dashboard_screen)
            self._controlla_aggiornamenti_avvio()

    def _controlla_aggiornamenti_avvio(self) -> None:
        """Mirror di `CartellinoApp._controlla_aggiornamenti_avvio`: controllo
        automatico all'avvio (Fase 11), solo se non è il primo avvio/onboarding
        e solo se `UserConfig.check_updates_on_startup` è vero. Fallisce
        silenziosamente (nessuna notifica) se la rete non è disponibile, per
        non degradare l'esperienza di avvio offline — stesso comportamento
        della TUI."""
        from cartellino.user_config import UserConfig

        user_config = UserConfig.load()
        if user_config is None or not user_config.check_updates_on_startup:
            return
        self._startup_update_worker = UpdateCheckWorker(_app_version(), self)
        self._startup_update_worker.finished_ok.connect(self._mostra_aggiornamento_disponibile)
        self._startup_update_worker.failed.connect(
            lambda errore: log.warning(f"Controllo aggiornamenti all'avvio fallito: {errore}")
        )
        self._startup_update_worker.start()

    def _mostra_aggiornamento_disponibile(self, release) -> None:
        if release is not None:
            AppUpdateDialog(_app_version(), release, self).exec()

    def show_dashboard(self) -> None:
        """Mirror di `self.app.pop_screen()` verso la Dashboard: usato sia da
        `UpdateScreen` (Indietro o fine download, con o senza successo — in
        "primo avvio" senza successo può mostrare ancora il messaggio "nessun
        cartellino scaricato") sia da `ReportsScreen` (Indietro)."""
        self.dashboard_screen.refresh()
        self.stack.setCurrentWidget(self.dashboard_screen)

    def show_reports(self) -> None:
        self.reports_screen.refresh()
        self.stack.setCurrentWidget(self.reports_screen)

    def show_timesheet(self) -> None:
        self.timesheet_screen.refresh()
        self.stack.setCurrentWidget(self.timesheet_screen)

    def show_statistiche(self) -> None:
        self.statistiche_screen.refresh()
        self.stack.setCurrentWidget(self.statistiche_screen)

    def show_settings(self) -> None:
        self.settings_screen.refresh()
        self.stack.setCurrentWidget(self.settings_screen)

    def show_date_escluse(self) -> None:
        self.date_escluse_screen.refresh()
        self.stack.setCurrentWidget(self.date_escluse_screen)

    def show_riposo_richiesto(self) -> None:
        self.riposo_richiesto_screen.refresh()
        self.stack.setCurrentWidget(self.riposo_richiesto_screen)

    def closeEvent(self, event) -> None:
        """Conferma prima di chiudere (issue #9): copre in modo uniforme la X
        della finestra, Alt+F4 e Cmd+Q, non solo il pulsante "Esci" della
        Dashboard (che richiama `self.close()`, innescando questo stesso
        metodo — nessuna logica di conferma duplicata)."""
        risposta = QMessageBox.question(
            self,
            "Esci",
            "Vuoi davvero uscire da CartellinoUniSA?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if risposta != QMessageBox.StandardButton.Yes:
            event.ignore()
        else:
            event.accept()


def run(data_folder: Path = DATA_FOLDER) -> None:
    data_folder.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyleSheet(_load_stylesheet())
    window = MainWindow(data_folder=data_folder)
    window.show()
    sys.exit(app.exec())
