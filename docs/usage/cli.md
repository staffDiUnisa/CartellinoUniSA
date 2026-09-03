# CLI — `cartellino_v2.py`

Uso non interattivo/scriptabile. Dati salvati in `data/v2/{anno}/` (relativo alla cwd) — vedi
[Struttura dati](../data/data-layout.md).

```bash
mise run app
# oppure
uv run python cartellino_v2.py
```

All'avvio, se non vengono passati flag, viene chiesto interattivamente se scaricare il cartellino
aggiornato e, in tal caso, con quale metodo di autenticazione:

```
Scegli il metodo di autenticazione:
  1. Credenziali UNISA   ← disponibile solo sulla rete universitaria
  2. SPID
  3. CIE
```

Per SPID e CIE il browser si apre e attende che l'utente completi manualmente il login (timeout
10 minuti).

## Opzioni non interattive

```bash
# Salta il download e usa i dati già presenti
uv run python cartellino_v2.py --no-aggiorna-cartellino

# Aggiorna scegliendo il metodo di autenticazione senza prompt interattivo
uv run python cartellino_v2.py --aggiorna-cartellino --auth-method spid

# Genera i report in CSV invece di xlsx (default: quello configurato in config.toml/Impostazioni)
uv run python cartellino_v2.py --no-aggiorna-cartellino --export-format csv

# Genera solo alcuni report (default: tutti)
uv run python cartellino_v2.py --no-aggiorna-cartellino --solo-report statistiche,credito

# Genera anche il timesheet di progetto (vedi Timesheet e rendiconto)
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml
```

| Opzione | Valori | Descrizione |
|---------|--------|-------------|
| `--aggiorna-cartellino`/`--no-aggiorna-cartellino` | flag | Scarica i dati aggiornati oppure usa solo quelli già presenti; se omesso, viene chiesto a schermo |
| `--auth-method` | `unisa`, `spid`, `cie` | Metodo di autenticazione per il download; se omesso e il download è attivo, viene chiesto a schermo |
| `--export-format` | `xlsx`, `csv` | Formato dei report generati; se omesso usa quello configurato (default `xlsx`) |
| `--solo-report` | `cartellino`, `riposo`, `credito`, `statistiche`, `ore-giornaliere` (separati da virgola) | Genera solo i report indicati; se omesso li genera tutti |
| `--timesheet-progetto` | nome file YAML | Genera anche il timesheet di progetto — vedi [Timesheet e rendiconto](../data/timesheet.md) |
