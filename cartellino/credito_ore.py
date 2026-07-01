import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

_MONTH_ORDER = {
    'gen': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'mag': 4, 'giu': 5,
    'lug': 6, 'ago': 7, 'set': 8, 'ott': 9, 'nov': 10, 'dic': 11,
}


class CreditoOre:
    def __init__(self, oo_diu: pd.DataFrame, oe: pd.DataFrame, excluded_dates_file: Path) -> None:
        self._oo_diu = oo_diu[["Stato", "Data", "Voci Base", "Saldo (ore medie)", "date"]].copy()
        self._oe = oe.copy()
        self.excluded_dates_file = excluded_dates_file
        self._df: pd.DataFrame | None = None

    def calcola(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        self._df = self._calcola()
        return self._df

    def salva(self, output_file: Path) -> None:
        df = self.calcola()
        print(f"Scrivo credito ore su {output_file}")
        from cartellino.excel_utils import apply_table_format
        renamed = (
            df[["Stato", "mese", "credito", "credito_ore_residuo"]]
            .rename(columns={
                "Stato": "Stato elaborazione mese",
                "mese": "Mese",
                "credito": "Credito ore",
                "credito_ore_residuo": "Credito ore al netto dei riposi maturati",
            })
        )
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            renamed.to_excel(writer, index=False, sheet_name="credito_ore")
            apply_table_format(writer.sheets["credito_ore"], renamed)

    # ------------------------------------------------------------------

    def _load_excluded_dates(self) -> list[dict]:
        excluded: list[dict] = []
        with open(self.excluded_dates_file, "r") as fh:
            for line in fh:
                line = line.strip()
                if re.match(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$', line):
                    dt = datetime.strptime(line, "%d-%m-%Y %H:%M")
                    has_time = True
                else:
                    dt = datetime.strptime(line, "%d-%m-%Y")
                    has_time = False
                excluded.append({"data": np.datetime64(dt), "has_time": has_time})
        return excluded

    def _calcola(self) -> pd.DataFrame:
        df = self._oo_diu.copy()
        excluded = self._load_excluded_dates()

        if excluded:
            df = df[~df["date"].isin([d["data"] for d in excluded])]

        df["mese"] = df["Data"].str[-3:]
        df["saldo_ore"] = df["Saldo (ore medie)"].astype(int) * 60
        df["saldo_minuti"] = ((df["Saldo (ore medie)"] - df["Saldo (ore medie)"].astype(int)) * 100).astype(int)
        df["Saldo (ore medie)"] = df["saldo_ore"] + df["saldo_minuti"]

        oe = self._oe.copy()
        oe["mese"] = oe["Data"].str[-3:]
        oe["Riposo Compensativo"] = (oe["ore eccedenti"] * 60) + oe["minuti eccedenti"]
        oe = (
            oe[["Stato", "mese", "Riposo Compensativo"]]
            .groupby(["Stato", "mese"])
            .sum()
            .reset_index()
        )
        oe.sort_values(by=["mese"], key=lambda x: x.map(_MONTH_ORDER), inplace=True)

        df = df[["Stato", "mese", "Saldo (ore medie)"]].groupby(["Stato", "mese"]).sum().reset_index()
        df = pd.merge(df, oe[["Stato", "mese", "Riposo Compensativo"]], on=["Stato", "mese"], how="outer")
        df["Riposo Compensativo"] = df["Riposo Compensativo"].fillna(0).astype(int)
        df["ore_residue"] = (df["Saldo (ore medie)"] - df["Riposo Compensativo"]).apply(lambda x: max(x, 0))
        df["credito"] = pd.to_datetime(df["Saldo (ore medie)"], unit="m").dt.strftime("%H:%M")
        df["credito_ore_residuo"] = pd.to_datetime(df["ore_residue"], unit="m").dt.strftime("%H:%M")
        df.sort_values(by=["mese"], key=lambda x: x.map(_MONTH_ORDER), inplace=True)
        return df
