import logging
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    MaskedInput,
    Select,
    Static,
    Switch,
)

from cartellino.credentials import delete_credentials, get_credentials, set_credentials
from cartellino.tui.screens.folder_picker import FolderPickerScreen
from cartellino.user_config import (
    DEFAULT_DASHBOARD_BALANCE_CODES,
    DEFAULT_DASHBOARD_EXCEPTION_CODES,
    UserConfig,
)

log = logging.getLogger(__name__)

_DATA_TICKET_TEMPLATE = "99-99-9999"  # DD-MM-YYYY


class SettingsScreen(Screen):
    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="settings-body"):
            user_config = UserConfig.load() or UserConfig(current_year=self.app.config.current_year)
            config = self.app.config

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

            yield Label("Cartella dati (dove viene salvato cartellino.feather)")
            with Horizontal():
                yield Input(
                    value=user_config.data_folder or str(config.data_folder),
                    id="input-data-folder",
                )
                yield Button("Sfoglia...", id="btn-sfoglia-data-folder")

            yield Label("Cartella output report (vuoto = predefinita: {cartella dati}/{anno}/output)")
            with Horizontal():
                yield Input(value=user_config.output_folder or "", id="input-output-folder")
                yield Button("Sfoglia...", id="btn-sfoglia-output-folder")

            yield Label("Buoni pasto accreditati fino al (data_ticket.txt, DD-MM-YYYY)")
            yield MaskedInput(
                _DATA_TICKET_TEMPLATE,
                value=self._leggi_data_ticket_esistente(config),
                id="input-data-ticket",
            )

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

    @staticmethod
    def _leggi_data_ticket_esistente(config) -> str:
        try:
            return config.data_ticket_file.read_text().strip()
        except FileNotFoundError:
            return ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-salva":
            self._salva()
        elif event.button.id == "btn-rimuovi-cred":
            delete_credentials()
            log.info("Credenziali UniSA rimosse dal keyring.")
            self.query_one("#settings-errore", Static).update("Credenziali rimosse.")
        elif event.button.id == "btn-sfoglia-data-folder":
            self._sfoglia("#input-data-folder")
        elif event.button.id == "btn-sfoglia-output-folder":
            self._sfoglia("#input-output-folder")

    def _sfoglia(self, input_id: str) -> None:
        campo = self.query_one(input_id, Input)
        start = Path(campo.value) if campo.value.strip() else None

        def _scelto(path: Path | None) -> None:
            if path is not None:
                campo.value = str(path)

        self.app.push_screen(FolderPickerScreen(start_path=start), callback=_scelto)

    def _salva(self) -> None:
        errore_widget = self.query_one("#settings-errore", Static)
        anno_str = self.query_one("#input-anno", Input).value.strip()
        if not anno_str.isdigit():
            errore_widget.update("[red]Anno corrente obbligatorio e numerico.[/red]")
            return

        data_ticket_input = self.query_one("#input-data-ticket", MaskedInput)
        if data_ticket_input.value and not data_ticket_input.is_valid:
            errore_widget.update("[red]Data ticket incompleta o non valida (formato DD-MM-YYYY).[/red]")
            return
        data_ticket_valore = data_ticket_input.value.strip()
        if data_ticket_valore:
            try:
                datetime.strptime(data_ticket_valore, "%d-%m-%Y")
            except ValueError:
                errore_widget.update("[red]Data ticket non valida.[/red]")
                return

        data_folder_valore = self.query_one("#input-data-folder", Input).value.strip()
        if not data_folder_valore:
            errore_widget.update("[red]La cartella dati non può essere vuota.[/red]")
            return
        output_folder_valore = self.query_one("#input-output-folder", Input).value.strip() or None

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
            data_folder=data_folder_valore,
            output_folder=output_folder_valore,
        ).save()

        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value
        if username and password:
            set_credentials(username, password)

        # Scrive data_ticket.txt nella NUOVA cartella dati (Config va ricaricato per
        # avere il path corretto, dato che data_folder può essere appena cambiato).
        if data_ticket_valore:
            from cartellino.config import Config
            nuovo_config = Config.load(data_folder=self.app.data_folder)
            nuovo_config.data_ticket_file.write_text(data_ticket_valore + "\n")

        log.info("Impostazioni salvate.")
        self.app.reload_config_and_route()

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
