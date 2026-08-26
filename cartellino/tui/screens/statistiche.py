import logging

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, MarkdownViewer, Static

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.ore_eccedenti import OreEccedenti
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
_BTN_RIPOSI = "btn-stat-riposi"


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

    def _calcola_riposi_markdown(self) -> str:
        """Stessa fonte dati di `riposi_compensativi.txt` (`OreEccedenti.raggruppa`,
        vedi `CartellinoProcessor.run`), resa come Markdown invece che scritta su file."""
        config: Config = self.app.config
        cartellino = Cartellino.from_config(config)
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=config.excluded_dates_file,
            current_year=config.current_year,
        )
        if config.min_date:
            riposi_usati = OreEccedenti.get_date_usate_from_src(
                src_df=cartellino.src,
                min_date=config.min_date,
            )
        else:
            riposi_usati = OreEccedenti.get_date_usate_from_file(config.riposi_usati_file)
        riposi = oe_proc.raggruppa(riposi_usati)
        return oe_proc.riposi_markdown(riposi)

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
        bottoni.append(Button("Riposo compensativo", id=_BTN_RIPOSI, disabled=self._senza_oe()))

        return [
            Static("Seleziona una categoria (i pulsanti senza dati sono disabilitati)."),
            Horizontal(*bottoni, classes="button-row"),
            DataTable(id="stat-table"),
            MarkdownViewer(id="stat-riposi", show_table_of_contents=True),
        ]

    def _senza_oe(self) -> bool:
        try:
            config: Config = self.app.config
            return Cartellino.from_config(config).oe_diu.empty
        except Exception:
            return True

    def on_mount(self) -> None:
        self.query_one("#stat-riposi", MarkdownViewer).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == _BTN_RIPOSI:
            self._mostra_riposi()
            return
        chiave = _ID_TO_CHIAVE.get(event.button.id or "")
        if chiave is not None:
            self._mostra(chiave)

    def _mostra(self, chiave: str) -> None:
        self.query_one("#stat-riposi", MarkdownViewer).display = False
        tabella = self.query_one("#stat-table", DataTable)
        tabella.display = True
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

    def _mostra_riposi(self) -> None:
        self.query_one("#stat-table", DataTable).display = False
        viewer = self.query_one("#stat-riposi", MarkdownViewer)
        viewer.display = True
        try:
            markdown = self._calcola_riposi_markdown()
        except Exception as e:
            log.error(f"Errore nel caricamento dei riposi compensativi: {e}")
            markdown = f"Errore nel caricamento dei riposi compensativi: {e}"
        viewer.document.update(markdown)

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
