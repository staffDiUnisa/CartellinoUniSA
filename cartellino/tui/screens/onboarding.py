import logging
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, Switch

from cartellino.credentials import set_credentials
from cartellino.user_config import UserConfig

log = logging.getLogger(__name__)


class OnboardingScreen(Screen):
    """Setup iniziale: mostrata quando manca `config.toml` o le credenziali nel keyring."""

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="onboarding-body"):
            yield Static(
                "Benvenuto in Cartellino UniSA.\n"
                "Configura anno e credenziali per iniziare "
                "(le credenziali sono opzionali qui: puoi impostarle anche dopo, da Impostazioni)."
            )
            yield Label("Anno corrente *")
            yield Input(
                value=str(datetime.now().year),
                placeholder="2026",
                restrict=r"\d*",
                id="input-anno",
            )
            yield Label("Data minima riposi compensativi usati (MM-DD, opzionale)")
            yield Input(placeholder="01-01", id="input-min-date")
            yield Label("Username UniSA (opzionale)")
            yield Input(placeholder="mario.rossi", id="input-username")
            yield Label("Password UniSA (opzionale)")
            yield Input(password=True, id="input-password")
            with Vertical():
                yield Label("Download headless (solo per Credenziali UNISA)")
                yield Switch(id="switch-headless")
            yield Static("", id="onboarding-errore")
            with Horizontal(classes="button-row"):
                yield Button("Salva e continua", id="btn-salva", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-salva":
            self._salva()

    def _salva(self) -> None:
        errore_widget = self.query_one("#onboarding-errore", Static)
        anno_str = self.query_one("#input-anno", Input).value.strip()
        min_date = self.query_one("#input-min-date", Input).value.strip() or None
        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value
        headless = self.query_one("#switch-headless", Switch).value

        if not anno_str.isdigit():
            errore_widget.update("[red]Anno corrente obbligatorio e numerico.[/red]")
            return

        user_config = UserConfig(
            current_year=int(anno_str),
            min_date_riposi_usati=min_date,
            headless=headless,
        )
        user_config.save()

        if username and password:
            set_credentials(username, password)

        log.info(f"Configurazione iniziale salvata (anno {anno_str}).")
        self.app.reload_config_and_route()
