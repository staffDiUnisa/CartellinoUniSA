# File di input

Percorsi relativi a `{data_folder}/{anno}/input/` — vedi [Struttura dati](data-layout.md).

## `date_escluse.txt`

Date da escludere dal calcolo delle ore eccedenti. Due formati supportati:

```
# Esclusione completa della giornata (DD-MM-YYYY)
16-01-2025
17-01-2025

# Sottrazione parziale: sottrae HH:MM dalle ore eccedenti di quel giorno
20-01-2025 03:30
```

## `riposi_usati.txt` *(opzionale)*

Usato solo se `min_date_riposi_usati` (`MIN_DATE_RIPOSI_USATI` nel percorso legacy) non è
impostato. Elenco delle date in cui sono stati fruiti riposi compensativi:

```
2025-06-26
2025-06-27
2025-07-15
```

## `data_ticket.txt`

Data da cui il ticket mensa viene pagato dall'ente (formato `DD-MM-YYYY`). Usato per distinguere
i ticket già ricevuti da quelli ancora da ricevere:

```
01-01-2025
```
