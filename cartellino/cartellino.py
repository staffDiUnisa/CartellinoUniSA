import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from cartellino.config import Config

_MONTH_MAP = {
    "gen": 1, "feb": 2, "mar": 3, "apr": 4,
    "mag": 5, "giu": 6, "lug": 7, "ago": 8,
    "set": 9, "ott": 10, "nov": 11, "dic": 12,
}

# Separatore usato nell'Excel originale tra voci base multiple
_VOCI_SEP = chr(160) + "&-&" + chr(160)


class Cartellino:
    def __init__(self, df: pd.DataFrame, year: int) -> None:
        self.year = year
        self.df = df
        self.codici_usati: list[str] = []

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_excel(cls, path: Path, year: int) -> "Cartellino":
        df = pd.read_excel(path)
        df["Voci Base"] = df["Voci Base"].str.split(_VOCI_SEP)
        df["date"] = df["Data"].apply(lambda x: cls.get_date_from_string(x, year))
        df = df.explode("Voci Base")
        df["Voci Base"] = df["Voci Base"].fillna("____")
        df["Codice"] = df["Voci Base"].apply(cls.extract_codice)
        return cls(df=df, year=year)

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_codice(voci_base: str) -> str:
        match = re.search(r'[A-Z]+-?[A-Z][A-Z]+', voci_base)
        return match.group(0).strip() if match else "-"

    @staticmethod
    def get_date_from_string(date_string: str, year: int) -> datetime:
        regex = r"[a-z]{3}\s(\d\d?)\s([a-z]{3})"
        m = re.search(regex, date_string, re.IGNORECASE)
        day = int(m.group(1))
        month = _MONTH_MAP[m.group(2).lower()]
        try:
            return datetime(year, month, day)
        except ValueError:
            print(f"Invalid date: {day}-{month}-{year}")
            raise

    # ------------------------------------------------------------------
    # Filtered views (each marks the codice as used)
    # ------------------------------------------------------------------

    def _filter(self, *codici: str) -> pd.DataFrame:
        self.codici_usati.extend(c for c in codici if c not in self.codici_usati)
        mask = self.df["Codice"].isin(codici)
        return self.df[mask].copy()

    @property
    def oe_diu(self) -> pd.DataFrame:
        return self._filter("OE-DIU")

    @property
    def oo_diu(self) -> pd.DataFrame:
        return self._filter("OO-DIU")

    @property
    def src(self) -> pd.DataFrame:
        return self._filter("SRC")

    @property
    def tck(self) -> pd.DataFrame:
        return self._filter("TCK")

    @property
    def vsg(self) -> pd.DataFrame:
        return self._filter("VSG")

    @property
    def straordinari(self) -> pd.DataFrame:
        return self._filter("STRSOS", "FSTLAV", "OS-FSD")

    @property
    def malattia(self) -> pd.DataFrame:
        return self._filter("MAL", "RIC")

    @property
    def ferie(self) -> pd.DataFrame:
        return self._filter("FER", "FEV", "FST")

    @property
    def permesso_gravi_motivi(self) -> pd.DataFrame:
        return self._filter("PMF")

    @property
    def entrata_ritardo(self) -> pd.DataFrame:
        return self._filter("ERIT")

    @property
    def vigilanza_concorsi(self) -> pd.DataFrame:
        return self._filter("VIG")

    @property
    def motivi_di_servizio(self) -> pd.DataFrame:
        return self._filter("AMU")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def codici_non_usati(self) -> list[str]:
        all_codes = set(self.df["Codice"].unique())
        return sorted(all_codes - set(self.codici_usati))

    def salva(self, output_file: Path) -> None:
        from pandas.io.formats import excel as excel_fmt
        from cartellino.excel_utils import apply_table_format
        excel_fmt.ExcelFormatter.header_style = None
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            self.df.to_excel(writer, index=False, sheet_name="cartellino")
            apply_table_format(writer.sheets["cartellino"], self.df)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, config: Config) -> "Cartellino":
        return cls.from_excel(config.input_folder / "cartellino.xlsx", config.current_year)
