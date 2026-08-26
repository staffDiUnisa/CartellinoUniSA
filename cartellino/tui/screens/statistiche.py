import logging

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)

# (chiave del foglio in Statistiche.calcola(), etichetta pulsante, id widget)
_CATEGORIE = [
    ("statistica_ticket", "Buoni pasto", "btn-stat-ticket"),
    ("ferie", "Ferie", "btn-stat-ferie"),
    ("permessi_gravi_motivi", "Permessi per motivi familiari", "btn-stat-pmf"),
    ("entrata_ritardo", "Entrata in ritardo", "btn-stat-erit"),
    ("straordinari", "Straordinari", "btn-stat-straordinari"),
    ("visite_specialistiche", "Visite Specialistiche", "btn-stat-vsg"),
    ("malattia", "Malattia", "btn-stat-malattia"),
]
_ID_TO_CHIAVE = {id_bottone: chiave for chiave, _, id_bottone in _CATEGORIE}


class StatisticheScreen(Screen):
    """Visualizzazione delle statistiche (stesse categorie di statistiche.xlsx,
    Statistiche.calcola()): un pulsante per categoria, abilitato solo se ci sono
    dati, che carica la tabella corrispondente in una DataTable sotto."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="statistiche-body"):
            yield from self._build_body()
        yield Footer()

    def _calcola(self) -> dict:
        config: Config = self.app.config
        cartellino = Cartellino.from_config(config)
        return Statistiche(cartellino=cartellino, config=config).calcola()

    def _build_body(self) -> list:
        try:
            sheets = self._calcola()
        except Exception as e:
            log.warning(f"Errore nel caricamento delle statistiche: {e}")
            return [Static(f"[red]Errore nel caricamento delle statistiche: {e}[/red]")]

        bottoni = []
        for chiave, etichetta, id_bottone in _CATEGORIE:
            df = sheets.get(chiave)
            vuoto = df is None or df.empty
            bottoni.append(Button(etichetta, id=id_bottone, disabled=vuoto))

        return [
            Static("Seleziona una categoria (i pulsanti senza dati sono disabilitati)."),
            Horizontal(*bottoni, classes="button-row"),
            DataTable(id="stat-table"),
        ]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        chiave = _ID_TO_CHIAVE.get(event.button.id or "")
        if chiave is not None:
            self._mostra(chiave)

    def _mostra(self, chiave: str) -> None:
        tabella = self.query_one("#stat-table", DataTable)
        tabella.clear(columns=True)
        try:
            sheets = self._calcola()
        except Exception as e:
            log.error(f"Errore nel caricamento della statistica '{chiave}': {e}")
            return
        df = sheets.get(chiave)
        if df is None or df.empty:
            return
        tabella.add_columns(*[str(c) for c in df.columns])
        tabella.add_rows(df.astype(str).values.tolist())

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
