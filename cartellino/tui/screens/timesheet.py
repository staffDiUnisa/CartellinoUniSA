import logging
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Select, Static

from cartellino.timesheet_runner import esegui_timesheet_progetto

log = logging.getLogger(__name__)

TIMESHEET_FOLDER = Path("timesheet")


class TimesheetScreen(Screen):
    """Selezione di uno YAML esistente in `timesheet/` e generazione del timesheet
    mensile (+ rendiconto Excel, se configurato). Niente wizard di creazione YAML da
    zero: resta un'operazione manuale sul filesystem, come oggi (fuori scope Fase 4)."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="timesheet-body"):
            yaml_files = sorted(TIMESHEET_FOLDER.glob("*.yaml")) if TIMESHEET_FOLDER.exists() else []
            if not yaml_files:
                yield Static(
                    f"Nessun file YAML trovato in '{TIMESHEET_FOLDER}'. "
                    "Crea un file di configurazione (vedi "
                    "templates/timesheet_progetto_template.yaml) e riapri questa schermata."
                )
            else:
                yield Static("Seleziona un timesheet di progetto:")
                yield Select(
                    [(f.name, str(f)) for f in yaml_files],
                    id="select-timesheet",
                )
                yield Button("Genera", id="btn-genera", variant="primary")
            yield RichLog(id="timesheet-log", wrap=True, markup=True)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-genera":
            return
        richlog = self.query_one("#timesheet-log", RichLog)
        select = self.query_one("#select-timesheet", Select)
        if select.value == Select.BLANK:
            richlog.write("[red]Seleziona un file YAML.[/red]")
            return

        ts_path = Path(str(select.value))
        try:
            ts_config = esegui_timesheet_progetto(self.app.config, ts_path)
            richlog.write(f"Timesheet '{ts_config.nome}' generato in {self.app.config.output_folder}")
        except Exception as e:
            log.error(f"Errore nella generazione del timesheet: {e}")
            richlog.write(f"[red]Errore: {e}[/red]")

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
