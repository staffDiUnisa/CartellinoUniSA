# TODO GUI — Piano di sviluppo interfaccia grafica desktop

> Piano di dettaglio per una nuova interfaccia grafica (GUI) desktop, pensata per affiancare —
> non sostituire — la TUI Textual esistente (`cartellino_tui.py` / `cartellino/tui/`), offrendo
> le stesse funzionalità senza richiedere un terminale. Sviluppo di portata maggiore che
> probabilmente giustifica un bump di versione major (v3.0.0, da confermare al momento del tag
> effettivo). Documento di pianificazione: nessuna implementazione è iniziata.

## Decisioni prese

1. **Framework: [PySide6](https://doc.qt.io/qtforpython-6/)** (bindings Qt6, licenza LGPL).
   Motivazioni:
   - Licenza LGPL, compatibile con un progetto OSS che vuole restare permissivo (a differenza di
     PyQt6, stessa qualità tecnica ma licenza GPL/commerciale).
   - Ottimo supporto nativo multipiattaforma (macOS/Windows/Linux) con look-and-feel del
     sistema operativo.
   - Modello di threading `QThread`/`Signal`/`Slot` concettualmente equivalente al pattern già
     in uso nella TUI (`@work(thread=True)` + `App.call_from_thread`), quindi porting diretto
     della logica di background già scritta per il download Selenium e i controlli
     aggiornamento.
   - Supporto PyInstaller maturo (hook della community `pyinstaller-hooks-contrib`), stesso
     schema onedir già usato dal progetto — nessun cambio di strategia di packaging.
   - Widget nativi che in alcuni casi **semplificano** rispetto all'equivalente Textual: es.
     `QFileDialog.getExistingDirectory` nativo del sistema operativo al posto del
     `FolderPickerScreen` custom con `DirectoryTree`.
   - Alternative scartate: Kivy (peggiore integrazione nativa desktop), Flet/Flutter (runtime
     più pesante, meno maturo rispetto alla pipeline di firma/notarizzazione macOS già
     consolidata e documentata in `CLAUDE.md`).
2. **Packaging: distribuzione combinata.** Un solo pacchetto/installer per OS include sia la GUI
   sia la TUI/CLI esistenti (non due prodotti separati con identità distinte). La pipeline CI
   esistente va **estesa**, non duplicata.
3. **Issue #5 (Documentazione): posticipata** a dopo il completamento della GUI — vedi nota in
   `TODO.md`. Motivazione: evitare di scrivere la documentazione due volte (una per la sola TUI,
   una dopo l'introduzione della GUI).

## Struttura del nuovo pacchetto

```
cartellino_gui.py            # entrypoint, mirror di cartellino_tui.py
cartellino/gui/
    app.py                    # QApplication + finestra principale/router (mirror di CartellinoApp)
    workers.py                # QObject/QThread + Signal per lavoro in background
                               #   (mirror di RichLogHandler + @work(thread=True))
    widgets/                  # eventuali widget custom condivisi tra schermate (se necessario)
    style.qss                 # foglio di stile Qt (equivalente concettuale di app.tcss)
    screens/ (o windows/)     # una classe per schermata, mirror di cartellino/tui/screens/
```

Pattern di navigazione: `QStackedWidget` nella finestra principale per le schermate primarie
(Onboarding/Dashboard/Update/Reports/...), `QDialog` modali per i popup con valore di ritorno
(Credentials; FolderPicker sostituito dal `QFileDialog` nativo).

## Codice esistente riusabile senza modifiche

L'intero layer di dominio, già condiviso oggi tra CLI (`cartellino_v2.py`) e TUI, è agnostico
rispetto al frontend e **non richiede alcuna modifica** per essere chiamato dalla GUI:

- `cartellino/config.py` (`Config`), `cartellino/user_config.py` (`UserConfig`)
- `cartellino/credentials.py` (wrapper `keyring`)
- `cartellino/cartellino.py` (`Cartellino`)
- `cartellino/processor.py` (`CartellinoProcessor`, `REPORT_KEYS`)
- `cartellino/ore_eccedenti.py` (`OreEccedenti`)
- `cartellino/credito_ore.py` (`CreditoOre`)
- `cartellino/ore_giornaliere.py` (`OreGiornaliere`)
- `cartellino/statistiche.py` (`Statistiche`)
- `cartellino/ore_helpers.py`, `cartellino/excel_utils.py`, `cartellino/export_utils.py`
- `cartellino/timesheet_progetto.py`, `cartellino/timesheet_runner.py`, `cartellino/rendiconto_excel.py`
- `cartellino/update_checker.py`
- `get.py` (`ottieni_cartellino`, `is_on_unisa_network`, `METODI_AUTENTICAZIONE`) — resta
  sincrono/bloccante, va richiamato da un thread proprio (vedi Fase 4)

Nota di accoppiamento (non un blocco, solo da tenere presente): `ore_eccedenti.py` e
`timesheet_progetto.py` dipendono ancora dai package legacy root-level `model/` e `processor/`
(distinti da `cartellino/processor.py`) — nessun refactor necessario per la GUI.

**Non riusabile / da non portare**: `cartellino/tui/macos_terminal.py` è specifico del lancio
da AppleScript/Terminale ed è **droppabile per la GUI** (finestra nativa, nessun terminale da
scegliere all'avvio).

## Fasi di implementazione

| Fase | Contenuto | Complessità | Impatto utente | Impatto su codice esistente | Rischi principali |
|:---:|---|:---:|:---:|---|---|
| 0 | Spike tecnico: aggiungere PySide6 come dipendenza, "Hello World" con `QApplication`, verificare build PyInstaller onedir con `cartellino_gui.py` come secondo entrypoint nello stesso spec/staging, verificare se serve lo stesso workaround `DYLD_*`/re-exec di `cartellino_tui.py` per il conflitto pyarrow/Abseil. | S | Nullo (nessuna feature) | Nessuno (solo dipendenza + file nuovi) | Scoprire tardi un conflitto di librerie native (stesso tipo di bug già documentato in `CLAUDE.md` per pyarrow) — la spike serve a isolarlo prima di scrivere schermate. |
| 1 | Scaffolding app: `cartellino/gui/app.py` con `QStackedWidget`, routing iniziale (Onboarding/Update/Dashboard) mirror di `CartellinoApp.reload_config_and_route()`, foglio QSS base. | M | Nullo (shell vuota) | Nessuno | Decidere il pattern di navigazione/ritorno-valore da dialog in modo coerente per tutte le fasi successive — un errore di design qui si propaga a tutte le schermate. |
| 2 | Onboarding screen (year, min-date, credenziali, headless). | S | Alto (primo avvio) | Nessuno (`UserConfig.save`, `set_credentials` già riusabili) | Validazione campi con widget Qt nativi (`QLineEdit` + `QRegularExpressionValidator` o `QDateEdit`) al posto di `MaskedInput`. |
| 3 | Dashboard screen (sola lettura + navigazione). | M | Alto (schermata più vista) | Nessuno | Replicare `on_screen_resume` (refresh dati al ritorno da altra schermata) con i segnali Qt. |
| 4 | Update screen (download Selenium) — **la più complessa**. | L | Alto | Nessuno lato dominio; nuovo `workers.py` con `QThread`+`Signal` per streaming log, sostituisce `RichLogHandler` | Selenium apre una finestra Chrome reale (SPID/CIE) mentre la GUI resta aperta: verificare assenza di conflitti di focus tra le due finestre; il blocco fino a 10 minuti (`WebDriverWait`) deve girare in thread separato con log in tempo reale via signal — rischio di freeze UI se il worker non è isolato correttamente. |
| 5 | Reports screen (4 pulsanti sincroni). | S | Medio | Nessuno | Le chiamate sono sincrone anche nella TUI; valutare se spostarle comunque in worker thread per non freezare la UI su cartellini grandi (miglioria opzionale, non requisito). |
| 6 | Timesheet screen (select file YAML + genera). | S | Basso/Medio | Nessuno | Elenco file YAML da cartella `timesheet/` via `QFileDialog`/`QComboBox`, nessuna logica nuova. |
| 7 | Statistiche screen (tabella + markdown riposi). | M | Medio | Nessuno | `QTableView`+`QAbstractTableModel` per le 7 categorie (più lavoro di un `DataTable` Textual "drop-in"); `QTextBrowser` supporta Markdown nativamente per `riposi_markdown()`. |
| 8 | Settings screen — **la più estesa**. | L | Alto | Nessuno lato dominio; folder picker nativo (`QFileDialog.getExistingDirectory`) **semplifica** rispetto al `FolderPickerScreen` custom, che resta solo-TUI | Molti campi eterogenei (year, min-date, export format, dashboard codes, switch, data ticket, cartella dati/output, date escluse, credenziali) — rischio di regressioni per singolo campo se non testati uno a uno; il campo "Terminale (solo macOS)" va **omesso** in GUI (non applicabile, lancio come app nativa). |
| 9 | Date escluse screen (modale add/remove righe). | S | Basso | Nessuno | `QTableWidget` con add/remove riga, stesso formato file (`DD-MM-YYYY[ HH:MM]`). |
| 10 | Credentials screen (modale). | S | Medio | Nessuno | Dialog semplice, `QLineEdit` con `EchoMode.Password`. |
| 11 | App update screen (note di rilascio + apri browser). | S | Basso | Nessuno | `QTextBrowser` per markdown + `QDesktopServices.openUrl`, nessuna logica nuova. |
| 12 | Packaging: estendere `packaging/cartellino.spec` per includere `cartellino_gui.py` nello stesso staging onedir della distribuzione combinata; individuare eventuali `hiddenimports` mancanti per PySide6. | M | Nullo (infrastruttura) | `packaging/cartellino.spec` | Rischio di rompere la build TUI/CLI esistente se lo spec combinato non isola bene i due entrypoint — validare con build locale prima di toccare CI. |
| 13 | CI/release: aggiornare `.github/workflows/release.yml` per generare/firmare/notarizzare anche il nuovo eseguibile GUI nello stesso `.pkg`/`.exe`/`.deb`/`.rpm`; aggiungere/adattare un launcher macOS per il lancio diretto della GUI (nessun picker "quale terminale" necessario per la GUI). | L | Nullo (infrastruttura) | `.github/workflows/release.yml`, `packaging/windows/installer.iss`, `packaging/macos/*`, `packaging/linux/postinstall.sh` | Massima superficie di rischio infrastrutturale del piano: firma/notarizzazione macOS già delicata (vedi `CLAUDE.md`), un secondo eseguibile nello stesso pacchetto raddoppia i punti di fallimento — procedere con una release `-rc` di prova dedicata, come già fatto per v2.0.1/v2.0.2. |
| 14 | QA manuale end-to-end su tutte le schermate (nessun framework di test automatico oggi nel repo). | M | Alto (qualità percepita) | Nessuno, salvo eventuale introduzione di `pytest-qt` come opportunità futura (fuori scope) | Senza test automatici, ogni fase rischia regressioni silenziose sulle fasi precedenti — la QA va ripetuta ad ogni fase, non solo alla fine. |
| 15 | Aggiornare `CLAUDE.md` con la nuova architettura `cartellino/gui/`, allo stesso livello di dettaglio già presente per `cartellino/tui/`. | S | Nullo | `CLAUDE.md` | Da fare a fine sviluppo, per non documentare un'API ancora instabile. |

**Totale stimato**: indicativamente **~25-35 giorni-persona part-time** (somma delle
complessità S/M/L sopra), a supporto dell'ipotesi di bump di versione major. Da confermare al
momento del tag effettivo, seguendo la convenzione del progetto di bump `pyproject.toml`
**prima** di ogni tag, anche per rc di prova.

## Note aperte da decidere prima di iniziare l'implementazione

- Se tracciare questa roadmap come sezione dedicata di `TODO.md` (analoga alla precedente
  "roadmap v2.0.0") oppure mantenerla solo in questo file separato.
- Se introdurre `pytest`/`pytest-qt` contestualmente alla GUI (Fase 14) o rimandare anche questo.
- Nome definitivo dell'app/prodotto combinato per l'installer (identità unica CLI+TUI+GUI).
