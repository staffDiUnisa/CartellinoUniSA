import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from cartellino.cartellino import Cartellino
from cartellino.config import Config

log = logging.getLogger(__name__)

_MONTH_ORDER = {
    'gen': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'mag': 4, 'giu': 5,
    'lug': 6, 'ago': 7, 'set': 8, 'ott': 9, 'nov': 10, 'dic': 11,
}


class Statistiche:
    def __init__(self, cartellino: Cartellino, config: Config) -> None:
        self._cartellino = cartellino
        self._config = config
        self._sheets: dict[str, pd.DataFrame] | None = None

    def calcola(self) -> dict[str, pd.DataFrame]:
        if self._sheets is not None:
            return self._sheets
        c = self._cartellino
        tck = self._elabora_ticket(c.tck)
        tck_stat = self._stat_ticket(tck)
        self._sheets = {
            "visite_specialistiche": c.vsg[["Stato", "Data", "Voci Base"]],
            "straordinari": c.straordinari[["Stato", "Data", "Voci Base"]],
            "ticket": tck,
            "statistica_ticket": tck_stat,
            "malattia": c.malattia[["Stato", "Data", "Voci Base"]],
            "ferie": c.ferie[["Stato", "Data", "Voci Base"]],
            "vigilanza_concorsi": c.vigilanza_concorsi[["Stato", "Data", "Voci Base"]],
            "permessi_gravi_motivi": c.permesso_gravi_motivi[["Stato", "Data", "Voci Base"]],
            "entrata_ritardo": c.entrata_ritardo[["Stato", "Data", "Voci Base"]],
        }
        return self._sheets

    def salva(self, output_file: Path, fmt: str = "xlsx") -> None:
        sheets = self.calcola()
        log.info(f"Scrivo le statistiche ottenute su {output_file}")
        from cartellino.export_utils import save_sheets
        save_sheets(sheets, output_file, fmt=fmt)

    # ------------------------------------------------------------------

    def _elabora_ticket(self, tck: pd.DataFrame) -> pd.DataFrame:
        ticket_date = self._leggi_data_ticket()
        tck = tck[["Stato", "Data", "Voci Base"]].copy()
        tck["Maturati"] = 1
        tck["Valore maturati"] = 7.00
        tck["Da ricevere"] = tck["Data"].apply(
            lambda x: 1 if Cartellino.get_date_from_string(x, self._config.current_year) > ticket_date else 0
        )
        tck["Valore da ricevere"] = tck["Da ricevere"] * 7.00
        return tck

    def _leggi_data_ticket(self) -> datetime:
        line = self._config.data_ticket_file.read_text().strip()
        return datetime.strptime(line, "%d-%m-%Y")

    @staticmethod
    def _stat_ticket(tck: pd.DataFrame) -> pd.DataFrame:
        tck = tck.copy()
        tck["mese"] = tck["Data"].str[-3:]
        stat = (
            tck[["Stato", "mese", "Data"]]
            .groupby(["Stato", "mese"])
            .count()
            .reset_index()
        )
        stat.rename(columns={"Data": "Numero Ticket"}, inplace=True)
        stat.sort_values(by=["mese"], key=lambda x: x.map(_MONTH_ORDER), inplace=True)
        return stat
