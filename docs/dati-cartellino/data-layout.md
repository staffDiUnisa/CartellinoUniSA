# Struttura dati (versione corrente)

```
CartellinoUniSA/
├── templates/
│   └── timesheet_progetto_template.yaml  ← template per il timesheet di progetto
├── timesheet/                            ← YAML personali (ignorati da git)
│   └── mio_progetto.yaml                 ← copia e adatta dal template
└── data/v2/
    └── {anno}/
        ├── input/
        │   ├── cartellino.feather     ← scaricato dal downloader (formato primario, Feather/pyarrow)
        │   ├── cartellino.xlsx        ← solo legacy: se presente e manca il .feather, viene
        │   │                            migrato automaticamente una tantum al primo avvio
        │   ├── date_escluse.txt       ← date da escludere/ridurre dal calcolo OE — vedi File di input
        │   ├── riposi_usati.txt       ← fallback per riposi già fruiti (se non impostata min_date_riposi_usati)
        │   └── data_ticket.txt        ← data da cui i ticket sono stati pagati
        └── output/
            ├── cartellino.xlsx               ← cartellino con colonna Codice aggiunta
            ├── riposo_compensativo.xlsx      ← dettaglio e riassunto ore eccedenti
            ├── riposi_compensativi.txt       ← riepilogo testuale riposi
            ├── credito_ore.xlsx              ← credito ore mensile
            ├── statistiche.xlsx              ← più fogli (ticket, ferie, malattia, ...)
            ├── ore_giornaliere.xlsx          ← ore OO-DIU per giorno, per mese
            └── ore_svolte_per_giorno/
                └── {nome_progetto}/          ← generato dal timesheet di progetto
                    ├── 01_gennaio.xlsx
                    ├── 02_febbraio.xlsx
                    └── ...
```

Vedi il dettaglio di ciascun file: [File di input](input-files.md), [Output generati](output-files.md).

!!! note
    Questa struttura è relativa alla cartella del repository quando si usa la CLI (`cartellino_v2.py`).
    Per gli eseguibili standalone (TUI/GUI), la stessa struttura (`data/v2/` in poi) vive dentro
    `~/.cartellino_unisa/` (`%LOCALAPPDATA%\cartellino_unisa\` su Windows), non nella cartella da
    cui si lancia il binario.

Il percorso legacy (`main.py`) usa invece `data/{anno}/` (senza `v2/`) — vedi
[versione legacy](../usage/legacy.md).
