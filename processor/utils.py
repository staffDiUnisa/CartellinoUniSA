import pandas as pd

from pathlib import Path
from pandas.io.formats import excel

def write_excel_file(df: pd.DataFrame, output_file: Path, sheetname: str = "Sheet1", startrow: int = 0, index: bool = False, datetime_format: str = "dd/mm/yyyy", date_format: str = "dd/mm/yyyy"):
    excel.ExcelFormatter.header_style = None

    writer = pd.ExcelWriter(output_file,
                            engine='xlsxwriter',
                            datetime_format=datetime_format,
                            date_format=date_format)

    df.to_excel(writer,sheet_name=sheetname,index=index, startrow=startrow)

    worksheet = writer.sheets[sheetname]
    col_headers = ([df.index.name or ""] if index else []) + [str(c) for c in df.columns]
    n_cols = len(col_headers)
    for i, header in enumerate(col_headers):
        if index and i == 0:
            series = df.index.astype(str)
        else:
            series = df.iloc[:, i - (1 if index else 0)].astype(str)
        data_max = int(series.str.len().fillna(0).max()) if len(series) > 0 else 0
        max_len = max(data_max, len(header)) + 2
        worksheet.set_column(i, i, max_len)

    n_rows = len(df)
    if n_rows > 0 and n_cols > 0:
        worksheet.add_table(
            startrow, 0,
            startrow + n_rows, n_cols - 1,
            {
                "columns": [{"header": h} for h in col_headers],
                "style": "Table Style Medium 9",
            },
        )
    writer.close()