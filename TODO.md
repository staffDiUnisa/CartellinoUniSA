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
4. Per ogni issue nuova, e a ogni ricensimento anche per quelle già in tabella, valutare se
   segnalare il flag **URG** (vedi sotto) — senza aspettare che sia l'utente a chiederlo — quando
   ricorre almeno una di: bug che rompe una funzionalità già rilasciata (non solo in sviluppo),
   nessun workaround disponibile per l'utente, o impatto utente Alto combinato con un
   peggioramento visibile rispetto a una release precedente. Segnalare sempre all'utente, nel
   messaggio di risposta, quali issue sono state marcate/rimosse da `URG` e perché.

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

### Flag `URG`

`URG` non è uno stato del flusso sopra ma un **flag di priorità ortogonale**, che segnala che la
soluzione va prioritizzata rispetto al resto del Backlog. Si combina con lo stato corrente della
riga invece di sostituirlo: in tabella compare come prefisso, es. colonna Stato → `URG` (issue
ancora senza stato), `URG WIP`, `URG VER`. Non è applicabile a `IGN`/`DEN`/`CLO` (per definizione
non più prioritarie/attive). Chi lo assegna:

- Di norma è Claude a proporlo durante il censimento (vedi passo 4 sopra) o un ricensimento
  successivo, segnalandolo esplicitamente all'utente — non richiede che l'utente lo chieda prima.
- L'utente può comunque assegnarlo o rimuoverlo in qualunque momento su una riga specifica.

Nessuna azione automatica su GitHub all'assegnazione (nessun commento/label) — è un segnale solo
per la prioritizzazione interna in questo file.

## Sviluppo interno: GUI desktop (non da issue GitHub)

È in fase di pianificazione una nuova interfaccia grafica desktop (PySide6/Qt), da affiancare
alla TUI Textual esistente mantenendone le stesse funzionalità. Sviluppo di portata maggiore
(nuovo frontend, packaging combinato CLI+TUI+GUI) che probabilmente giustifica un bump di
versione major (v3.0.0, da confermare al momento del tag). Piano dettagliato a fasi, con analisi
di complessità/impatto per ciascuna, in [`TODO_gui.md`](TODO_gui.md).

## Backlog

| Issue | Stato | Complessità | Impatto utente | Difficoltà / rischi principali |
|---|:-----:|:---:|:---:|---|
| [#5 Documentazione](https://github.com/staffDiUnisa/CartellinoUniSA/issues/5) |  IGN  | L | Alto | Due deliverable distinti: struttura `docs/` in Markdown (guida utente + note architetturali, in parte già derivabile da `CLAUDE.md`) e setup ReadTheDocs (scelta toolchain — Sphinx/MkDocs —, config di build, hosting). Rischio principale: mantenere la documentazione sincronizzata con un progetto che cambia rapidamente (v2.x in evoluzione attiva) senza duplicare/disallinearsi da `CLAUDE.md`, che resta la fonte di verità per i dettagli implementativi. **Posticipata** a dopo lo sviluppo della GUI desktop (vedi [`TODO_gui.md`](TODO_gui.md)): scriverla ora significherebbe documentare la sola TUI e poi riscriverla per includere anche la GUI. |

## Implementate

- [#7 Compilazione pdf riposi compensativi](https://github.com/staffDiUnisa/CartellinoUniSA/issues/7) —
  compilazione automatica, da GUI, del modulo PDF di richiesta riposo compensativo (piano
  dettagliato in [`TODO_riposo_richiesto.md`](TODO_riposo_richiesto.md)): in Impostazioni si
  carica una tantum il proprio template PDF (AcroForm) già pre-personalizzato con i dati
  anagrafici; da Statistiche → Riposo compensativo, il pulsante "Richiedi riposo compensativo"
  compila e salva il PDF per il prossimo riposo compensativo completo non ancora usato — uso
  rigorosamente sequenziale, un solo riposo alla volta, come richiesto dal segnalante. Nuovo
  stato intermedio "richiesto per `<data>`" (`RiposoCompensativo.data_richiesta`) tra "completo
  non ancora usato" e "usato" (quest'ultimo resta gestito come prima da
  `riposi_usati.txt`/`SRC`). Le richieste pendenti si vedono in una tabella con pulsanti
  "Scarica PDF" e "Annulla (e successive)" — annullare una richiesta annulla anche tutte quelle
  successive già in coda, eliminando i PDF già generati. Verificato dal segnalante. Risolto in
  `v3.1.0`.
- [#6 Problemi GUI MacOS](https://github.com/staffDiUnisa/CartellinoUniSA/issues/6) — la GUI
  installata via `.pkg` restava a rimbalzare nel dock e andava in "non risponde" per minuti
  all'avvio da Finder/Launchpad: il launcher `Cartellino UniSA.app` faceva `exec` del binario
  "sciolto" in `/usr/local/cartellino-unisa/`, perdendo l'identità di bundle macOS — senza un
  `Info.plist` risolvibile, ogni lookup di localizzazione lazy di PySide6/Shiboken (migliaia
  durante l'avvio) degradava a una query non cache-ata via XPC a `cfprefsd`, accumulandosi a
  minuti. La GUI è ora impacchettata con `BUNDLE()` di PyInstaller in un vero bundle `.app`
  firmato/notarizzato correttamente (`packaging/cartellino.spec`, `release.yml`); dettagli
  completi (incluse le due iterazioni di firma/notarizzazione necessarie) in `CLAUDE.md`.
  Verificato dal segnalante. Risolto in `v3.0.2`.
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
