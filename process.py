import os
import re
from cmath import isnan
from datetime import datetime,timedelta
from fileinput import lineno

import pandas as pd

from pathlib import Path
from typing import List, Dict

from model.ore_inserite import OreInserite
from model.riposo_compensativo import RiposoCompensativo
from dotenv import load_dotenv

load_dotenv()

codici_usati = []

current_year=2025

custom_dict = {'gen': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'mag': 4, 'giu': 5, 'lug': 6, 'ago': 7, 'set': 8, 'ott': 9,
                   'nov': 10, 'dic': 11}

def scrivi_dataframe(dfs: Dict[str, pd.DataFrame], output_file: Path) -> None:
    """
    Scrive i DataFrame in un file Excel con più fogli.
    :param dfs: Dizionario con i nomi dei fogli come chiavi e i DataFrame come valori.
    :param output_file: Percorso del file di output.
    """
    print(f"Scrivo le statistiche ottenute su {output_file}")
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def scrivi_riposo_compensativo(df: pd.DataFrame, output_file: Path) -> None:
    print(f"Scrivo riposi compensativo su {output_file}")
    base_date = datetime(1900, 1, 1)
    df['intervallo'] = df['intervallo'].apply(lambda x: base_date + x)

    riassunto = df[["Stato", "ore eccedenti", "minuti eccedenti"]].groupby(['Stato']).sum().reset_index().set_index(
        "Stato").sort_index(ascending=False)
    riassunto["OE"] = riassunto["ore eccedenti"] + (riassunto["minuti eccedenti"] // 60)
    riassunto["ME"] = riassunto["minuti eccedenti"] % 60
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df[["Stato", "Data", "Voci Base", "ore eccedenti", "minuti eccedenti", "intervallo"]].to_excel(writer, sheet_name='dettaglio', index=False)
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['dettaglio']

        # Format the time column
        time_format = workbook.add_format({'num_format': 'hh:mm'})

        # Write the time column with proper formatting
        for row_num, value in enumerate(df['intervallo'], 1):
            worksheet.write_datetime(row_num, 5, value, time_format)  # Column index 5 for column F
        riassunto.to_excel(writer, index=False, sheet_name='riassunto')

def scrivi_credito_ore(df: pd.DataFrame, output_file: Path) -> None:
    print(f"Scrivo credito ore su {output_file}")
    df[["Stato", "mese", "credito","credito_ore_residuo"]].rename(columns={"Stato":"Stato elaborazione mese",
             "mese":"Mese",
             "credito": "Credito ore",
             "credito_ore_residuo": "Credito ore al netto dei riposi maturati"}).to_excel(output_file, index=False, sheet_name='credito_ore')

def scrivi_riposi_compensativi(riposi_compensativi: List[RiposoCompensativo], output_file: Path) -> None:
    print(f"Scrivo riposi compensativi su {output_file}")
    with open(output_file, mode='w') as file:
        for riposo in riposi_compensativi:
            file.write("_________________________________________________\n")
            file.write(f"Riposo compensativo {riposo.id}:")
            if riposo.data:
                file.write(f" - usato per il {riposo.data}")
            if riposo.ore_mancanti() > timedelta(hours=0, minutes=0):
                hours, minutes = (riposo.ore_mancanti().seconds // 3600, (riposo.ore_mancanti().seconds // 60) % 60)
                file.write(f" - ore necessarie al completamento: {hours}:{minutes}")
            file.write("\n")
            file.write("_________________________________________________\n")
            for ore in riposo.ore_inserite:
                hours, minutes = (ore.ore.seconds // 3600, (ore.ore.seconds // 60) % 60)
                stato = "OK" if ore.stato == "ELAB P1" else "NO"
                data_ore=get_date_from_string(ore.data, current_year).strftime("%d-%m-%Y")
                file.write(f"\t- {data_ore} -> {hours:02}:{minutes:02} [{stato}]\n")
            file.write("_________________________________________________\n")

def elabora_ore_eccedenti(df: pd.DataFrame, excluded_dates_file: Path) -> pd.DataFrame:
    df = df[["Stato", "Data", "Voci Base", "date"]]
    with open(excluded_dates_file, 'r') as file:
        excluded_dates = []
        for line in file:
            line = line.strip()
            preg_datetime = re.match(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$', line)
            if preg_datetime is not None:
                data_con_ore = datetime.strptime(line, "%d-%m-%Y %H:%M")
            else:
                data_con_ore = datetime.strptime(line, "%d-%m-%Y")
            excluded_dates.append(data_con_ore)
        if excluded_dates and len(excluded_dates) > 0:
            df = df[~df["date"].isin([d.date() for d in excluded_dates if d.time() <= datetime.strptime("00:00", "%H:%M").time()])]
    ore_eccedenti = []
    for values in df['Voci Base']:
        ore_eccedenti.append(re.search(r'\d\d\.', values).group()[:-1])
    df["ore eccedenti"] = ore_eccedenti
    df["ore eccedenti"] = df["ore eccedenti"].astype(int)
    minuti_eccedenti = []
    for values in df['Voci Base']:
        minuti_eccedenti.append(re.search(r'\.\d\d', values).group()[1:])
    df["minuti eccedenti"] = minuti_eccedenti
    df["minuti eccedenti"] = df["minuti eccedenti"].astype(int)
    for d in excluded_dates:
        if d.time() > datetime.strptime("00:00", "%H:%M").time():
            minuti_eccedenti = df.loc[df.date == d.strftime("%d-%m-%Y"), "minuti eccedenti"].values[0]
            ore_eccedenti = df.loc[df.date == d.strftime("%d-%m-%Y"), "ore eccedenti"].values[0]
            minuti_eccedenti = minuti_eccedenti - d.minute
            ore_eccedenti = ore_eccedenti - d.hour
            ore_eccedenti = ore_eccedenti -1 if minuti_eccedenti < 0 else ore_eccedenti
            minuti_eccedenti = minuti_eccedenti + 60 if minuti_eccedenti < 0 else minuti_eccedenti
            df.loc[df.date == d.strftime("%d-%m-%Y"), "minuti eccedenti"] = minuti_eccedenti
            df.loc[df.date == d.strftime("%d-%m-%Y"), "ore eccedenti"] = ore_eccedenti
    df['intervallo'] = pd.to_timedelta(df['ore eccedenti'], unit='h') + pd.to_timedelta(df['minuti eccedenti'], unit='m')
    return df

def credito_ore(df: pd.DataFrame, oe: pd.DataFrame, excluded_dates_file: Path) -> pd.DataFrame:
    df = df[["Stato", "Data", "Voci Base", "Saldo (ore medie)", "date"]]
    with open(excluded_dates_file, 'r') as file:
        excluded_dates = []
        for line in file:
            line = line.strip()
            preg_datetime = re.match(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$', line)
            if preg_datetime is not None:
                data_con_ore = datetime.strptime(line, "%d-%m-%Y %H:%M")
            else:
                data_con_ore = datetime.strptime(line, "%d-%m-%Y")
            excluded_dates.append(data_con_ore)
        if excluded_dates and len(excluded_dates) > 0:
            df = df[~df["date"].isin([d.date() for d in excluded_dates])]
    df["mese"] = df["Data"].str[-3:]
    df["saldo_ore"] = df["Saldo (ore medie)"].astype(int) * 60
    df["saldo_minuti"] = ((df["Saldo (ore medie)"] - df["Saldo (ore medie)"].astype(int)) * 100).astype(int)
    df["Saldo (ore medie)"] = df["saldo_ore"] + df["saldo_minuti"]
    oe["mese"] = oe["Data"].str[-3:]
    oe["Riposo Compensativo"] = (oe["ore eccedenti"] * 60) + oe["minuti eccedenti"]
    oe = oe[["Stato", "mese", "Riposo Compensativo"]].groupby(["Stato", "mese"]).sum().reset_index()

    oe.sort_values(by=['mese'], key=lambda x: x.map(custom_dict), inplace=True)
    df = df[["Stato", "mese", "Saldo (ore medie)"]].groupby(["Stato", "mese"]).sum().reset_index()
    df = pd.merge(df, oe[["Stato", "mese", "Riposo Compensativo"]], on=["Stato", "mese"], how="outer")
    df['Riposo Compensativo'] = df["Riposo Compensativo"].fillna(0).astype(int)
    df["ore_residue"] = df["Saldo (ore medie)"] - df["Riposo Compensativo"]
    df["ore_residue"] = df["ore_residue"].apply(lambda x: max(x, 0))  # Assicurati che le ore residue non siano negative
    df["credito"] = pd.to_datetime(df["Saldo (ore medie)"], unit="m").dt.strftime('%H:%M')
    df["credito_ore_residuo"] = pd.to_datetime(df["ore_residue"], unit="m").dt.strftime('%H:%M')

    df.sort_values(by=['mese'], key=lambda x: x.map(custom_dict), inplace=True)
    return df

def raggruppa_ore_eccedenti(df: pd.DataFrame, riposi_usati: List[str]) -> List[RiposoCompensativo]:
    riposi_compensativi = []
    id = 1
    riposo_compensativo = RiposoCompensativo(id=id)
    for index, row in df.iterrows():
        if riposo_compensativo.ore_mancanti() >= row['intervallo']:
            riposo_compensativo.ore_inserite.append(OreInserite(id=index, data=row['Data'], ore=row['intervallo'], stato=row['Stato']))
        else:
            residuo = row['intervallo'] - riposo_compensativo.ore_mancanti()
            riposo_compensativo.ore_inserite.append(OreInserite(id=index, data=row['Data'], ore=riposo_compensativo.ore_mancanti(), stato=row['Stato']))
            if len(riposi_usati) > 0:
                riposo_compensativo.data = riposi_usati.pop(0)
            riposi_compensativi.append(riposo_compensativo)
            id+=1
            riposo_compensativo = RiposoCompensativo(id=id,ore_inserite=[OreInserite(id=index, data=row['Data'], ore=residuo, stato=row['Stato'])])
    riposi_compensativi.append(riposo_compensativo)
    return riposi_compensativi

def get_date_usate_riposi_compensativi(riposi_usati_file: Path) -> List[str]:
    riposi_usati = []
    if riposi_usati_file.exists():
        with open(riposi_usati_file, 'r') as file:
            for line in file:
                riposi_usati.append(line.strip())
    return riposi_usati

def get_date_from_string(date_string: str, year:int) -> datetime:
    regex = r"[a-z]{3}\s(\d\d?)\s([a-z]{3})"
    date_search = re.search(regex, date_string, re.IGNORECASE)
    day = int(date_search.group(1))
    month_dict = {
        "gen": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "mag": 5,
        "giu": 6,
        "lug": 7,
        "ago": 8,
        "set": 9,
        "ott": 10,
        "nov": 11,
        "dic": 12
    }
    month = month_dict[date_search.group(2)]
    try:
        return datetime(year, month, day)
    except ValueError:
        print(f"Invalid date: {day}-{month}-{year}")
        raise ValueError("Invalid date format")

def get_riposi_compensativi_usati_from_data(df: pd.DataFrame, min_date:datetime) -> List[str]:
    df = df[df.date > min_date]
    riposi_usati = []
    for index, row in df.iterrows():
        riposi_usati.append(row['date'].strftime('%d-%m-%Y'))
    return riposi_usati

def extract_codice(voci_base: str) -> str:
    """
    Estrae il codice da una stringa di voci base.
    Il codice è definito come la parte della stringa che precede il primo trattino.
    """
    match = re.search(r'[A-Z]+-?[A-Z][A-Z]+', voci_base)
    if match:
        return match.group(0).strip()
    return '-'

def ottieni_visite_specialistiche(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("VSG")
    cartellino = cartellino[cartellino["Codice"] == "VSG"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_straordinari(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("STRSOS")
    codici_usati.append("FSTLAV")
    codici_usati.append("OS-FSD")
    cartellino = cartellino[(cartellino["Codice"] == "STRSOS") | (cartellino["Codice"] == "FSTLAV") | (cartellino["Codice"] == "OS-FSD")]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_ticket(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("TCK")
    cartellino = cartellino[cartellino["Codice"] == "TCK"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_malattia(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("MAL")
    codici_usati.append("RIC")
    cartellino = cartellino[(cartellino["Codice"] == "MAL") | (cartellino["Codice"] == "RIC")]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_ferie(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("FER")
    codici_usati.append("FEV")
    codici_usati.append("FST")
    cartellino = cartellino[(cartellino["Codice"] == "FER") | (cartellino["Codice"] == "FEV") | (cartellino["Codice"] == "FST")]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_permesso_gravi_motivi(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("PMF")
    cartellino = cartellino[cartellino["Codice"] == "PMF"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_entrata_ritardo(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("ERIT")
    cartellino = cartellino[cartellino["Codice"] == "ERIT"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_vigilanza_concorsi(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("VIG")
    cartellino = cartellino[cartellino["Codice"] == "VIG"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_motivi_di_servizio(cartellino: pd.DataFrame) -> pd.DataFrame:
    global codici_usati
    codici_usati.append("AMU")
    cartellino = cartellino[cartellino["Codice"] == "AMU"]
    cartellino = cartellino[["Stato", "Data", "Voci Base"]]
    return cartellino

def ottieni_codici_non_usati(cartellino: pd.DataFrame) -> List[str]:
    all_codes = set(cartellino["Codice"].unique())
    used_codes = set(codici_usati)
    unused_codes = all_codes - used_codes
    return list(unused_codes)

def processa_dati(data_folder: Path) -> None:
    global codici_usati
    global current_year

    current_year = int(os.getenv("CURRENT_YEAR"))
    try:
        min_date = datetime.strptime(f"{current_year}-{os.getenv('MIN_DATE_RIPOSI_USATI')}", "%Y-%m-%d")
        print(f"Data da cui verranno considerati i Riposi Compensativi Usati: {min_date.strftime('%d-%m-%Y')}")
    except ValueError:
        print("Errore nel processare la variabile MIN_DATE_RIPOSI_USATI. Userò il file dei riposi usati, se disponibile, per determinare quelli già usati")
        min_date = None
    input_folder = data_folder / 'input'
    if input_folder.exists():
        input_folder.mkdir(parents=True, exist_ok=True)
    input_file = input_folder / 'cartellino.xlsx'
    excluded_dates_file = input_folder / 'date_escluse.txt'
    riposi_usati_file = input_folder / 'riposi_usati.txt'
    output_folder = data_folder / 'output'
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / 'riposo_compensativo.xlsx'
    credito_ore_file = output_folder / 'credito_ore.xlsx'
    riposi_compensativi_file = output_folder / 'riposi_compensativi.txt'
    cartellino = pd.read_excel(input_file)
    cartellino["Voci Base"]=cartellino["Voci Base"].str.split(chr(160)+'&-&'+chr(160))
    cartellino["date"]=cartellino["Data"].apply(lambda x: get_date_from_string(x, current_year))
    cartellino = cartellino.explode("Voci Base")
    cartellino["Voci Base"]=cartellino["Voci Base"].fillna("____")
    cartellino["Codice"]=cartellino["Voci Base"].apply(lambda x: extract_codice(x))
    # print(cartellino["Codice"].unique())
    cartellino.to_excel(output_folder / 'cartellino.xlsx', index=False)
    oe = elabora_ore_eccedenti(
        cartellino[cartellino["Codice"]=="OE-DIU"],
        excluded_dates_file)
    codici_usati.append("OE-DIU")
    if min_date:
        riposi_usati = get_riposi_compensativi_usati_from_data(
            df=cartellino[cartellino["Codice"]=="SRC"],
            min_date=min_date)
    else:
        riposi_usati = get_date_usate_riposi_compensativi(riposi_usati_file)
    codici_usati.append("SRC")
    riposi_compensativi= raggruppa_ore_eccedenti(oe, riposi_usati)
    scrivi_riposo_compensativo(oe, output_file)
    scrivi_riposi_compensativi(riposi_compensativi, riposi_compensativi_file)
    ce = credito_ore(
        df=cartellino[cartellino["Codice"]=="OO-DIU"],
        oe=oe,
        excluded_dates_file=excluded_dates_file,
    )
    codici_usati.append("OO-DIU")
    scrivi_credito_ore(ce, credito_ore_file)
    vsg = ottieni_visite_specialistiche(cartellino)
    str = ottieni_straordinari(cartellino)
    tck = ottieni_ticket(cartellino)
    tck_stat = tck.copy()
    tck_stat["mese"] = tck_stat["Data"].str[-3:]
    tck_stat = tck_stat[["Stato","mese","Data"]].groupby(["Stato", "mese"]).count().reset_index()
    tck_stat.rename(columns={"Data": "Numero Ticket"}, inplace=True)
    tck_stat.sort_values(by=['mese'], key=lambda x: x.map(custom_dict), inplace=True)
    mal = ottieni_malattia(cartellino)
    fer = ottieni_ferie(cartellino)
    vig = ottieni_vigilanza_concorsi(cartellino)
    pmf = ottieni_permesso_gravi_motivi(cartellino)
    erit = ottieni_entrata_ritardo(cartellino)

    dfs = {
        "visite_specialistiche": vsg,
        "straordinari": str,
        "ticket": tck,
        "statistica_ticket": tck_stat,
        "malattia": mal,
        "ferie": fer,
        "vigilanza_concorsi": vig,
        "permessi_gravi_motivi": pmf,
        "entrata_ritardo": erit,
    }
    scrivi_dataframe(dfs, output_folder / 'statistiche.xlsx')

    print("Codici usati per le statistiche del cartellino:")
    print(codici_usati)

    print("Codici non usati per le statistiche del cartellino:")
    print(ottieni_codici_non_usati(cartellino))


def run() -> None:
    data_folder = Path('data')
    processa_dati(data_folder)

def main() -> None:
    run()

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    main()
    print("Script completato")
