# Data flow

Il flusso dati segue sempre lo stesso schema, indipendentemente dal frontend (CLI/TUI/GUI):

```
presenze.unisa.it
       │  (Selenium: login + scraping paginato)
       ▼
{data_folder}/{anno}/input/cartellino.feather   ← formato primario (Feather/pyarrow)
       │
       │  + date_escluse.txt, riposi_usati.txt, data_ticket.txt (input aggiuntivi manuali)
       │
       ▼  elaborazione (esplosione "Voci Base", estrazione Codice, calcoli)
       │
{data_folder}/{anno}/output/
       ├── cartellino.xlsx
       ├── riposo_compensativo.xlsx
       ├── riposi_compensativi.txt
       ├── credito_ore.xlsx
       ├── statistiche.xlsx
       ├── ore_giornaliere.xlsx
       └── ore_svolte_per_giorno/{progetto}/   (solo se richiesto il timesheet di progetto)
```

Dettaglio dei singoli file: [Struttura dati](../dati-cartellino/data-layout.md),
[File di input](../dati-cartellino/input-files.md), [Output generati](../dati-cartellino/output-files.md).

Il percorso legacy (`main.py`/`process.py`) usa lo stesso schema di output ma legge
`cartellino.xlsx` direttamente (nessun formato Feather), in `data/{anno}/` — vedi
[versione legacy](../usage/legacy.md).

Per il dettaglio implementativo di ogni fase (scraping, esplosione righe, calcolo dei riposi
compensativi, ecc.), vedi la [Guida per sviluppatori](../developer-guide/architecture.md).
