import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

_MONTH_ORDER = {
    'gen': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'mag': 4, 'giu': 5,
    'lug': 6, 'ago': 7, 'set': 8, 'ott': 9, 'nov': 10, 'dic': 11,
}


class OreGiornaliere:
    def __init__(self, oo_diu: pd.DataFrame) -> None:
        self._df = oo_diu[["Stato", "Data", "Svolte", "date"]].copy()
        self._result: dict[str, pd.DataFrame] | None = None

    def calcola(self) -> dict[str, pd.DataFrame]:
        if self._result is not None:
            return self._result
        self._result = self._calcola()
        return self._result

    def salva(self, output_file: Path, fmt: str = "xlsx") -> None:
        data = self.calcola()
        mesi = sorted(data.keys(), key=lambda x: _MONTH_ORDER[x])
        log.info(f"Scrivo ore giornaliere su {output_file}")

        sheets = {}
        for mese in mesi:
            df = data[mese].copy()
            df["date"] = df["date"].dt.strftime("%d/%m/%Y")
            sheets[mese] = df

        from cartellino.export_utils import save_sheets
        save_sheets(sheets, output_file, fmt=fmt)

    # ------------------------------------------------------------------

    def _calcola(self) -> dict[str, pd.DataFrame]:
        df = self._df.copy()
        df["mese"] = df["Data"].str[-3:]
        df["Giorno della settimana"] = df["date"].dt.day_name(locale="it_IT.UTF-8")
        mesi = sorted(set(df["mese"].unique()), key=lambda x: _MONTH_ORDER[x])
        result: dict[str, pd.DataFrame] = {}
        for mese in mesi:
            df_mese = df[df["mese"] == mese][["date", "Giorno della settimana", "Svolte"]].copy()
            result[mese] = df_mese
        return result
