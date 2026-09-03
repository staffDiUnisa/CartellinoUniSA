# GUI — interfaccia grafica

Interfaccia desktop basata su [PySide6](https://doc.qt.io/qtforpython-6/), pensata per chi
preferisce non usare il terminale: stesse funzionalità della TUI, senza richiedere Python/uv se
si usa l'eseguibile standalone.

Condivide dati, `config.toml` e credenziali con la TUI — sono due frontend sullo stesso layer di
dominio, non due prodotti separati: la stessa cartella dati fissa nella home dell'utente
(`~/.cartellino_unisa/` su macOS/Linux, `%LOCALAPPDATA%\cartellino_unisa\` su Windows) e lo
stesso `data/v2/{anno}/`.

```bash
mise run gui
# oppure
uv run python cartellino_gui.py
```

## Schermate disponibili

Stesse della TUI, navigazione da pulsante invece che da scorciatoia da tastiera:

| Schermata | Descrizione |
|-----------|---------|
| **Onboarding** | Mostrata automaticamente se manca `config.toml`; imposta anno, data minima riposi, credenziali (opzionali qui) |
| **Dashboard** | Home: eccezioni del mese, saldo ore, riepilogo riposi compensativi, ferie/PMF usati, ticket da ricevere, data ultimo aggiornamento |
| **Aggiornamento** | Scelta del metodo di autenticazione (Credenziali UNISA/SPID/CIE, UNISA disabilitata fuori rete) e download con log in tempo reale |
| **Report** | Generazione on-demand di riposo compensativo, credito ore, statistiche, ore giornaliere, nel formato scelto in Impostazioni |
| **Timesheet progetto** | Selezione (o "Sfoglia...") ed esecuzione di uno YAML esistente in `timesheet/` — vedi [Timesheet e rendiconto](../dati-cartellino/timesheet.md) |
| **Statistiche** | Visualizzazione a schermo (non export) delle categorie di `statistiche.xlsx` — un pulsante per categoria, disabilitato se la categoria non ha dati |
| **Impostazioni** | Anno, data minima riposi, formato export, codici dashboard, cartella dati/output (con selettore nativo del sistema operativo), data ticket mensa, gestione date escluse; credenziali UniSA modificabili in una finestra dedicata |

Assente rispetto alla TUI: il campo "Terminale (solo macOS)" in Impostazioni (non applicabile, la
GUI è già una finestra nativa).

A differenza della TUI, chiudere la finestra (dalla X, dal pulsante **🚪 Esci** in Dashboard, o
con Alt+F4/Cmd+Q) chiede sempre conferma prima di uscire.
