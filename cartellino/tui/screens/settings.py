import logging

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from cartellino.credentials import delete_credentials, get_credentials, set_credentials
from cartellino.user_config import (
    DEFAULT_DASHBOARD_BALANCE_CODES,
    DEFAULT_DASHBOARD_EXCEPTION_CODES,
    UserConfig,
)

log = logging.getLogger(__name__)


class SettingsScreen(Screen):
    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings-body"):
            user_config = UserConfig.load() or UserConfig(current_year=self.app.config.current_year)

            yield Label("Anno corrente")
            yield Input(value=str(user_config.current_year), restrict=r"\d*", id="input-anno")

            yield Label("Data minima riposi compensativi usati (MM-DD, opzionale)")
            yield Input(value=user_config.min_date_riposi_usati or "", id="input-min-date")

            yield Label("Formato export report")
            yield Select(
                [("xlsx", "xlsx"), ("csv", "csv")],
                value=user_config.export_format,
                allow_blank=False,
                id="select-formato",
            )

            yield Label("Codici eccezione dashboard (separati da virgola)")
            yield Input(value=",".join(user_config.dashboard_exception_codes), id="input-codici-eccezione")

            yield Label("Codici saldo mensile dashboard (separati da virgola)")
            yield Input(value=",".join(user_config.dashboard_balance_codes), id="input-codici-saldo")

            with Vertical():
                yield Label("Download headless (solo Credenziali UNISA)")
                yield Switch(value=user_config.headless, id="switch-headless")

            stato_cred = "impostate" if get_credentials() is not None else "non impostate"
            yield Static(f"[b]Credenziali UniSA[/b]: {stato_cred}")
            yield Label("Nuovo username (lascia vuoto per non modificare)")
            yield Input(placeholder="mario.rossi", id="input-username")
            yield Label("Nuova password (lascia vuoto per non modificare)")
            yield Input(password=True, id="input-password")
            yield Button("Rimuovi credenziali", id="btn-rimuovi-cred")

            yield Static("", id="settings-errore")
            yield Button("Salva", id="btn-salva", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-salva":
            self._salva()
        elif event.button.id == "btn-rimuovi-cred":
            delete_credentials()
            log.info("Credenziali UniSA rimosse dal keyring.")
            self.query_one("#settings-errore", Static).update("Credenziali rimosse.")

    def _salva(self) -> None:
        errore_widget = self.query_one("#settings-errore", Static)
        anno_str = self.query_one("#input-anno", Input).value.strip()
        if not anno_str.isdigit():
            errore_widget.update("[red]Anno corrente obbligatorio e numerico.[/red]")
            return

        min_date = self.query_one("#input-min-date", Input).value.strip() or None
        export_format = self.query_one("#select-formato", Select).value
        codici_eccezione = [
            c.strip() for c in self.query_one("#input-codici-eccezione", Input).value.split(",") if c.strip()
        ]
        codici_saldo = [
            c.strip() for c in self.query_one("#input-codici-saldo", Input).value.split(",") if c.strip()
        ]
        headless = self.query_one("#switch-headless", Switch).value

        UserConfig(
            current_year=int(anno_str),
            min_date_riposi_usati=min_date,
            headless=headless,
            export_format=str(export_format),
            dashboard_exception_codes=codici_eccezione or list(DEFAULT_DASHBOARD_EXCEPTION_CODES),
            dashboard_balance_codes=codici_saldo or list(DEFAULT_DASHBOARD_BALANCE_CODES),
        ).save()

        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value
        if username and password:
            set_credentials(username, password)

        log.info("Impostazioni salvate.")
        self.app.reload_config_and_route()

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
