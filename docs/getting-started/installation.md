# Installazione

## Prerequisiti

- [`mise`](https://mise.jdx.dev/) (gestisce la versione di Python e installa `uv`)
- [`uv`](https://docs.astral.sh/uv/) (gestione dipendenze e virtualenv) — installato
  automaticamente da `mise`
- Google Chrome installato (ChromeDriver gestito automaticamente da `webdriver-manager`)
- Connessione alla rete universitaria **solo** per il metodo "Credenziali UNISA" (SPID e CIE
  funzionano anche da fuori rete)
- Account UniSA valido

Non vuoi installare Python/`mise`/`uv`? Vedi [Eseguibili standalone](standalone-executables.md).

## Installazione da sorgente

```bash
git clone https://github.com/staffDiUnisa/CartellinoUniSA.git
cd CartellinoUniSA

mise install       # installa Python 3.12 e uv (versioni pinnate in .mise.toml)
mise run install   # equivalente a: uv sync (installa le dipendenze da pyproject.toml/uv.lock)
```

## Avvio

```bash
mise run tui    # interfaccia testuale (consigliata) — uv run python cartellino_tui.py
mise run gui    # interfaccia grafica desktop        — uv run python cartellino_gui.py
mise run app    # CLI non interattiva                — uv run python cartellino_v2.py
```

Al primo avvio, se non esiste ancora una configurazione, viene mostrata una schermata di
onboarding (TUI/GUI) che guida nella creazione di `config.toml` e nel salvataggio delle
credenziali — vedi [Configurazione](configuration.md).

Per il dettaglio di ogni frontend: [TUI](../usage/tui.md), [GUI](../usage/gui.md),
[CLI](../usage/cli.md).
