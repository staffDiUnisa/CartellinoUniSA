import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from cartellino.ore_helpers import estrai_ore_minuti
from model.ore_inserite import OreInserite
from model.riposo_compensativo import RiposoCompensativo

log = logging.getLogger(__name__)


class OreEccedenti:
    def __init__(self, df: pd.DataFrame, excluded_dates_file: Path, current_year: int) -> None:
        self._raw = df[["Stato", "Data", "Voci Base", "date"]].copy()
        self.excluded_dates_file = excluded_dates_file
        self.current_year = current_year
        self._df: pd.DataFrame | None = None  # lazily populated by elabora()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def elabora(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        self._df = self._elabora()
        return self._df

    def raggruppa(self, riposi_usati: list[str]) -> list[RiposoCompensativo]:
        df = self.elabora()
        return self._raggruppa_ore_eccedenti(df, riposi_usati)

    def salva_dettaglio(self, output_file: Path, fmt: str = "xlsx") -> None:
        df = self.elabora().copy()
        log.info(f"Scrivo riposi compensativo su {output_file}")
        base_date = datetime(1900, 1, 1)
        df["intervallo"] = df["intervallo"].apply(lambda x: base_date + x)

        riassunto = (
            df[["Stato", "ore eccedenti", "minuti eccedenti"]]
            .groupby(["Stato"])
            .sum()
            .reset_index()
            .set_index("Stato")
            .sort_index(ascending=False)
        )
        riassunto["OE"] = riassunto["ore eccedenti"] + (riassunto["minuti eccedenti"] // 60)
        riassunto["ME"] = riassunto["minuti eccedenti"] % 60

        cols = ["Stato", "Data", "Voci Base", "ore eccedenti", "minuti eccedenti", "intervallo"]

        if fmt == "xlsx":
            from cartellino.excel_utils import apply_table_format
            with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                df[cols].to_excel(writer, sheet_name="dettaglio", index=False)
                workbook = writer.book
                worksheet = writer.sheets["dettaglio"]
                time_format = workbook.add_format({"num_format": "hh:mm"})
                for row_num, value in enumerate(df["intervallo"], 1):
                    worksheet.write_datetime(row_num, 5, value, time_format)
                apply_table_format(worksheet, df[cols])
                riassunto.to_excel(writer, index=False, sheet_name="riassunto")
                apply_table_format(writer.sheets["riassunto"], riassunto)
            return

        dettaglio = df[cols].copy()
        dettaglio["intervallo"] = dettaglio["intervallo"].dt.strftime("%H:%M")
        from cartellino.export_utils import save_sheets
        save_sheets(
            {"dettaglio": dettaglio, "riassunto": riassunto.reset_index()},
            output_file,
            fmt=fmt,
        )

    def salva_testo(self, riposi: list[RiposoCompensativo], output_file: Path) -> None:
        log.info(f"Scrivo riposi compensativi su {output_file}")
        with open(output_file, mode="w") as f:
            for riposo in riposi:
                f.write("_________________________________________________\n")
                f.write(f"Riposo compensativo {riposo.id}:")
                if riposo.data:
                    f.write(f" - usato per il {riposo.data}")
                if riposo.ore_mancanti() > timedelta(0):
                    h = riposo.ore_mancanti().seconds // 3600
                    m = (riposo.ore_mancanti().seconds // 60) % 60
                    f.write(f" - ore necessarie al completamento: {h}:{m}")
                f.write("\n")
                f.write("_________________________________________________\n")
                for ore in riposo.ore_inserite:
                    from cartellino.cartellino import Cartellino
                    h = ore.ore.seconds // 3600
                    m = (ore.ore.seconds // 60) % 60
                    stato = "OK" if ore.stato == "ELAB P1" else "NO"
                    data_str = Cartellino.get_date_from_string(ore.data, self.current_year).strftime("%d-%m-%Y")
                    f.write(f"\t- {data_str} -> {h:02}:{m:02} [{stato}]\n")
                f.write("_________________________________________________\n")

    def riposi_markdown(self, riposi: list[RiposoCompensativo]) -> str:
        """Stesso contenuto di `salva_testo` (usato per `riposi_compensativi.txt`), ma come
        Markdown — un titolo con tabella per ogni riposo compensativo — per la visualizzazione
        nella schermata Statistiche della TUI (`MarkdownViewer`), più leggibile del formato a
        delimitatori del file di testo."""
        from cartellino.cartellino import Cartellino

        righe: list[str] = []
        for riposo in riposi:
            titolo = f"### Riposo compensativo {riposo.id}"
            if riposo.data:
                titolo += f" — usato per il {riposo.data}"
            if riposo.ore_mancanti() > timedelta(0):
                h = riposo.ore_mancanti().seconds // 3600
                m = (riposo.ore_mancanti().seconds // 60) % 60
                titolo += f" — ore necessarie al completamento: {h}:{m:02}"
            righe.append(titolo)
            righe.append("")
            righe.append("| Data | Ore | Stato |")
            righe.append("| --- | --- | --- |")
            for ore in riposo.ore_inserite:
                h = ore.ore.seconds // 3600
                m = (ore.ore.seconds // 60) % 60
                stato = "✅" if ore.stato == "ELAB P1" else "⏳"
                data_str = Cartellino.get_date_from_string(ore.data, self.current_year).strftime("%d-%m-%Y")
                righe.append(f"| {data_str} | {h:02}:{m:02} | {stato} |")
            righe.append("")
        return "\n".join(righe)

    # ------------------------------------------------------------------
    # Internal helpers
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

    def _elabora(self) -> pd.DataFrame:
        df = self._raw.copy()
        excluded = self._load_excluded_dates()

        if excluded:
            for d in excluded:
                log.debug(d)
            df = df[~df["date"].isin([d["data"] for d in excluded if not d["has_time"]])]

        ore_minuti = df["Voci Base"].apply(estrai_ore_minuti)
        df["ore eccedenti"] = ore_minuti.apply(lambda x: x[0])
        df["minuti eccedenti"] = ore_minuti.apply(lambda x: x[1])

        for d in excluded:
            if d["has_time"]:
                dt = pd.Timestamp(d["data"]).to_pydatetime()
                date_str = dt.strftime("%d-%m-%Y")
                mask = df["date"] == dt.strftime("%d-%m-%Y")
                oe = df.loc[mask, "ore eccedenti"].values[0]
                me = df.loc[mask, "minuti eccedenti"].values[0]
                me -= dt.minute
                oe -= dt.hour
                if me < 0:
                    oe -= 1
                    me += 60
                df.loc[mask, "ore eccedenti"] = oe
                df.loc[mask, "minuti eccedenti"] = me

        df["intervallo"] = (
            pd.to_timedelta(df["ore eccedenti"], unit="h")
            + pd.to_timedelta(df["minuti eccedenti"], unit="m")
        )
        return df

    @staticmethod
    def _raggruppa_ore_eccedenti(df: pd.DataFrame, riposi_usati: list[str]) -> list[RiposoCompensativo]:
        riposi: list[RiposoCompensativo] = []
        id_ = 1
        corrente = RiposoCompensativo(id=id_)
        for index, row in df.iterrows():
            if corrente.ore_mancanti() >= row["intervallo"]:
                corrente.ore_inserite.append(
                    OreInserite(id=index, data=row["Data"], ore=row["intervallo"], stato=row["Stato"])
                )
            else:
                residuo = row["intervallo"] - corrente.ore_mancanti()
                corrente.ore_inserite.append(
                    OreInserite(id=index, data=row["Data"], ore=corrente.ore_mancanti(), stato=row["Stato"])
                )
                if riposi_usati:
                    corrente.data = riposi_usati.pop(0)
                riposi.append(corrente)
                id_ += 1
                corrente = RiposoCompensativo(
                    id=id_,
                    ore_inserite=[OreInserite(id=index, data=row["Data"], ore=residuo, stato=row["Stato"])],
                )
        riposi.append(corrente)
        return riposi

    # ------------------------------------------------------------------
    # Riposi usati helpers (class-level, no state needed)
    # ------------------------------------------------------------------

    @staticmethod
    def get_date_usate_from_file(riposi_usati_file: Path) -> list[str]:
        if not riposi_usati_file.exists():
            return []
        with open(riposi_usati_file, "r") as fh:
            return [line.strip() for line in fh]

    @staticmethod
    def get_date_usate_from_src(src_df: pd.DataFrame, min_date: datetime) -> list[str]:
        filtered = src_df[src_df["date"] > min_date]
        return [row["date"].strftime("%d-%m-%Y") for _, row in filtered.iterrows()]
