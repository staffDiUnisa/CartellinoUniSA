import webbrowser

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, MarkdownViewer, Static

from cartellino.update_checker import ReleaseInfo


class AppUpdateScreen(Screen):
    """Esito del controllo aggiornamenti dell'app (issue #3) — distinta da `UpdateScreen`,
    che riguarda l'aggiornamento dei *dati* del cartellino, non dell'app stessa.

    Niente self-update automatico (rischioso: binario onedir, .pkg macOS firmato/notarizzato,
    .exe Windows in esecuzione): il pulsante apre la pagina della release nel browser di
    sistema, l'installazione resta manuale come oggi."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def __init__(self, current_version: str, release: ReleaseInfo | None) -> None:
        super().__init__()
        self._current_version = current_version
        self._release = release

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="app-update-body"):
            if self._release is None:
                yield Static(f"Nessun aggiornamento disponibile (versione attuale: {self._current_version}).")
            else:
                yield Static(
                    f"Nuova versione disponibile: [b]{self._release.version}[/b] "
                    f"(attuale: {self._current_version})"
                )
                yield MarkdownViewer(self._release.body or "_Nessuna nota di rilascio._", show_table_of_contents=False)
            with Horizontal(classes="button-row"):
                if self._release is not None:
                    yield Button("🌐 Apri pagina di download", id="btn-apri-download", variant="primary")
                yield Button("✖️ Chiudi", id="btn-chiudi")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apri-download" and self._release is not None:
            webbrowser.open(self._release.html_url)
        elif event.button.id == "btn-chiudi":
            self.app.pop_screen()

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
