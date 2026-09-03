# Codici del cartellino

Ogni riga del cartellino scaricato contiene una o più "Voci Base" identificate da un codice
breve. Questi sono i codici riconosciuti dalla pipeline di elaborazione:

| Codice | Significato |
|--------|-------------|
| `OE-DIU` | Ore eccedenti (straordinario diurno) |
| `OO-DIU` | Ore ordinarie lavorate in giornata |
| `SRC` | Riposo compensativo già fruito |
| `TCK` | Ticket mensa |
| `VSG` | Visita specialistica |
| `STRSOS` / `FSTLAV` / `OS-FSD` | Straordinario |
| `FER` / `FEV` / `FST` | Ferie/festività |
| `MAL` / `RIC` | Malattia/ricovero |
| `VIG` | Vigilanza concorsi |
| `PMF` | Permessi per gravi motivi familiari |
| `ERIT` | Entrata in ritardo |
| `CRE` | Credito ore (scostamento positivo) |
| `SCN` | Scostamento negativo — va **sottratto**, non sommato, nei calcoli di saldo (vedi sotto) |

## Saldo ore mensile della dashboard

La dashboard (TUI e GUI) mostra un saldo ore mensile calcolato sommando i codici configurati in
`dashboard_balance_codes` (default `CRE`, `OE-DIU`, `SCN` — vedi
[Configurazione](../getting-started/configuration.md)). `SCN` rappresenta uno scostamento
negativo (es. un'uscita anticipata non giustificata) e viene sottratto dal totale invece che
sommato: un mese con +00:07 di base e 00:26 di `SCN` produce un saldo di **-00:19**, evidenziato
in rosso; un saldo positivo è verde, un saldo esattamente a zero è blu.

Questa distinzione (quali codici sono "sottrattivi") è oggi limitata al solo `SCN`, definita
internamente come costante (`SUBTRACTIVE_CODES` in `cartellino/ore_helpers.py`) e non
configurabile dall'utente: è un fatto noto sul sistema di rilevazione presenze, non una
preferenza personalizzabile.
