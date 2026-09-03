# Output generati

Percorsi relativi a `{data_folder}/{anno}/output/` — vedi [Struttura dati](data-layout.md).

## `riposo_compensativo.xlsx`

Due fogli:

- **dettaglio**: ore eccedenti giornaliere con stato, data, voce base e intervallo (hh:mm)
- **riassunto**: totale ore/minuti eccedenti raggruppati per stato di elaborazione

## `riposi_compensativi.txt`

Riepilogo testuale dei riposi compensativi maturati, con indicazione delle date utilizzate e
delle ore mancanti al completamento:

```
_________________________________________________
Riposo compensativo 1: - usato per il 26-06-2025
_________________________________________________
    - 01-01-2025 -> 02:30 [OK]
    - 02-01-2025 -> 01:45 [OK]
    ...
_________________________________________________
Riposo compensativo 2: - ore necessarie al completamento: 5:42
_________________________________________________
    - 06-01-2025 -> 01:30 [OK]
_________________________________________________
```

## `credito_ore.xlsx`

Credito ore mensile per stato di elaborazione, con e al netto dei riposi maturati.

## `statistiche.xlsx`

File multi-foglio con:

| Foglio | Contenuto |
|--------|-----------|
| `ticket` | Giorni con ticket mensa, valore maturato e da ricevere |
| `statistica_ticket` | Conteggio ticket per mese e stato |
| `visite_specialistiche` | Giornate con visita specialistica (`VSG`) |
| `straordinari` | Giornate con straordinario (`STRSOS`, `FSTLAV`, `OS-FSD`) |
| `malattia` | Giornate di malattia/ricovero (`MAL`, `RIC`) |
| `ferie` | Giornate di ferie/festività (`FER`, `FEV`, `FST`) |
| `vigilanza_concorsi` | Giornate di vigilanza concorsi (`VIG`) |
| `permessi_gravi_motivi` | Permessi per gravi motivi (`PMF`) |
| `entrata_ritardo` | Giornate con entrata in ritardo (`ERIT`) |

Vedi anche [Codici del cartellino](../reference/codes.md).

## `ore_giornaliere.xlsx`

Ore `OO-DIU` (ore ordinarie) per ogni giornata lavorativa, organizzate per mese in fogli separati.
