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

| Issue | Complessità | Impatto utente | Difficoltà / rischi principali |
|---|:---:|:---:|---|
| [#3 Verifica esistenza aggiornamenti](https://github.com/staffDiUnisa/CartellinoUniSA/issues/3) | **L** | Medio-Alto — comodità per restare aggiornati, non blocca il workflow principale | Vedi nota dedicata sotto |

### #3 — Verifica esistenza aggiornamenti

Richiesta: controllo di nuove release sia on-demand che all'avvio (disattivabile da
Impostazioni), con possibilità di scaricare la release trovata.

- **Confronto versione**: riusa `_app_version()` (`cartellino/tui/app.py`) già esistente;
  serve solo una chiamata a `GET /repos/.../releases/latest` (GitHub API) e un confronto
  semver.
- **Nuova dipendenza di rete**: nessuna libreria HTTP applicativa presente oggi (solo
  `urllib3` transitiva di Selenium) — da aggiungere `requests`/`httpx`, o usare
  `urllib.request` di stdlib per evitare la nuova dipendenza.
- **Toggle in Impostazioni**: pattern diretto da clonare da `UserConfig.headless` +
  relativo `Switch` in `settings.py` — basso rischio, basso sforzo.
- **Check all'avvio non bloccante**: da lanciare come worker Textual (`@work`) da
  `CartellinoApp.on_mount()`, stesso pattern già usato in `update.py` — deve fallire in modo
  silenzioso se offline/rete assente, per non degradare l'avvio.
- **Rischio principale — "scaricare la release"**: il binario è pacchettizzato **onedir**
  (scelta esplicita, vedi `packaging/cartellino.spec`), quindi non sovrascrivibile file-per-file;
  inoltre il `.pkg` macOS è firmato/notarizzato/staplato e il `.exe` Windows è in esecuzione
  durante il check (non sovrascrivibile). Un vero self-update automatico è complesso e rischioso
  su tutte e 3 le piattaforme. **Consigliato ridurre lo scope reale a**: notifica + apertura
  della pagina Release (o download del solo asset nel browser), lasciando l'installazione
  manuale come oggi — non un updater in-app che sostituisce l'eseguibile mentre gira.
- **Nome**: evitare collisione con `UpdateScreen` esistente (aggiornamento *dati* cartellino,
  non *app*) — nominare la nuova schermata in modo distinto.
- Suggerita eventuale suddivisione in due milestone: (1) check + notifica con link alla
  release (S/M, basso rischio), (2) download automatico assistito (L, rischio alto,
  probabilmente da ridimensionare per i motivi sopra).
