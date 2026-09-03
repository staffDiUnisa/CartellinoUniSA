# Contribuire

1. Fork del repository
2. Crea un branch: `git checkout -b feature/nuova-funzionalita`
3. Commit: `git commit -m 'Aggiunta nuova funzionalità'`
4. Push: `git push origin feature/nuova-funzionalita`
5. Apri una Pull Request

Per capire dove intervenire nel codice, vedi [Architettura](architecture.md) e, per i dettagli
implementativi completi,
[`CLAUDE.md`](https://github.com/staffDiUnisa/CartellinoUniSA/blob/master/CLAUDE.md) nel
repository.

## Ambiente di sviluppo

```bash
git clone https://github.com/staffDiUnisa/CartellinoUniSA.git
cd CartellinoUniSA
mise install
mise run install
```

Per rigenerare l'eseguibile standalone localmente:

```bash
uv sync --group build
uv run pyinstaller packaging/cartellino.spec
```

Per lavorare su questa documentazione:

```bash
uv sync --group docs
uv run mkdocs serve
```
