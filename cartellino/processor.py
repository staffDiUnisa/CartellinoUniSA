import logging
from pathlib import Path

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.credito_ore import CreditoOre
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_giornaliere import OreGiornaliere
from cartellino.statistiche import Statistiche

log = logging.getLogger(__name__)

# Chiavi selezionabili con `--solo-report` (cartellino_v2.py) / `run(reports=...)`.
REPORT_KEYS = ("cartellino", "riposo", "credito", "statistiche", "ore-giornaliere")


class CartellinoProcessor:
    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self, reports: set[str] | None = None) -> None:
        """Genera i report.

        `reports=None` (default, comportamento storico) li genera tutti. Passando un
        sottoinsieme di `REPORT_KEYS` si generano solo quelli — chiuso il punto
        lasciato aperto in Fase 3 TODO.md ("scrittura on demand, un'azione per
        report") anche lato CLI, non solo TUI (`ReportsScreen`).
        """
        reports = reports if reports is not None else set(REPORT_KEYS)
        cfg = self.config

        # Cartellino grezzo: sempre caricato (serve come base per tutti i report),
        # scritto su disco solo se richiesto.
        cartellino = Cartellino.from_config(cfg)
        if "cartellino" in reports:
            cartellino.salva(cfg.output_folder / "cartellino.xlsx")

        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )

        if "riposo" in reports:
            if cfg.min_date:
                riposi_usati = OreEccedenti.get_date_usate_from_src(
                    src_df=cartellino.src,
                    min_date=cfg.min_date,
                )
            else:
                riposi_usati = OreEccedenti.get_date_usate_from_file(cfg.riposi_usati_file)

            riposi_compensativi = oe_proc.raggruppa(riposi_usati)
            oe_proc.salva_dettaglio(cfg.output_folder / "riposo_compensativo.xlsx", fmt=cfg.export_format)
            oe_proc.salva_testo(riposi_compensativi, cfg.output_folder / "riposi_compensativi.txt")

        if "credito" in reports:
            ce_proc = CreditoOre(
                oo_diu=cartellino.oo_diu,
                oe=oe_proc.elabora(),
                excluded_dates_file=cfg.excluded_dates_file,
            )
            ce_proc.salva(cfg.output_folder / "credito_ore.xlsx", fmt=cfg.export_format)

        if "statistiche" in reports:
            stat = Statistiche(cartellino=cartellino, config=cfg)
            stat.salva(cfg.output_folder / "statistiche.xlsx", fmt=cfg.export_format)
            log.info(f"Codici usati per le statistiche del cartellino: {cartellino.codici_usati}")
            log.info(f"Codici non usati per le statistiche del cartellino: {cartellino.codici_non_usati()}")

        if "ore-giornaliere" in reports:
            og_proc = OreGiornaliere(oo_diu=cartellino.oo_diu)
            og_proc.salva(cfg.output_folder / "ore_giornaliere.xlsx", fmt=cfg.export_format)

    @classmethod
    def from_env(cls, data_folder: Path = Path("data")) -> "CartellinoProcessor":
        return cls(config=Config.load(data_folder=data_folder))
