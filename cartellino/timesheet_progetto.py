from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from math import floor
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from pandas.io.formats import excel as excel_fmt

from processor.utils import write_excel_file

_MONTH_NAMES = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]

_MIN_ORE_ELIGIBILITA = 5.0


@dataclass
class _Intervallo:
    da: date
    a: date

    def contains(self, d: date) -> bool:
        return self.da <= d <= self.a


@dataclass
class _OraFissa:
    giorno: date
    ore: float


@dataclass
class Persona:
    nome: str
    cognome: str
    codice_fiscale: str
    figura_professionale: str


@dataclass
class ConfigTimesheet:
    nome: str
    cup: str
    anno: int
    mesi: list[int]
    ore_totali: float
    giorni_interi: list[_Intervallo] = field(default_factory=list)
    ore_fisse: list[_OraFissa] = field(default_factory=list)
    codice: str = ""
    persona: Optional[Persona] = None
    template_rendiconto: Optional[Path] = None

    @classmethod
    def from_yaml(cls, path: Path) -> "ConfigTimesheet":
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        prog = raw["progetto"]
        nome = prog["nome"]
        cup = prog.get("cup", "")
        codice = prog.get("codice", "")
        anno = int(prog["anno"])
        mesi = [int(m) for m in raw["mesi"]]
        ore_totali = float(raw["ore_totali"])

        template_rendiconto: Optional[Path] = None
        if "template_rendiconto" in prog:
            template_rendiconto = Path(prog["template_rendiconto"])

        giorni_interi = [
            _Intervallo(
                da=date.fromisoformat(str(gi["da"])),
                a=date.fromisoformat(str(gi["a"])),
            )
            for gi in raw.get("giorni_interi", [])
        ]

        ore_fisse = [
            _OraFissa(
                giorno=date.fromisoformat(str(of["data"])),
                ore=float(of["ore"]),
            )
            for of in raw.get("ore_fisse", [])
        ]

        persona: Optional[Persona] = None
        if "persona" in prog:
            p = prog["persona"]
            persona = Persona(
                nome=p.get("nome", ""),
                cognome=p.get("cognome", ""),
                codice_fiscale=p.get("codice_fiscale", ""),
                figura_professionale=p.get("figura_professionale", ""),
            )

        return cls(
            nome=nome,
            cup=cup,
            codice=codice,
            anno=anno,
            mesi=mesi,
            ore_totali=ore_totali,
            giorni_interi=giorni_interi,
            ore_fisse=ore_fisse,
            persona=persona,
            template_rendiconto=template_rendiconto,
        )


class TimesheetProgetto:
    """Calcola e scrive il timesheet mensile di progetto a partire da OO-DIU."""

    def __init__(
        self,
        oo_diu: pd.DataFrame,
        config: ConfigTimesheet,
        output_folder: Path,
    ) -> None:
        self._oo_diu = oo_diu
        self._config = config
        self._output_folder = output_folder
        self._result: Optional[dict[int, pd.DataFrame]] = None

    # ------------------------------------------------------------------
    # Helpers

    def _is_giorno_intero(self, d: date) -> bool:
        return any(gi.contains(d) for gi in self._config.giorni_interi)

    def _ore_fisse_per_giorno(self, d: date) -> Optional[float]:
        for of in self._config.ore_fisse:
            if of.giorno == d:
                return of.ore
        return None

    @staticmethod
    def _arrotonda_mezzora_inferiore(v: float) -> float:
        return floor(v * 2) / 2

    # ------------------------------------------------------------------
    # Core logic

    def _costruisci_calendario(self) -> pd.DataFrame:
        """Calendario completo dei mesi selezionati, unito ai dati OO-DIU."""
        cfg = self._config
        rows: list[date] = []
        for m in sorted(cfg.mesi):
            _, n_days = calendar.monthrange(cfg.anno, m)
            for d in range(1, n_days + 1):
                rows.append(date(cfg.anno, m, d))

        cal = pd.DataFrame({"date_only": rows})
        cal["date_dt"] = pd.to_datetime(cal["date_only"])

        oo = self._oo_diu.copy()
        oo = oo[oo["date"].dt.year == cfg.anno]
        oo = oo[oo["date"].dt.month.isin(cfg.mesi)]
        oo["date_only"] = oo["date"].dt.date
        oo = oo[["date_only", "Svolte"]].rename(columns={"Svolte": "ore_svolte"})

        merged = cal.merge(oo, on="date_only", how="left")
        merged["ore_svolte"] = merged["ore_svolte"].fillna(0.0)
        return merged

    def _calcola_ore_progetto(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self._config
        df = df.copy()

        df["_giorno_intero"] = df["date_only"].apply(self._is_giorno_intero)
        df["_ore_fisse"] = df["date_only"].apply(self._ore_fisse_per_giorno)

        def _ore_fisse_value(row: pd.Series) -> float:
            if row["_giorno_intero"]:
                return row["ore_svolte"]
            if row["_ore_fisse"] is not None:
                return row["_ore_fisse"]
            return float("nan")

        df["ore_progetto"] = df.apply(_ore_fisse_value, axis=1)

        ore_fisse_totali = df["ore_progetto"].fillna(0.0).sum()
        ore_residue = cfg.ore_totali - ore_fisse_totali

        if ore_residue < 0:
            print(
                f"ATTENZIONE: le ore già assegnate ({ore_fisse_totali:.2f}h) "
                f"superano le ore totali obiettivo ({cfg.ore_totali:.2f}h)."
            )

        # Eligible: no fixed assignment and ≥ MIN_ORE_ELIGIBILITA worked
        mask_eligible = df["ore_progetto"].isna() & (df["ore_svolte"] >= _MIN_ORE_ELIGIBILITA)
        n_eligible = int(mask_eligible.sum())

        # Fill non-eligible days with 0 before assigning distribution rate
        df["ore_progetto"] = df["ore_progetto"].fillna(0.0)

        if ore_residue > 0 and n_eligible == 0:
            print(
                f"ATTENZIONE: nessun giorno idoneo (≥{_MIN_ORE_ELIGIBILITA}h lavorative) "
                f"per distribuire {ore_residue:.2f}h residue."
            )
        elif ore_residue > 0 and n_eligible > 0:
            rate = ore_residue / n_eligible
            rate_rounded = self._arrotonda_mezzora_inferiore(rate)
            df.loc[mask_eligible, "ore_progetto"] = rate_rounded

            # Remainder (sum up per-day rounding losses) → last eligible day
            total_assigned = df["ore_progetto"].sum()
            remainder = round(cfg.ore_totali - total_assigned, 4)
            if remainder > 0:
                if remainder >= 0.5:
                    print(
                        f"ATTENZIONE: il resto da aggiungere all'ultimo giorno è "
                        f"{remainder:.2f}h ({remainder * 60:.1f} min ≥ 30 min). "
                        "Il totale sarà corretto ma l'ultimo giorno avrà un valore non multiplo di mezz'ora."
                    )
                last_idx = df.loc[mask_eligible].index[-1]
                df.at[last_idx, "ore_progetto"] = round(
                    df.at[last_idx, "ore_progetto"] + remainder, 4
                )

        df["ore_ordinarie"] = (df["ore_svolte"] - df["ore_progetto"]).clip(lower=0.0)
        df.drop(columns=["_giorno_intero", "_ore_fisse"], inplace=True)
        return df

    # ------------------------------------------------------------------
    # Public API

    def calcola(self) -> dict[int, pd.DataFrame]:
        """Ritorna {numero_mese: DataFrame con ore_progetto per giorno}. Risultato cached."""
        if self._result is not None:
            return self._result
        df = self._costruisci_calendario()
        df = self._calcola_ore_progetto(df)
        result: dict[int, pd.DataFrame] = {}
        for m in sorted(self._config.mesi):
            mdf = df[df["date_dt"].dt.month == m].copy()
            mdf.reset_index(drop=True, inplace=True)
            result[m] = mdf
        self._result = result
        return result

    def salva(self) -> None:
        cfg = self._config
        data = self.calcola()

        label_progetto = (
            f"Attività svolta sul progetto CUP: {cfg.cup}"
            if cfg.cup
            else "Attività svolta sul progetto"
        )

        output_folder = self._output_folder / "ore_svolte_per_giorno" / cfg.nome
        output_folder.mkdir(parents=True, exist_ok=True)

        print(f"\nTimesheet progetto '{cfg.nome}':")
        excel_fmt.ExcelFormatter.header_style = None
        total_ore = 0.0

        for month_num, mdf in data.items():
            month_name = _MONTH_NAMES[month_num - 1]
            mm = f"{month_num:02d}"

            mdf = mdf.copy()
            mdf["day"] = mdf["date_dt"].dt.strftime("%d")

            out = mdf[["day", "ore_progetto", "ore_ordinarie"]].copy()
            out["ore_altri_prog"] = 0
            out["ore_altro"] = 0
            out = out[["day", "ore_progetto", "ore_altri_prog", "ore_ordinarie", "ore_altro"]]
            out = out.transpose()

            out["label"] = pd.Series({
                "day": "Giorno",
                "ore_progetto": label_progetto,
                "ore_altri_prog": "Attività svolte su altri progetti",
                "ore_ordinarie": "Attività ordinaria",
                "ore_altro": "Altro (Malattia, Ferie..)",
            })

            cols = out.columns.tolist()
            out = out[[cols[-1]] + cols[:-1]]

            output_file = output_folder / f"{mm}_{month_name}.xlsx"
            write_excel_file(
                df=out,
                sheetname=month_name,
                output_file=output_file,
                index=False,
                startrow=0,
            )

            month_total = mdf["ore_progetto"].sum()
            total_ore += month_total
            print(f"  {mm}_{month_name}: {month_total:.2f}h → {output_file}")

        print(f"Totale ore progetto: {total_ore:.4f}h (obiettivo: {cfg.ore_totali}h)")
