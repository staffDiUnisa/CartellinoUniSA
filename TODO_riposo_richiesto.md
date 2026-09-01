# TODO Riposo richiesto — Compilazione PDF richiesta riposo compensativo (issue #7)

> Piano di dettaglio per [issue #7](https://github.com/staffDiUnisa/CartellinoUniSA/issues/7):
> compilare automaticamente, da GUI, il modulo PDF da consegnare in amministrazione per
> richiedere l'uso di un riposo compensativo maturato, a partire da un template AcroForm
> (`giorni`, `dalle`, `alle`, `giorno`, `giorno1..8`, `ore1..8`, `totaleOre`, `data`, `dal`,
> `al`) che l'utente carica una tantum in Impostazioni, già pre-personalizzato con i propri dati
> anagrafici dalla propria area UNISA. Richiede un nuovo stato intermedio per i riposi
> compensativi — "richiesto per `<data>`" — tra "completo non ancora usato" e "usato"
> (quest'ultimo resta gestito dal meccanismo esistente `riposi_usati.txt`/`SRC`, non toccato da
> questo lavoro). Solo GUI (PySide6) in questa fase, come richiesto nell'issue; i moduli di
> dominio restano comunque UI-agnostici per un'eventuale estensione futura alla TUI.

Decisioni di design già confermate con l'utente:
- Uso rigorosamente sequenziale: si può richiedere solo il *prossimo* riposo compensativo
  completo non ancora usato/richiesto — nessun selettore, un solo pulsante "richiedi il
  prossimo disponibile".
- Annullare una richiesta annulla anche tutte quelle successive già in coda (troncamento della
  lista, non rimozione puntuale) **e cancella i PDF già generati** per le richieste troncate.

## Stato di avanzamento

Tutte le fasi (1-6) completate e verificate.

- **Fase 1**: `pypdf` aggiunto a `pyproject.toml` (`uv sync` eseguito, lockfile aggiornato);
  `RiposoCompensativo.data_richiesta` aggiunto; `Config.riposi_richiesti_file` aggiunto
  (stesso trattamento non-auto-creato di `riposi_usati_file`).
- **Fase 2**: `cartellino/riposo_richiesto.py` scritto e verificato con uno script ad-hoc
  (carica/salva, `applica_richieste` FIFO, `prossimo_riposo_disponibile`,
  `annulla_richiesta_da` con troncamento + eliminazione PDF) — tutti i casi passano.
  Formato file `riposi_richiesti.txt`: una riga per richiesta, `data_richiesta|pdf_path`
  (separatore `|`, non usato in nessuno degli altri due campi).
- **Fase 3**: `cartellino/pdf_riposo.py::genera_pdf_richiesta` scritto e verificato con un
  template AcroForm sintetico (script ad-hoc, i campi reali del template utente non erano
  disponibili in questa sessione) — compilazione dei campi (`dal`/`al`/`giorni`/`giorno`/
  `data`/`totaleOre`/`giorno1..N`/`ore1..N`), errore esplicito per template mancante e per
  più di 8 giornate contribuenti, entrambi verificati. Mapping finale dei campi (dopo i
  bugfix sotto): `giorni`="1", **`dal`/`al` sempre vuoti** (nel template reale sono gli
  stessi campi riusati sotto "ATTESTAZIONE DI AVVENUTA CONSEGNA", compilata
  dall'amministrazione — vanno lasciati vuoti anche nella sezione richiesta per non
  precompilare anche quella), `dalle`/`alle` sempre vuoti (non usati per il riposo
  compensativo, giornata intera), `giorno`=**data della richiesta** (non il giorno della
  settimana, fix applicato dopo revisione), `data`=data odierna di compilazione.
- **Fase 4**: il template PDF caricato in Impostazioni viene **copiato** in
  `Config.template_riposo_file` (`{data_folder}/template_riposo_compensativo.pdf`, non
  per-anno: è personale, non cambia da un anno all'altro) invece di essere solo
  referenziato per percorso originale — un file spostato/rinominato dall'utente dopo il
  caricamento non deve rompere la generazione. `UserConfig.template_riposo_compensativo`
  (path grezzo) è stato rimosso: la presenza del template è ora determinata dall'esistenza
  del file copiato. Riga "Template PDF richiesta riposo compensativo (issue #7)" in
  `cartellino/gui/screens/settings.py` mostra lo stato ("Impostato"/"Non impostato") e
  copia il file scelto con "Sfoglia..." al salvataggio (`shutil.copy`, stessa cartella dati
  eventualmente appena cambiata nello stesso salvataggio).
- **Fase 5**: `cartellino/gui/screens/riposo_richiesto.py` scritto
  (`RiposoRichiestoScreen` + `RichiestaRiposoDialog`); wiring completo in
  `cartellino/gui/app.py` (`riposo_richiesto_screen` nello stack, `show_riposo_richiesto()`)
  e in `cartellino/gui/screens/statistiche.py` (pulsante "Richiedi riposo compensativo"
  accanto a "Esporta riposi in txt"). PDF salvati in
  `{output_folder}/richieste_riposo/richiesta_riposo_{id}_{YYYYMMDD}.pdf`. Tabella con
  colonne Data richiesta / PDF (solo nome file, tooltip col path completo) / "Scarica PDF"
  (apre il PDF compilato col visualizzatore di sistema, `QDesktopServices.openUrl`) /
  "Annulla (e successive)". Data richiesta inserita con `QDateEdit` (calendario cliccabile
  o digitazione solo numerica, niente separatori da digitare a mano).
- **Fase 6**: QA end-to-end eseguita headless (`QT_QPA_PLATFORM=offscreen`,
  `QWidget.grab()`) sui dati reali del progetto (`data/v2`): Statistiche → Riposo
  compensativo richiesto → richiesta generata (PDF verificato su disco, `dal`/`al` vuoti,
  `giorno`=data) → "Scarica PDF" (verificato che chiami `QDesktopServices.openUrl` sul
  file) → annullo a cascata con verifica di eliminazione del PDF, tutto verificato via
  script — nessuna regressione nei layout di Impostazioni (nuova riga template) e della
  nuova schermata (colonne della tabella entro il riquadro, nessun pulsante tagliato). Non
  è stato possibile un vero click-through interattivo, solo automazione headless dei
  percorsi di codice.

### Bugfix applicati dopo la prima implementazione (revisione utente)
- Data richiesta: da `QLineEdit` con validator regex a `QDateEdit` con calendario
  (`setCalendarPopup(True)`) — digitazione da tastiera ora accetta solo cifre, i
  separatori non sono digitabili.
- Campo "giorno" nel PDF: conteneva il giorno della settimana, ora contiene la data della
  richiesta (`dd/MM/yyyy`), coerente con "dal"/"al" prima del fix successivo.
- Campi "dal"/"al": lasciati sempre vuoti (vedi Fase 3 sopra) — nel template reale sono
  condivisi con la sezione "ATTESTAZIONE DI AVVENUTA CONSEGNA" compilata
  dall'amministrazione.
- Template PDF: ora copiato in `Config.template_riposo_file` dentro la cartella dati
  invece di essere referenziato dal percorso di origine (vedi Fase 4 sopra).
- Aggiunto pulsante "Scarica PDF" per riga nella tabella delle richieste pendenti (apre il
  PDF già compilato col visualizzatore di sistema).
- Campo "giorni": nonostante il nome, nel template reale è il numero di ORE (non
  giorni) di "di poter usufrire di n. ___ ore di riposo compensativo" — conteneva
  erroneamente "1" (assunto come conteggio giorni), ora contiene lo stesso valore di
  "totaleOre" (es. "07:12").
- Bug di rendering: le colonne con soli pulsanti (nessun testo) non venivano
  dimensionate correttamente da `resizeColumnsToContents()` una tantum, causando pulsanti
  troppo stretti/tagliati — sostituito con
  `horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)` +
  `setStretchLastSection(True)`; colonna PDF ridotta al solo nome file (tooltip col path
  completo) per non forzare uno scroll orizzontale che tagliava i pulsanti fuori dal
  riquadro della tabella.

### Da fare a valle (fuori scope di questa sessione, note per il prossimo giro)
- QA manuale reale in `mise run gui` con un template PDF vero, come da piano originale —
  in particolare confermare che il template reale abbia davvero campi `dal`/`al`
  condivisi tra sezione richiesta e "ATTESTAZIONE DI AVVENUTA CONSEGNA" (assunzione alla
  base del bugfix sopra, mai verificata su un file reale in questa sessione).

## Fasi

### Fase 1 — Dipendenza e modello dati di base
- `pyproject.toml`: aggiungere `pypdf`.
- `model/riposo_compensativo.py`: nuovo campo opzionale `data_richiesta: str | None = None`
  su `RiposoCompensativo`, parallelo a `data` (che resta il significato "usato/confermato").
  Nessuna modifica a `OreEccedenti._raggruppa_ore_eccedenti`.
- `cartellino/config.py`: nuovo `Config.riposi_richiesti_file` = `input_folder / "riposi_richiesti.txt"`,
  stesso trattamento (non auto-creato) di `riposi_usati_file`.

### Fase 2 — Stato persistito e matching FIFO delle richieste
Nuovo modulo `cartellino/riposo_richiesto.py`:
- `RichiestaRiposo` (dataclass: `data_richiesta`, `pdf_path`).
- `carica_richieste(path) -> list[RichiestaRiposo]` / `salva_richieste(path, richieste)`.
- `applica_richieste(riposi, richieste)` — secondo passaggio dopo `raggruppa()`: assegna
  `.data_richiesta` in ordine FIFO ai riposi completi con `data is None`.
- `prossimo_riposo_disponibile(riposi) -> RiposoCompensativo | None`.
- `annulla_richiesta_da(path, indice)` — tronca la lista da `indice` in poi ed elimina i PDF
  corrispondenti.

### Fase 3 — Generazione PDF
Nuovo modulo `cartellino/pdf_riposo.py`, `genera_pdf_richiesta(template_path, riposo,
data_richiesta, current_year, output_folder) -> Path`, via `pypdf` (`PdfReader`/`PdfWriter`,
`update_page_form_field_values`). Errori espliciti (`RiposoPdfError`) per: più di 8 giornate
contribuenti nel riposo (limite del template), template senza i campi attesi.

### Fase 4 — Impostazioni: upload template one-shot
- `cartellino/user_config.py`: nuovo campo `template_riposo_compensativo: str | None = None`.
- `cartellino/gui/screens/settings.py`: nuova riga con `QFileDialog.getOpenFileName` per
  selezionare il PDF, salvata in `UserConfig`.

### Fase 5 — Schermata GUI richiesta/annullo
- Nuovo `cartellino/gui/screens/riposo_richiesto.py`: `RiposoRichiestoScreen` (tabella
  richieste pendenti + pulsante "Richiedi il prossimo disponibile" + annullo a cascata) e
  `RichiestaRiposoDialog` (mirror di `CredentialsDialog`, singolo campo data richiesta).
- Wiring in `cartellino/gui/app.py` (nuova voce nello stack + `show_riposo_richiesto()`) e in
  `cartellino/gui/screens/statistiche.py` (pulsante di ingresso accanto a "Esporta riposi in
  txt", visibile nella vista "Riposo compensativo").

### Fase 6 — QA end-to-end
Percorso completo in `mise run gui`: Impostazioni → carica template di test → Statistiche →
Riposo compensativo → Richiedi riposo compensativo → richiesta → verifica PDF generato →
annullo a cascata con verifica cancellazione PDF. Screenshot (`QWidget.grab()`) delle nuove
schermate per QA di layout/scroll, stesso metodo già in uso nel progetto.
