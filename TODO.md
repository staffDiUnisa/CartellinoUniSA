# TODO — Backlog feature/bug da issue GitHub

> Backlog delle feature e dei bug proposti tramite le issue del repo
> [`staffDiUnisa/CartellinoUniSA`](https://github.com/staffDiUnisa/CartellinoUniSA/issues).
> Sostituisce la precedente roadmap v2.0.0 (completata e rilasciata — consultabile nella storia
> git di questo file, `git log -p TODO.md`).

## Procedimento di aggiornamento

Da ripetere ogni volta che viene chiesto di aggiornare questo file con le nuove issue:

1. `gh issue list --state open` sul repo per l'elenco aggiornato.
2. Per ogni issue aperta non ancora presente in tabella: aggiungere una riga con
   titolo/link, e una sotto-sezione dedicata con la stima.
3. Per ogni issue presente in tabella ma nel frattempo chiusa: rimuoverla dalla tabella (resta
   comunque nello storico GitHub) e, se utile, annotarla come risolta con riferimento alla
   versione/release che l'ha chiusa.
4. Stima con la stessa scala usata di seguito: **Complessità** (S = 1-2 giorni, M = 3-5 giorni,
   L = 6-10 giorni, XL = 10+ giorni, sviluppo part-time una persona sola), **Impatto utente**
   (Basso/Medio/Alto), **Difficoltà/rischi principali** (in prosa, punti concreti).

## Backlog

Nessuna issue aperta al momento. Storico delle voci implementate sotto.

## Implementate

- [#3 Verifica esistenza aggiornamenti](https://github.com/staffDiUnisa/CartellinoUniSA/issues/3) —
  controllo release GitHub on-demand (pulsante "Controlla aggiornamenti" in Dashboard) e
  all'avvio (disattivabile da Impostazioni, `UserConfig.check_updates_on_startup`), con apertura
  della pagina Release nel browser per il download (nessun self-update automatico, per i rischi
  di packaging — binario onedir, `.pkg` macOS firmato/notarizzato, `.exe` Windows in esecuzione).
  Vedi `cartellino/update_checker.py` e `cartellino/tui/screens/app_update.py`; dettagli in
  `CLAUDE.md`.
