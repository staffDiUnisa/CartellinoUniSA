import logging

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RadioButton, RadioSet, RichLog, Static

from cartellino.tui.logging_handler import RichLogHandler
from get import METODI_AUTENTICAZIONE, is_on_unisa_network, ottieni_cartellino

log = logging.getLogger(__name__)


class UpdateScreen(Screen):
    """Aggiornamento del cartellino: mai automatico, richiede scelta esplicita del
    metodo di autenticazione e avvio manuale (TODO.md § Fase 4)."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def __init__(self) -> None:
        super().__init__()
        self._handler: RichLogHandler | None = None
        self._metodo_scelto: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="update-body"):
            yield Static("Scegli il metodo di autenticazione e avvia il download.")
            su_rete = is_on_unisa_network()
            with RadioSet(id="radio-metodo"):
                for metodo in METODI_AUTENTICAZIONE:
                    disabilitato = metodo == "Credenziali UNISA" and not su_rete
                    yield RadioButton(metodo, disabled=disabilitato)
            if not su_rete:
                yield Static(
                    "[dim]Credenziali UNISA non disponibile: non sei sulla rete universitaria.[/dim]"
                )
            yield Button("Avvia download", id="btn-avvia", variant="primary")
            yield RichLog(id="update-log", wrap=True, markup=True)
        yield Footer()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self._metodo_scelto = str(event.pressed.label)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-avvia":
            return
        richlog = self.query_one("#update-log", RichLog)
        if not self._metodo_scelto:
            richlog.write("[red]Seleziona un metodo di autenticazione.[/red]")
            return

        event.button.disabled = True
        self.query_one("#radio-metodo", RadioSet).disabled = True

        self._handler = RichLogHandler(self.app, richlog)
        logging.getLogger().addHandler(self._handler)
        logging.getLogger().setLevel(logging.INFO)

        self._scarica(self._metodo_scelto)

    @work(thread=True, exclusive=True)
    def _scarica(self, metodo: str) -> None:
        try:
            ottieni_cartellino(self.app.data_folder, metodo=metodo)
        except Exception as e:
            log.error(f"Download fallito: {e}")
        finally:
            self.app.call_from_thread(self._fine_download)

    def _fine_download(self) -> None:
        if self._handler is not None:
            logging.getLogger().removeHandler(self._handler)
            self._handler = None
        self.query_one("#btn-avvia", Button).disabled = False
        self.query_one("#radio-metodo", RadioSet).disabled = False

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
