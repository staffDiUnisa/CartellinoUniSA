import logging
import sys
import tomllib
from pathlib import Path

from textual import work
from textual.app import App
from textual.binding import Binding

from cartellino.config import Config

log = logging.getLogger(__name__)

DATA_FOLDER = Path("data/v2")


def _bundle_base() -> Path:
    """Cartella base per risolvere risorse (CSS, `pyproject.toml`) sia in sviluppo
    sia una volta impacchettati con PyInstaller (Fase 6 TODO.md).

    In sviluppo è la root del repo (calcolata da questo file); una volta
    "frozen", `sys._MEIPASS` è la cartella (temporanea o dell'eseguibile onedir)
    in cui PyInstaller estrae i `datas` dichiarati in `packaging/cartellino.spec`
    — che li piazza con gli stessi percorsi relativi usati qui.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def _app_version() -> str:
    """Legge la versione da `pyproject.toml` (il progetto ha `tool.uv.package = false`,
    quindi non è installato come pacchetto e `importlib.metadata.version()` non
    funzionerebbe)."""
    pyproject_path = _bundle_base() / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as fh:
            data = tomllib.load(fh)
        return data["project"]["version"]
    except Exception:
        return "dev"


class CartellinoApp(App):
    TITLE = "Cartellino UniSA"
    SUB_TITLE = f"v{_app_version()}"
    CSS_PATH = "app.tcss"
    # Necessario per PyInstaller: senza `_BASE_PATH` esplicito, Textual risolve
    # CSS_PATH con `inspect.getfile(CartellinoApp)`, che una volta "frozen" non
    # punta a un file reale su disco (il modulo vive nell'archivio PYZ bundled).
    # Textual fa `.parent` su `_BASE_PATH` (si aspetta il path di un *file*, come
    # ritornerebbe `inspect.getfile`), quindi va puntato dentro "tui/", non alla
    # cartella stessa.
    _BASE_PATH = str(_bundle_base() / "cartellino" / "tui" / "app.py")

    BINDINGS = [
        Binding("q", "quit", "Esci"),
    ]

    def __init__(self, data_folder: Path = DATA_FOLDER) -> None:
        super().__init__()
        self.data_folder = data_folder
        self.config: Config | None = None

    def on_mount(self) -> None:
        self._load_saved_theme()
        self.theme_changed_signal.subscribe(self, self._save_theme)
        self.reload_config_and_route()

    def _load_saved_theme(self) -> None:
        """Applica il tema salvato in `config.toml`, se presente (palette comandi -> Theme)."""
        from cartellino.user_config import UserConfig

        user_config = UserConfig.load()
        if user_config and user_config.theme and user_config.theme in self.available_themes:
            self.theme = user_config.theme

    def _save_theme(self, theme) -> None:
        """Persiste in `config.toml` il tema scelto dalla palette comandi (^p -> Theme).

        Nessun effetto prima del completamento dell'Onboarding (config.toml non esiste
        ancora, `UserConfig.load()` ritorna `None`): il tema verrà salvato a partire dalla
        prossima modifica una volta che `current_year` è noto.
        """
        from cartellino.user_config import UserConfig

        user_config = UserConfig.load()
        if user_config is None or user_config.theme == theme.name:
            return
        user_config.theme = theme.name
        user_config.save()

    def reload_config_and_route(self) -> None:
        """Ricarica `Config` da disco e mostra la schermata iniziale corretta.

        Usata sia all'avvio sia dopo che Onboarding/Settings hanno scritto una nuova
        configurazione, per ripartire da uno stato coerente.
        """
        from cartellino.tui.screens.dashboard import DashboardScreen
        from cartellino.tui.screens.onboarding import OnboardingScreen
        from cartellino.tui.screens.update import UpdateScreen

        try:
            config = Config.load(data_folder=self.data_folder)
        except Exception:
            config = None

        self.config = config

        while len(self.screen_stack) > 1:
            self.pop_screen()

        if config is None:
            self.push_screen(OnboardingScreen())
        elif not (config.input_folder / "cartellino.feather").exists():
            # Prima volta per questa cartella dati (nuova o appena cambiata in
            # Impostazioni): la cartella è già stata creata da Config.__post_init__,
            # si passa direttamente alla schermata di download invece di mostrare la
            # Dashboard vuota con un click in più.
            self.push_screen(DashboardScreen())
            self.push_screen(UpdateScreen())
        else:
            self.push_screen(DashboardScreen())
            self._controlla_aggiornamenti_avvio()

    def _controlla_aggiornamenti_avvio(self) -> None:
        from cartellino.user_config import UserConfig

        user_config = UserConfig.load()
        if user_config is None or not user_config.check_updates_on_startup:
            return
        self._check_update_worker()

    @work(thread=True)
    def _check_update_worker(self) -> None:
        from cartellino.update_checker import check_for_update

        current_version = _app_version()
        try:
            release = check_for_update(current_version)
        except Exception as e:
            log.warning(f"Controllo aggiornamenti all'avvio fallito: {e}")
            return
        if release is not None:
            self.call_from_thread(self._mostra_aggiornamento_disponibile, current_version, release)

    def _mostra_aggiornamento_disponibile(self, current_version: str, release) -> None:
        from cartellino.tui.screens.app_update import AppUpdateScreen
        self.push_screen(AppUpdateScreen(current_version, release))


def run(data_folder: Path = DATA_FOLDER) -> None:
    data_folder.mkdir(parents=True, exist_ok=True)
    CartellinoApp(data_folder=data_folder).run()
