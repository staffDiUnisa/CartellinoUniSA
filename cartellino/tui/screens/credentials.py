import logging

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from cartellino.credentials import set_credentials

log = logging.getLogger(__name__)


class CredentialsScreen(Screen[bool]):
    """Form per impostare/aggiornare le credenziali UniSA nel keyring, raggiunta da
    Impostazioni con il pulsante "Modifica credenziali". Ritorna (via `dismiss`)
    `True` se ha salvato, `False` se annullato — così Impostazioni sa quando
    aggiornare la riga di stato delle credenziali."""

    BINDINGS = [("escape", "annulla", "Annulla")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="credentials-body"):
            yield Label("Username UniSA")
            yield Input(placeholder="mario.rossi", id="input-username")
            yield Label("Password UniSA")
            yield Input(password=True, id="input-password")
            yield Static("", id="credentials-errore")
            with Horizontal(classes="button-row"):
                yield Button("💾 Salva", id="btn-salva", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-salva":
            self._salva()

    def _salva(self) -> None:
        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value
        if not username or not password:
            self.query_one("#credentials-errore", Static).update(
                "[red]Username e password sono obbligatori.[/red]"
            )
            return
        set_credentials(username, password)
        log.info("Credenziali UniSA aggiornate.")
        self.dismiss(True)

    def action_annulla(self) -> None:
        self.dismiss(False)
