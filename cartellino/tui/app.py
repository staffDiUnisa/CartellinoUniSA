import logging
import tomllib
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from cartellino.config import Config

log = logging.getLogger(__name__)

DATA_FOLDER = Path("data/v2")


def _app_version() -> str:
    """Legge la versione da `pyproject.toml` (il progetto ha `tool.uv.package = false`,
    quindi non è installato come pacchetto e `importlib.metadata.version()` non
    funzionerebbe)."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as fh:
            data = tomllib.load(fh)
        return data["project"]["version"]
    except Exception:
        return "dev"


class CartellinoApp(App):
    TITLE = "Cartellino UniSA"
    SUB_TITLE = f"v{_app_version()}"

    BINDINGS = [
        Binding("q", "quit", "Esci"),
    ]

    def __init__(self, data_folder: Path = DATA_FOLDER) -> None:
        super().__init__()
        self.data_folder = data_folder
        self.config: Config | None = None

    def on_mount(self) -> None:
        self.reload_config_and_route()

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


def run(data_folder: Path = DATA_FOLDER) -> None:
    data_folder.mkdir(parents=True, exist_ok=True)
    CartellinoApp(data_folder=data_folder).run()
