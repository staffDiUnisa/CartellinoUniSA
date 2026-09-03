# `main.py` — versione legacy

Il percorso pre-v2.0.0 (`main.py`/`process.py`) è ancora presente e funzionante, ma non riceve
nuove funzionalità (niente statistiche, niente ore giornaliere — solo la pipeline di calcolo
originaria: ore eccedenti/riposi compensativi). Usa `.env` invece di `config.toml`/keyring — vedi
[Configurazione](../getting-started/configuration.md).

Dati salvati in `data/{anno}/` (nota: **senza** il segmento `v2/` usato dal percorso corrente).

```bash
uv run python main.py
uv run python main.py --no-aggiorna-cartellino
```

Per i nuovi utilizzi è consigliato uno degli entrypoint correnti: [TUI](tui.md), [GUI](gui.md) o
[CLI](cli.md).
