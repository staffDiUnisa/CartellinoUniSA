# TODO — Backlog feature/bug da issue GitHub

> Backlog delle feature e dei bug proposti tramite le issue del repo
> [`staffDiUnisa/CartellinoUniSA`](https://github.com/staffDiUnisa/CartellinoUniSA/issues).
> Sostituisce la precedente roadmap v2.0.0 (completata e rilasciata — consultabile nella storia
> git di questo file, `git log -p TODO.md`).

## Procedimento di censimento

Da ripetere ogni volta che viene chiesto di aggiornare questo file con le nuove issue:

1. `gh issue list --state open` sul repo per l'elenco aggiornato.
2. Per ogni issue aperta non ancora presente in tabella: aggiungere una riga con titolo/link e
   **Stato** vuoto (nessuna decisione presa ancora), e una sotto-sezione dedicata con la stima
   di **Complessità** (S = 1-2 giorni, M = 3-5 giorni, L = 6-10 giorni, XL = 10+ giorni,
   sviluppo part-time una persona sola), **Impatto utente** (Basso/Medio/Alto) e
   **Difficoltà/rischi principali** (in prosa, punti concreti).
3. Le issue già presenti in tabella non vengono ristimate: si aggiorna solo l'elenco con le
   nuove.

## Stati delle issue e flusso di lavoro

Quando viene chiesta la lista delle cose da fare, l'utente sceglie per ciascuna issue nel
Backlog uno stato tra quelli sotto. Ogni cambio di stato aggiorna sia questo file sia la issue
su GitHub (`gh issue comment`/`gh issue close`), come indicato:

| Stato | Significato | Azione su GitHub | Azione su TODO.md |
|:---:|---|---|---|
| *(vuoto)* | Appena censita, nessuna decisione presa | Nessuna | Resta in Backlog, colonna Stato vuota |
| **WIP** | Si passa alla fase di risoluzione | Commento: issue in lavorazione, sarà risolta con una prossima release | Colonna Stato → `WIP`, resta in Backlog |
| **IGN** | Ignorata per ora | Nessuna azione — issue resta aperta così com'è | Colonna Stato → `IGN`, resta in Backlog |
| **DEN** | Scartata, non verrà implementata | Commento con la motivazione fornita dall'utente, **poi chiusura automatica** della issue | Riga rimossa dal Backlog e aggiunta a **Rifiutate** con la motivazione |
| **VER** | Implementazione completata, in fase di verifica | Commento: implementazione completata, in verifica | Colonna Stato → `VER`, resta in Backlog |
| **CLO** | Verificata e chiusa | Commento con riferimento alla release che la risolve (o alla motivazione se non risolvibile), **poi chiusura** della issue | Riga rimossa dal Backlog e aggiunta a **Implementate** |

Flusso tipico: *(vuoto)* → `WIP` → `VER` → `CLO`. `IGN` può essere scelto in qualunque momento
per rimandare la decisione, senza uscire dal Backlog. `DEN` è uno stato terminale alternativo
(da *(vuoto)* o da `IGN`) — a differenza di `CLO`, non richiede una release: la motivazione del
rifiuto sostituisce il riferimento alla soluzione.

## Backlog

| Issue | Stato | Complessità | Impatto utente | Difficoltà / rischi principali |
|---|:---:|:---:|:---:|---|
| [#5 Documentazione](https://github.com/staffDiUnisa/CartellinoUniSA/issues/5) | IGN | L | Alto | Due deliverable distinti: struttura `docs/` in Markdown (guida utente + note architetturali, in parte già derivabile da `CLAUDE.md`) e setup ReadTheDocs (scelta toolchain — Sphinx/MkDocs —, config di build, hosting). Rischio principale: mantenere la documentazione sincronizzata con un progetto che cambia rapidamente (v2.x in evoluzione attiva) senza duplicare/disallinearsi da `CLAUDE.md`, che resta la fonte di verità per i dettagli implementativi. |

## Implementate

- [#4 Miglioramento interfaccia](https://github.com/staffDiUnisa/CartellinoUniSA/issues/4) —
  pulsanti uniformati su tutte le schermate della TUI tramite le classi condivise
  `.button-row`/`.button-grid` (prima applicate solo su alcune) e una nuova classe `.field-row`
  per le righe che affiancano un campo Input/MaskedInput a un pulsante (senza ereditare il
  `width: auto` di `.button-row`, che comprimerebbe il campo e — combinato col `width: 100%` di
  default di `Input` — spingerebbe il pulsante fuori dal viewport). Vedi `cartellino/tui/app.tcss`.
  Risolto in `v2.0.5`.
- [#3 Verifica esistenza aggiornamenti](https://github.com/staffDiUnisa/CartellinoUniSA/issues/3) —
  controllo release GitHub on-demand (pulsante "Controlla aggiornamenti" in Dashboard) e
  all'avvio (disattivabile da Impostazioni, `UserConfig.check_updates_on_startup`), con apertura
  della pagina Release nel browser per il download (nessun self-update automatico, per i rischi
  di packaging — binario onedir, `.pkg` macOS firmato/notarizzato, `.exe` Windows in esecuzione).
  Vedi `cartellino/update_checker.py` e `cartellino/tui/screens/app_update.py`; dettagli in
  `CLAUDE.md`. Risolto in `v2.0.4`.

## Rifiutate

_nessuna issue rifiutata al momento._
