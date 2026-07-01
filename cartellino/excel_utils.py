import pandas as pd


def apply_table_format(
    worksheet,
    df: pd.DataFrame,
    startrow: int = 0,
    startcol: int = 0,
    index: bool = False,
    table_style: str = "Table Style Medium 9",
) -> None:
    """Auto-fit columns and apply Excel table styling to an already-written sheet."""
    if index:
        col_headers = [df.index.name or ""] + list(df.columns)
        col_series = [df.index.astype(str)] + [df[c].astype(str) for c in df.columns]
    else:
        col_headers = list(df.columns)
        col_series = [df[c].astype(str) for c in df.columns]

    for i, (header, series) in enumerate(zip(col_headers, col_series)):
        data_max = int(series.str.len().fillna(0).max()) if len(series) > 0 else 0
        max_len = max(data_max, len(str(header))) + 2
        worksheet.set_column(startcol + i, startcol + i, max_len)

    n_rows = len(df)
    n_cols = len(col_headers)
    if n_rows > 0 and n_cols > 0:
        worksheet.add_table(
            startrow, startcol,
            startrow + n_rows, startcol + n_cols - 1,
            {
                "columns": [{"header": str(h)} for h in col_headers],
                "style": table_style,
            },
        )
