from pathlib import Path

import pandas as pd
from pandas.io.formats import excel

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

    def salva(self, output_file: Path) -> None:
        data = self.calcola()
        mesi = sorted(data.keys(), key=lambda x: _MONTH_ORDER[x])
        print(f"Scrivo ore giornaliere su {output_file}")

        from cartellino.excel_utils import apply_table_format
        excel.ExcelFormatter.header_style = None
        writer = pd.ExcelWriter(
            output_file,
            engine="xlsxwriter",
            datetime_format="dd/mm/yyyy",
            date_format="dd/mm/yyyy",
        )
        for mese in mesi:
            df = data[mese]
            df.to_excel(writer, sheet_name=mese, index=False)
            apply_table_format(writer.sheets[mese], df)
        writer.close()

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
