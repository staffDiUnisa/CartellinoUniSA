import re
import pandas as pd

from pathlib import Path


def elabora_ore_eccedenti(df: pd.DataFrame, output_file: Path) -> None:
    df = df[["Stato", "Data", "Voci Base"]]
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
    riassunto = df[["Stato", "ore eccedenti", "minuti eccedenti"]].groupby(['Stato']).sum().reset_index().set_index(
        "Stato").sort_index(ascending=False)
    riassunto["OE"] = riassunto["ore eccedenti"] + (riassunto["minuti eccedenti"] // 60)
    riassunto["ME"] = riassunto["minuti eccedenti"] % 60
    output_writer = pd.ExcelWriter(output_file, engine='openpyxl', date_format=None, mode='w')
    df.to_excel(output_writer, index=False, sheet_name='dettaglio')
    output_writer.close()
    output_writer = pd.ExcelWriter(output_file, engine='openpyxl', date_format=None, mode='a')
    riassunto.to_excel(output_writer, index=False, sheet_name='riassunto')
    output_writer.close()
    print(riassunto)


def credito_ore(df: pd.DataFrame, output_file: Path) -> None:
    df = df[["Stato", "Data", "Voci Base", "Saldo (ore medie)"]]
    df["mese"] = df["Data"].str[-3:]
    df["saldo_ore"] = df["Saldo (ore medie)"].astype(int) * 60
    df["saldo_minuti"] = ((df["Saldo (ore medie)"] - df["Saldo (ore medie)"].astype(int)) * 100).astype(int)
    df["Saldo (ore medie)"] = df["saldo_ore"] + df["saldo_minuti"]
    df = df[["Stato", "mese", "Saldo (ore medie)"]].groupby(["Stato", "mese"]).sum().reset_index()
    df["credito"] = pd.to_datetime(df["Saldo (ore medie)"], unit="m").dt.strftime('%H:%M')
    custom_dict = {'gen': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'mag': 4, 'giu': 5, 'lug': 6, 'ago': 7, 'set': 8, 'ott': 9,
                   'nov': 10, 'dic': 11}
    df.sort_values(by=['mese'], key=lambda x: x.map(custom_dict), inplace=True)
    df[["Stato", "mese", "credito"]].to_excel(output_file, index=False, sheet_name='credito_ore')

    print(df)


def main():
    data_folder = Path('data')
    input_folder = data_folder / 'input'
    input_file = input_folder / 'cartellino.xlsx'
    output_folder = data_folder / 'output'
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / 'riposo_compensativo.xlsx'
    # cartellino = pd.concat([pd.read_excel(input_file, sheet_name="P1"), pd.read_excel(input_file, sheet_name="GG")])
    # cartellino.ffill(inplace=True)
    cartellino = pd.read_excel(input_file)
    cartellino["Voci Base"]=cartellino["Voci Base"].str.split(chr(160)+'&-&'+chr(160))
    cartellino = cartellino.explode("Voci Base")
    cartellino.to_excel(output_folder / 'cartellino.xlsx', index=False)
    elabora_ore_eccedenti(
        cartellino[(cartellino["Voci Base"].notnull()) & (cartellino["Voci Base"].str.match('^OE-DIU'))], output_file)
    credito_ore(cartellino[(cartellino["Voci Base"].notnull()) & (cartellino["Voci Base"].str.match('^OO-DIU'))],
                output_file=output_folder / 'credito_ore.xlsx')


if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    main()
