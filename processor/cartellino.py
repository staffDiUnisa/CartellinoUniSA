import pandas as pd

from pathlib import Path

from processor.utils import write_excel_file
from datetime import datetime, timedelta

class Cartellino:
    df: pd.DataFrame
    input_folder: Path
    output_folder: Path
    hours_in_month: int
    min_hours_per_day: int
    project_hours_per_day: int

    def __init__(self, df: pd.DataFrame = None, input_folder: Path = None, output_folder: Path = None, hours_in_month: int = 34, min_hours_per_day: int = 6, project_hours_per_day: int = None):
        if df is None:
            if not input_folder is None:
                self.df = pd.read_excel(input_folder / 'cartellino.xlsx')
            else:
                raise Exception("Cartellino non caricato")
        else:
            self.df = df

        self.input_folder = input_folder
        if output_folder is None:
            output_folder = input_folder
        self.output_folder = output_folder
        self.hours_in_month = hours_in_month
        self.min_hours_per_day = min_hours_per_day
        self.project_hours_per_day = project_hours_per_day

    def splitta_ore(self, ore: float, days_in_month: int = 20):
        if ore < self.min_hours_per_day:
            return 0

        ore_giornaliere = self.project_hours_per_day if self.project_hours_per_day else round(self.hours_in_month / days_in_month, 1)
        print(f"giorni_nel_mese: {days_in_month} - ore giornaliere: {ore_giornaliere}")
        return ore_giornaliere

    def print_head(self):
        print(self.df.head())

    def print_columns(self):
        print(self.df.columns)

    def ottieni_ore_svolte_per_giorno(self, current_year=2025) -> pd.DataFrame:
        data = self.df[(self.df.Codice == 'OO-DIU')][["date", "Codice", "Svolte"]]

        date_in_anno = []

        current_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year, 12, 31)

        while current_date <= end_date:
            date_in_anno.append(current_date)
            current_date += timedelta(days=1)

        date_df = pd.DataFrame(date_in_anno, columns=['date'])

        data = date_df.merge(data, on='date', how='left').sort_values(by='date')
        data.reset_index(drop=True, inplace=True)
        data['Svolte'] = data['Svolte'].fillna(0)
        data['Codice'] = data['Codice'].fillna('~')
        data['month'] = data['date'].apply(lambda x: x.strftime('%m'))
        data['day'] = data['date'].apply(lambda x: x.strftime('%d'))

        months = sorted(set(data['month'].unique()))
        month_names = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
        for month in months:
            mdata = data[data['month'] == month].copy()
            mdata.reset_index(drop=True, inplace=True)
            giorni =len(mdata[mdata.Svolte > 6]['date'])
            mdata['ore_progetto'] = mdata["Svolte"].apply(lambda x: self.splitta_ore(x, giorni))
            mdata['ore_altri_prog'] = 0
            mdata["ore_ordinarie"]=mdata["Svolte"]-mdata["ore_progetto"]
            mdata['ore_altro'] = 0

            mdata = mdata[['day', 'ore_progetto', 'ore_altri_prog', 'ore_ordinarie', 'ore_altro']].transpose()
            if self.output_folder is not None:
                month_name = month_names[int(month)-1]
                output_folder = self.output_folder / 'ore_svolte_per_giorno'
                output_folder.mkdir(parents=True, exist_ok=True)
                write_excel_file(df=mdata, sheetname=month_name, output_file=output_folder / f"{month}_{month_name}.xlsx", index=True, startrow=1)

        return data