import pandas as pd

from pathlib import Path
from pandas.io.formats import excel

def write_excel_file(df: pd.DataFrame, output_file: Path, sheetname: str = "Sheet1", startrow: int = 0, index: bool = False):
    excel.ExcelFormatter.header_style = None

    writer = pd.ExcelWriter(output_file,
                            engine='xlsxwriter',
                            datetime_format="dd/mm/yyyy",
                            date_format="dd/mm/yyyy")

    df.to_excel(writer,sheet_name=sheetname,index=index, startrow=startrow)

    worksheet = writer.sheets[sheetname]
    for idx, col in enumerate(df):
        series = df[col]
        max_len = max((
            series.astype(str).map(len).max(),
            len(str(series.name))
        )) + 1
        worksheet.set_column(idx, idx, max_len)
    writer.close()