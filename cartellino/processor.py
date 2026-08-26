from pathlib import Path

from processor.cartellinoprogetto import CartellinoProgetto

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.credito_ore import CreditoOre
from cartellino.ore_eccedenti import OreEccedenti
from cartellino.ore_giornaliere import OreGiornaliere
from cartellino.statistiche import Statistiche


class CartellinoProcessor:
    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self) -> None:
        cfg = self.config

        # 1. Carica e parsa il cartellino
        cartellino = Cartellino.from_config(cfg)
        cartellino.salva(cfg.output_folder / "cartellino.xlsx")

        # 2. Ore eccedenti
        oe_proc = OreEccedenti(
            df=cartellino.oe_diu,
            excluded_dates_file=cfg.excluded_dates_file,
            current_year=cfg.current_year,
        )
        oe_df = oe_proc.elabora()

        # 3. Riposi compensativi usati
        if cfg.min_date:
            riposi_usati = OreEccedenti.get_date_usate_from_src(
                src_df=cartellino.src,
                min_date=cfg.min_date,
            )
        else:
            riposi_usati = OreEccedenti.get_date_usate_from_file(cfg.riposi_usati_file)

        riposi_compensativi = oe_proc.raggruppa(riposi_usati)
        oe_proc.salva_dettaglio(cfg.output_folder / "riposo_compensativo.xlsx")
        oe_proc.salva_testo(riposi_compensativi, cfg.output_folder / "riposi_compensativi.txt")

        # 4. Credito ore
        ce_proc = CreditoOre(
            oo_diu=cartellino.oo_diu,
            oe=oe_df,
            excluded_dates_file=cfg.excluded_dates_file,
        )
        ce_proc.salva(cfg.output_folder / "credito_ore.xlsx")

        # 5. Statistiche
        stat = Statistiche(cartellino=cartellino, config=cfg)
        stat.salva(cfg.output_folder / "statistiche.xlsx")

        print("Codici usati per le statistiche del cartellino:")
        print(cartellino.codici_usati)
        print("Codici non usati per le statistiche del cartellino:")
        print(cartellino.codici_non_usati())

        # 6. Ore giornaliere
        og_proc = OreGiornaliere(oo_diu=cartellino.oo_diu)
        og_proc.salva(cfg.output_folder / "ore_giornaliere.xlsx")

        # 7. Timesheet di progetto
        CartellinoProgetto(
            input_folder=cfg.output_folder,
            min_hours_per_day=5,
            max_project_hours_per_day=2.5,
        )

    @classmethod
    def from_env(cls, data_folder: Path = Path("data")) -> "CartellinoProcessor":
        return cls(config=Config.load(data_folder=data_folder))
