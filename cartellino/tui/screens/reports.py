import logging

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from cartellino.cartellino import Cartellino
from cartellino.credito_ore import CreditoOre
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_giornaliere import OreGiornaliere
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)


class ReportsScreen(Screen):
    """Report on-demand (TODO.md § Fase 3/4): nessuna scrittura automatica, un'azione
    per report, nel formato scelto in Impostazioni (`Config.export_format`)."""

    BINDINGS = [("escape", "torna_indietro", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="reports-body"):
            yield Static(
                f"Formato export: {self.app.config.export_format} (modificabile in Impostazioni)"
            )
            with Horizontal(classes="button-row"):
                yield Button("🛌 Riposo compensativo", id="btn-riposo")
                yield Button("🧮 Credito ore", id="btn-credito")
                yield Button("📊 Statistiche", id="btn-statistiche")
                yield Button("🕓 Ore giornaliere", id="btn-ore-giornaliere")
            yield RichLog(id="reports-log", wrap=True, markup=True)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        azioni = {
            "btn-riposo": self._genera_riposo_compensativo,
            "btn-credito": self._genera_credito_ore,
            "btn-statistiche": self._genera_statistiche,
            "btn-ore-giornaliere": self._genera_ore_giornaliere,
        }
        azione = azioni.get(event.button.id)
        if azione is None:
            return
        richlog = self.query_one("#reports-log", RichLog)
        try:
            azione(richlog)
        except Exception as e:
            log.error(f"Errore nella generazione del report: {e}")
            richlog.write(f"[red]Errore: {e}[/red]")

    def _cartellino(self) -> Cartellino:
        return Cartellino.from_config(self.app.config)

    def _riposi_usati(self, cartellino: Cartellino) -> list[str]:
        cfg = self.app.config
        if cfg.min_date:
            return OreEccedenti.get_date_usate_from_src(src_df=cartellino.src, min_date=cfg.min_date)
        return OreEccedenti.get_date_usate_from_file(cfg.riposi_usati_file)

    def _genera_riposo_compensativo(self, richlog: RichLog) -> None:
        cfg = self.app.config
        cartellino = self._cartellino()
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )
        riposi = oe_proc.raggruppa(self._riposi_usati(cartellino))
        oe_proc.salva_dettaglio(cfg.output_folder / "riposo_compensativo.xlsx", fmt=cfg.export_format)
        oe_proc.salva_testo(riposi, cfg.output_folder / "riposi_compensativi.txt")
        richlog.write(f"Riposo compensativo generato in {cfg.output_folder}")

    def _genera_credito_ore(self, richlog: RichLog) -> None:
        cfg = self.app.config
        cartellino = self._cartellino()
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )
        oe_df = oe_proc.elabora()
        CreditoOre(
            oo_diu=cartellino.oo_diu, oe=oe_df, excluded_dates_file=cfg.excluded_dates_file
        ).salva(cfg.output_folder / "credito_ore.xlsx", fmt=cfg.export_format)
        richlog.write(f"Credito ore generato in {cfg.output_folder}")

    def _genera_statistiche(self, richlog: RichLog) -> None:
        cfg = self.app.config
        cartellino = self._cartellino()
        Statistiche(cartellino=cartellino, config=cfg).salva(
            cfg.output_folder / "statistiche.xlsx", fmt=cfg.export_format
        )
        richlog.write(f"Statistiche generate in {cfg.output_folder}")

    def _genera_ore_giornaliere(self, richlog: RichLog) -> None:
        cfg = self.app.config
        cartellino = self._cartellino()
        OreGiornaliere(oo_diu=cartellino.oo_diu).salva(
            cfg.output_folder / "ore_giornaliere.xlsx", fmt=cfg.export_format
        )
        richlog.write(f"Ore giornaliere generate in {cfg.output_folder}")

    def action_torna_indietro(self) -> None:
        self.app.pop_screen()
