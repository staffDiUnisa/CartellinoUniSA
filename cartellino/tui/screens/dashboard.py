import logging
from datetime import datetime, timedelta

from textual import work
from textual.app import ComposeResult
from textual.containers import ItemGrid, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from cartellino.cartellino import Cartellino
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_helpers import calcola_saldo_minuti, somma_ore_per_codici
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)


def _categorizza_riposo(riposo) -> tuple[str, str]:
    """Categorizzazione dei riposi compensativi per la dashboard, vedi TODO.md
    § "Note tecniche sulla categorizzazione dei riposi compensativi"."""
    if riposo.data:
        return "USATO", f"il {riposo.data}"
    if riposo.ore_mancanti() <= timedelta(0):
        confermato = all(o.stato == "ELAB P1" for o in riposo.ore_inserite)
        stato = "COMPLETO E CONFERMATO" if confermato else "COMPLETO NON CONFERMATO"
        return stato, ""
    mancanti = riposo.ore_mancanti()
    ore = mancanti.seconds // 3600
    minuti = (mancanti.seconds // 60) % 60
    return "DA COMPLETARE", f"mancano {ore}:{minuti:02}"


class DashboardScreen(Screen):
    BINDINGS = [
        ("r", "aggiorna_cartellino", "Aggiorna cartellino"),
        ("t", "apri_timesheet", "Timesheet progetto"),
        ("p", "apri_report", "Report"),
        ("v", "apri_statistiche", "Statistiche"),
        ("s", "apri_impostazioni", "Impostazioni"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="dashboard-body"):
            yield from self._build_body()
        yield Footer()

    async def on_screen_resume(self) -> None:
        # Ricostruisce solo il contenuto dinamico (non Header/Footer): un
        # `Screen.recompose()` pieno ricrea anche l'Header, che può lasciare in
        # sospeso il suo task interno di set-title contro l'istanza appena
        # rimossa e far fallire il prossimo evento gestito da Textual.
        body = self.query_one("#dashboard-body")
        await body.remove_children()
        await body.mount_all(self._build_body())

    # ------------------------------------------------------------------

    def _build_body(self) -> list:
        # NB: costruisce i widget con i costruttori (`Vertical(*children)`), non con
        # `with Vertical(): yield ...` — quel pattern di composizione funziona solo
        # dentro una chiamata a `compose()` vera e propria (si appoggia allo stack
        # interno `App._compose_stacks`), mentre questo metodo viene richiamato anche
        # da `on_screen_resume` fuori da un ciclo di compose.
        config = self.app.config
        feather_path = config.input_folder / "cartellino.feather"

        if not feather_path.exists():
            return [
                Static(
                    "Nessun cartellino scaricato ancora per l'anno "
                    f"{config.current_year}.\n\n"
                    "Premi 'r' o il pulsante qui sotto per avviare il primo download."
                ),
                Button("🔄 Aggiorna cartellino", id="btn-aggiorna", variant="primary"),
            ]

        try:
            cartellino = Cartellino.from_config(config)
        except Exception as e:
            return [
                Static(f"[red]Errore nella lettura del cartellino: {e}[/red]"),
                Button("🔄 Aggiorna cartellino", id="btn-aggiorna", variant="primary"),
            ]

        now = datetime.now()

        sezioni = [
            ("Eccezioni/saldo mese", lambda: self._sezione_eccezioni(cartellino, config, now)),
            ("Saldo mensile", lambda: self._sezione_saldo(cartellino, config, now)),
            ("Riposi compensativi", lambda: self._sezione_riposi(cartellino, config)),
            ("Ferie/PMF", lambda: self._sezione_ferie_pmf(cartellino)),
            ("Ticket da ricevere", lambda: self._sezione_ticket(cartellino, config)),
            ("Ultimo aggiornamento", lambda: self._sezione_aggiornamento(feather_path)),
        ]

        sezione_widgets = []
        for nome, build in sezioni:
            try:
                testo = build()
            except Exception as e:
                log.warning(f"Errore nella sezione dashboard '{nome}': {e}")
                testo = f"[b]{nome}[/b]\n  [red]Errore: {e}[/red]"
            sezione_widgets.append(Static(testo, classes="dashboard-section"))

        return [
            Vertical(*sezione_widgets),
            ItemGrid(
                Button("🔄 Aggiorna cartellino [r]", id="btn-aggiorna"),
                Button("📄 Genera report [p]", id="btn-report"),
                Button("📐 Genera timesheet [t]", id="btn-timesheet"),
                Button("📊 Statistiche [v]", id="btn-statistiche-nav"),
                Button("⚙️ Impostazioni [s]", id="btn-impostazioni"),
                Button("⬆️ Controlla aggiornamenti", id="btn-controlla-aggiornamenti"),
                classes="button-grid",
                min_column_width=24,
            ),
        ]

    @staticmethod
    def _sezione_eccezioni(cartellino: Cartellino, config, now: datetime) -> str:
        codici = config.dashboard_exception_codes
        df = somma_ore_per_codici(cartellino.df, codici)
        df = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
        if df.empty:
            righe = "nessuna"
        else:
            righe = "\n".join(
                f"  - {row['date'].strftime('%d/%m/%Y')}: {row['Codice']} {row['ore']:02}:{row['minuti']:02}"
                for _, row in df.iterrows()
            )
        return f"[b]Eccezioni del mese ({', '.join(codici)})[/b]\n{righe}"

    @staticmethod
    def _sezione_saldo(cartellino: Cartellino, config, now: datetime) -> str:
        codici = config.dashboard_balance_codes
        df = cartellino.df[
            (cartellino.df["date"].dt.month == now.month) & (cartellino.df["date"].dt.year == now.year)
        ]
        totale_minuti = calcola_saldo_minuti(df, codici)
        ore, minuti = divmod(abs(totale_minuti), 60)
        if totale_minuti < 0:
            colore, segno = "red", "-"
        elif totale_minuti > 0:
            colore, segno = "green", ""
        else:
            colore, segno = "blue", ""
        return (
            f"[b]Saldo ore del mese ({', '.join(codici)})[/b]\n"
            f"  [{colore}]{segno}{ore:02}:{minuti:02}[/{colore}]"
        )

    @staticmethod
    def _sezione_riposi(cartellino: Cartellino, config) -> str:
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=config.excluded_dates_file,
            current_year=config.current_year,
        )
        if config.min_date:
            riposi_usati = OreEccedenti.get_date_usate_from_src(
                src_df=cartellino.src, min_date=config.min_date
            )
        else:
            riposi_usati = OreEccedenti.get_date_usate_from_file(config.riposi_usati_file)

        riposi = oe_proc.raggruppa(riposi_usati)
        righe = []
        for riposo in riposi:
            stato, dettaglio = _categorizza_riposo(riposo)
            righe.append(f"  - Riposo {riposo.id}: {stato}" + (f" ({dettaglio})" if dettaglio else ""))
        return "[b]Riposi compensativi[/b]\n" + ("\n".join(righe) if righe else "  nessuno")

    @staticmethod
    def _sezione_ferie_pmf(cartellino: Cartellino) -> str:
        return (
            "[b]Ferie e permessi (anno corrente)[/b]\n"
            f"  Ferie usate: {len(cartellino.ferie)}\n"
            f"  Permessi gravi motivi familiari usati: {len(cartellino.permesso_gravi_motivi)}"
        )

    @staticmethod
    def _sezione_ticket(cartellino: Cartellino, config) -> str:
        sheets = Statistiche(cartellino=cartellino, config=config).calcola()
        ticket_df = sheets.get("ticket")
        if ticket_df is None:
            return (
                "[b]Ticket da ricevere[/b]\n"
                "  data ticket non impostata (Impostazioni → Buoni pasto accreditati fino al)"
            )
        da_ricevere = ticket_df[ticket_df["Da ricevere"] == 1]
        if da_ricevere.empty:
            return "[b]Ticket da ricevere[/b]\n  nessuno"
        valore = da_ricevere["Valore da ricevere"].sum()
        return f"[b]Ticket da ricevere[/b]\n  {len(da_ricevere)} (valore: {valore:.2f}€)"

    @staticmethod
    def _sezione_aggiornamento(feather_path) -> str:
        mtime = datetime.fromtimestamp(feather_path.stat().st_mtime)
        return f"[b]Ultimo aggiornamento[/b]\n  {mtime.strftime('%d/%m/%Y %H:%M')}"

    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-aggiorna": self.action_aggiorna_cartellino,
            "btn-report": self.action_apri_report,
            "btn-timesheet": self.action_apri_timesheet,
            "btn-statistiche-nav": self.action_apri_statistiche,
            "btn-impostazioni": self.action_apri_impostazioni,
            "btn-controlla-aggiornamenti": self.action_controlla_aggiornamenti,
        }
        action = actions.get(event.button.id)
        if action:
            action()

    def action_aggiorna_cartellino(self) -> None:
        from cartellino.tui.screens.update import UpdateScreen
        self.app.push_screen(UpdateScreen())

    def action_apri_report(self) -> None:
        from cartellino.tui.screens.reports import ReportsScreen
        self.app.push_screen(ReportsScreen())

    def action_apri_timesheet(self) -> None:
        from cartellino.tui.screens.timesheet import TimesheetScreen
        self.app.push_screen(TimesheetScreen())

    def action_apri_statistiche(self) -> None:
        from cartellino.tui.screens.statistiche import StatisticheScreen
        self.app.push_screen(StatisticheScreen())

    def action_apri_impostazioni(self) -> None:
        from cartellino.tui.screens.settings import SettingsScreen
        self.app.push_screen(SettingsScreen())

    def action_controlla_aggiornamenti(self) -> None:
        self._controlla_aggiornamenti()

    @work(thread=True)
    def _controlla_aggiornamenti(self) -> None:
        from cartellino.tui.app import _app_version
        from cartellino.update_checker import check_for_update

        current_version = _app_version()
        try:
            release = check_for_update(current_version)
        except Exception as e:
            log.warning(f"Controllo aggiornamenti fallito: {e}")
            release = None
        self.app.call_from_thread(self._mostra_esito_aggiornamento, current_version, release)

    def _mostra_esito_aggiornamento(self, current_version: str, release) -> None:
        from cartellino.tui.screens.app_update import AppUpdateScreen
        self.app.push_screen(AppUpdateScreen(current_version, release))
