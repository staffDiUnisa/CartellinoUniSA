import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, MaskedInput, Static

log = logging.getLogger(__name__)

_DATA_TEMPLATE = "99-99-9999"  # DD-MM-YYYY
_ORA_TEMPLATE = "99:99"  # HH:MM


@dataclass
class _VoceEsclusa:
    data: str  # DD-MM-YYYY
    ora: str | None  # HH:MM, oppure None per l'esclusione dell'intera giornata

    def to_line(self) -> str:
        return f"{self.data} {self.ora}" if self.ora else self.data


def _parse_riga(riga: str) -> "_VoceEsclusa | None":
    riga = riga.strip()
    if not riga:
        return None
    parti = riga.split(" ", 1)
    if len(parti) == 2:
        return _VoceEsclusa(data=parti[0], ora=parti[1])
    return _VoceEsclusa(data=parti[0], ora=None)


class DateEscluseScreen(Screen):
    """Gestione di `date_escluse.txt`: una riga `DD-MM-YYYY` esclude l'intera
    giornata dal calcolo delle ore eccedenti (OE-DIU); una riga
    `DD-MM-YYYY HH:MM` sottrae solo quell'orario dalle ore eccedenti del giorno
    (vedi `OreEccedenti._elabora`/CLAUDE.md)."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="date-escluse-body"):
            yield Static(
                "Date da escludere (giornata intera) o orari da sottrarre dal calcolo "
                "delle ore eccedenti (OE-DIU)."
            )
            with VerticalScroll(id="date-escluse-lista"):
                yield from self._build_lista()
            with Horizontal(classes="field-row"):
                yield MaskedInput(_DATA_TEMPLATE, id="input-nuova-data")
                yield MaskedInput(_ORA_TEMPLATE, id="input-nuova-ora")
                yield Button("Aggiungi", id="btn-aggiungi", variant="primary")
            yield Static("", id="date-escluse-errore")
        yield Footer()

    # ------------------------------------------------------------------

    def _file(self) -> Path:
        return self.app.config.excluded_dates_file

    def _leggi(self) -> list[_VoceEsclusa]:
        voci = []
        for riga in self._file().read_text().splitlines():
            voce = _parse_riga(riga)
            if voce is not None:
                voci.append(voce)
        return voci

    def _scrivi(self, voci: list[_VoceEsclusa]) -> None:
        contenuto = "\n".join(v.to_line() for v in voci)
        self._file().write_text(contenuto + ("\n" if contenuto else ""))

    def _build_lista(self) -> list:
        # Costruttori diretti (`Horizontal(*children)`), non `with Horizontal(): yield
        # ...`: questo metodo è richiamato anche fuori da compose() (da
        # `_aggiorna_lista`), dove lo stack interno di composizione di Textual non è
        # attivo (vedi nota analoga in dashboard.py).
        voci = self._leggi()
        if not voci:
            return [Static("Nessuna data esclusa.", id="date-escluse-vuoto")]
        righe = []
        for i, voce in enumerate(voci):
            testo = voce.data + (f" — sottrae {voce.ora}" if voce.ora else " — giornata intera")
            righe.append(
                Horizontal(
                    Static(testo, classes="date-esclusa-testo"),
                    Button("Rimuovi", id=f"rimuovi-{i}", classes="date-esclusa-rimuovi"),
                    classes="date-esclusa-riga",
                )
            )
        return righe

    async def _aggiorna_lista(self) -> None:
        contenitore = self.query_one("#date-escluse-lista")
        await contenitore.remove_children()
        await contenitore.mount_all(self._build_lista())

    # ------------------------------------------------------------------

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "btn-aggiungi":
            await self._aggiungi()
        elif button_id.startswith("rimuovi-"):
            await self._rimuovi(int(button_id.removeprefix("rimuovi-")))

    async def _aggiungi(self) -> None:
        errore_widget = self.query_one("#date-escluse-errore", Static)
        data_input = self.query_one("#input-nuova-data", MaskedInput)
        ora_input = self.query_one("#input-nuova-ora", MaskedInput)

        if not data_input.value or not data_input.is_valid:
            errore_widget.update("[red]Data non valida (formato DD-MM-YYYY).[/red]")
            return
        try:
            datetime.strptime(data_input.value, "%d-%m-%Y")
        except ValueError:
            errore_widget.update("[red]Data non valida.[/red]")
            return

        ora_valore = ora_input.value.strip()
        if ora_valore:
            if not ora_input.is_valid:
                errore_widget.update("[red]Orario incompleto (formato HH:MM).[/red]")
                return
            try:
                datetime.strptime(ora_valore, "%H:%M")
            except ValueError:
                errore_widget.update("[red]Orario non valido.[/red]")
                return

        nuova = _VoceEsclusa(data=data_input.value, ora=ora_valore or None)
        voci = self._leggi()
        voci.append(nuova)
        self._scrivi(voci)
        log.info(f"Aggiunta data esclusa: {nuova.to_line()}")

        data_input.value = ""
        ora_input.value = ""
        errore_widget.update("")
        await self._aggiorna_lista()

    async def _rimuovi(self, indice: int) -> None:
        voci = self._leggi()
        if 0 <= indice < len(voci):
            rimossa = voci.pop(indice)
            self._scrivi(voci)
            log.info(f"Rimossa data esclusa: {rimossa.to_line()}")
        await self._aggiorna_lista()

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
