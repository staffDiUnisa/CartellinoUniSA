from datetime import datetime, timedelta
from math import ceil
from pathlib import Path

import pandas as pd

from processor.utils import write_excel_file


class Cartellino:
    df: pd.DataFrame
    input_folder: Path
    output_folder: Path
    min_hours_per_day: float
    max_project_hours_per_day: float
    max_project_hours: float

    def __init__(self, df: pd.DataFrame = None, input_folder: Path = None, output_folder: Path = None,
                 min_hours_per_day: float = 6, max_project_hours_per_day: float = None, max_project_hours: float = 400):
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
        self.min_hours_per_day = min_hours_per_day
        self.max_project_hours_per_day = max_project_hours_per_day
        self.max_project_hours = max_project_hours

    def splitta_ore(self, ore: float, hours_in_month: int, days_in_month: int = 20):
        if ore < self.min_hours_per_day:
            return 0

        ore_giornaliere = round(hours_in_month / days_in_month, 1)
        self.max_project_hours_per_day = self.max_project_hours_per_day if self.max_project_hours_per_day else ore_giornaliere
        ore_giornaliere = min(min(ore_giornaliere, self.max_project_hours_per_day), self.max_project_hours)
        self.max_project_hours -= ore_giornaliere
        self.max_project_hours = round(self.max_project_hours, 1)
        # print(f"giorni_nel_mese: {days_in_month} - ore giornaliere: {ore_giornaliere} - ore residue: {self.max_project_hours}")
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
        month_names = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre',
                       'ottobre', 'novembre', 'dicembre']
        giorni_anno = len(data[data.Svolte > self.min_hours_per_day]['date'])
        ore_gorno_medie = ceil(self.max_project_hours / giorni_anno)
        ore_progetto = 0
        for month in months:
            mdata = data[data['month'] == month].copy()
            mdata.reset_index(drop=True, inplace=True)
            giorni = len(mdata[mdata.Svolte > self.min_hours_per_day]['date'])
            ore_mese = ore_gorno_medie * giorni
            mdata['ore_progetto'] = mdata["Svolte"].apply(
                lambda x: self.splitta_ore(ore=x, hours_in_month=ore_mese, days_in_month=giorni))
            mdata['ore_altri_prog'] = 0
            mdata["ore_ordinarie"] = mdata["Svolte"] - mdata["ore_progetto"]
            mdata['ore_altro'] = 0

            ore_progetto += mdata['ore_progetto'].sum()

            mdata = mdata[['day', 'ore_progetto', 'ore_altri_prog', 'ore_ordinarie', 'ore_altro']].transpose()
            mdata["label"] = pd.Series(
                {'day': "Giorno", 'ore_progetto': "Attività svolta sul progetto CUP: D43C22005040001",
                 'ore_altri_prog': "Attività svolte su altri progetti", 'ore_ordinarie': "Attività ordinaria",
                 'ore_altro': "Altro (Malattia, Ferie..)"})
            print(mdata["label"])
            if self.output_folder is not None:
                month_name = month_names[int(month) - 1]
                output_folder = self.output_folder / 'ore_svolte_per_giorno'
                output_folder.mkdir(parents=True, exist_ok=True)
                columns = mdata.columns.tolist()
                columns = [columns[-1]] + columns[:-1]
                write_excel_file(df=mdata[columns], sheetname=month_name,
                                 output_file=output_folder / f"{month}_{month_name}.xlsx", index=False, startrow=0)
        print(f"Ore progetto totale: {ore_progetto}")

        return data
