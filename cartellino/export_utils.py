from pathlib import Path

import pandas as pd

from cartellino.excel_utils import apply_table_format


def save_sheets(sheets: dict[str, pd.DataFrame], output_path: Path, fmt: str = "xlsx") -> list[Path]:
    """Scrive uno o più DataFrame su disco nel formato scelto (Fase 3/4 TODO.md:
    export on-demand in xlsx o csv).

    - `fmt == "xlsx"`: un unico file `output_path` con un foglio per voce di `sheets`,
      stile tabella Excel (comportamento storico dei vari `*.salva()`).
    - `fmt == "csv"`: un file `.csv` per foglio (`{output_path.stem}_{sheet}.csv`, o solo
      `{output_path.stem}.csv` se `sheets` ha una singola voce).

    Ritorna la lista dei path effettivamente scritti.
    """
    if fmt == "xlsx":
        from pandas.io.formats import excel as excel_fmt
        excel_fmt.ExcelFormatter.header_style = None
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                apply_table_format(writer.sheets[sheet_name], df)
        return [output_path]

    if fmt == "csv":
        written: list[Path] = []
        single = len(sheets) == 1
        for sheet_name, df in sheets.items():
            csv_path = (
                output_path.with_suffix(".csv")
                if single
                else output_path.with_name(f"{output_path.stem}_{sheet_name}.csv")
            )
            df.to_csv(csv_path, index=False)
            written.append(csv_path)
        return written

    raise ValueError(f"Formato export non supportato: {fmt!r}")
