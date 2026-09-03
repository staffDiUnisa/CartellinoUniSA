# TUI — interfaccia testuale

Interfaccia interattiva basata su [Textual](https://textual.textualize.io/), con dashboard,
gestione guidata di config/credenziali e report on-demand.

Dati e log salvati in una cartella fissa nella home dell'utente — **non** relativa alla cartella
da cui si lancia l'eseguibile (importante per il binario standalone, lanciabile da qualunque
posizione): `~/.cartellino_unisa/` su macOS/Linux, `%LOCALAPPDATA%\cartellino_unisa\` su Windows.
Dentro: `data/v2/{anno}/` (vedi [Struttura dati](../dati-cartellino/data-layout.md)) e `cartellino_tui.log`.

```bash
mise run tui
# oppure
uv run python cartellino_tui.py
```

## Schermate disponibili

| Schermata | Scorciatoia | Descrizione |
|-----------|:---:|---------|
| **Onboarding** | — | Mostrata automaticamente se manca `config.toml`; imposta anno, data minima riposi, credenziali (opzionali qui) |
| **Dashboard** | — | Home: eccezioni del mese, saldo ore, riepilogo riposi compensativi, ferie/PMF usati, ticket da ricevere, data ultimo aggiornamento |
| **Aggiornamento** | `r` | Scelta del metodo di autenticazione (Credenziali UNISA/SPID/CIE, UNISA disabilitata fuori rete) e download con log in tempo reale |
| **Report** | `p` | Generazione on-demand di riposo compensativo, credito ore, statistiche, ore giornaliere, nel formato scelto in Impostazioni |
| **Timesheet progetto** | `t` | Selezione ed esecuzione di uno YAML esistente in `timesheet/` — vedi [Timesheet e rendiconto](../dati-cartellino/timesheet.md) |
| **Statistiche** | `v` | Visualizzazione a schermo (non export) delle categorie di `statistiche.xlsx`: Buoni pasto, Ferie, Permessi per motivi familiari, Entrata in ritardo, Straordinari, Visite Specialistiche, Malattia — un pulsante per categoria, colori diversi, disabilitato se la categoria non ha dati |
| **Impostazioni** | `s` | Anno, data minima riposi, formato export, codici dashboard, cartella dati/output (con selettore), data ticket mensa, gestione date escluse (`date_escluse.txt`); credenziali UniSA modificabili in una schermata dedicata |

`Esc` torna alla schermata precedente, `q` esce dall'app (senza richiesta di conferma, a
differenza della GUI).
