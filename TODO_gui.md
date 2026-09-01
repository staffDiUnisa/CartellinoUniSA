# TODO GUI — Piano di sviluppo interfaccia grafica desktop

> Piano di dettaglio per una nuova interfaccia grafica (GUI) desktop, pensata per affiancare —
> non sostituire — la TUI Textual esistente (`cartellino_tui.py` / `cartellino/tui/`), offrendo
> le stesse funzionalità senza richiedere un terminale. Sviluppo di portata maggiore che
> probabilmente giustifica un bump di versione major (v3.0.0, da confermare al momento del tag
> effettivo). Documento di pianificazione: nessuna implementazione è iniziata.

## Stato di avanzamento

- **Fase 0 (spike tecnico) — completata.** `pyside6` aggiunto alle dipendenze
  (`pyproject.toml`), `cartellino_gui.py` come "Hello World" (`cartellino/gui/app.py`),
  task `mise run gui`. `packaging/cartellino.spec` esteso con un secondo `Analysis`/`EXE`
  (`MERGE` per deduplicare i moduli condivisi) così l'onedir combinato produce sia
  `cartellino-unisa` (TUI/CLI, console) sia `cartellino-unisa-gui` (windowed) nella stessa
  cartella. Build locale reale verificata (macOS arm64): nessun conflitto pyarrow/Abseil
  riscontrato con PySide6 nello stesso bundle, entrambi gli eseguibili partono senza errori
  (verificato con `QT_QPA_PLATFORM=offscreen`, terminazione solo per timeout del test — atteso
  per un event loop GUI/TUI che resta in attesa di input).
- **Fase 1 (scaffolding app) — completata.** `cartellino/gui/app.py::MainWindow` con
  `QStackedWidget` (Onboarding/Update/Dashboard) e `reload_config_and_route()`, mirror di
  `CartellinoApp.reload_config_and_route` — stessa identica logica di instradamento riusata
  senza modifiche (`Config.load`, poi Onboarding se `config is None`, Update se manca il
  feather, altrimenti Dashboard). `cartellino/gui/style.qss` come foglio di stile base (vuoto
  per ora). Le tre schermate (`cartellino/gui/screens/{onboarding,update,dashboard}.py`) sono
  ancora placeholder: contenuto reale nelle fasi 2-4. `cartellino_gui.py` esteso con lo stesso
  pattern di `cartellino_tui.py` per `APP_DATA_DIR`/log su file (`~/.cartellino_unisa`,
  condivisa con la TUI — stesso `config.toml`/dati, due frontend sullo stesso layer di
  dominio). Routing verificato per tutti e tre i casi con build locale reale, sia in `uv run`
  sia nel binario impacchettato.
- **Fase 2 (Onboarding screen) — completata.** `cartellino/gui/screens/onboarding.py`: stessi
  campi della TUI (anno, min-date, username/password opzionali, switch headless), stessa logica
  di salvataggio (`UserConfig.save`, `set_credentials`) riusata senza modifiche. Segnale Qt
  `saved` al posto di `self.app.reload_config_and_route()` diretto: la `MainWindow` lo ascolta e
  richiama il routing, mantenendo la schermata disaccoppiata dal router (mirror concettuale,
  non identico, dello screen-stack Textual). Validazione campo anno con
  `QRegularExpressionValidator` al posto di `Input(restrict=...)`.
- **Fase 3 (Dashboard screen) — completata.** `cartellino/gui/screens/dashboard.py`: le sei
  sezioni informative (eccezioni/saldo mese, saldo mensile, riposi compensativi, ferie/PMF,
  ticket da ricevere, ultimo aggiornamento) sono lo stesso codice di calcolo della TUI, solo
  riformattato da markup Rich a HTML per `QLabel` (`Qt.TextFormat.RichText`) invece che a testo
  ricostruito via `Static`. `refresh()` (chiamato da `MainWindow.reload_config_and_route`) è il
  mirror di `on_screen_resume`, ma più semplice: qui basta riassegnare il testo della label, non
  serve smontare/rimontare widget (la Dashboard TUI lo fa per via del vincolo `compose()`
  descritto in `CLAUDE.md`, che qui non si applica). Pulsante "Aggiorna cartellino" già
  funzionante (porta all'Update screen, ancora placeholder — Fase 4); i pulsanti verso
  Report/Timesheet/Statistiche/Impostazioni sono presenti ma disabilitati con tooltip, dato che
  quelle schermate non esistono ancora lato GUI (Fasi 5-9) — niente promesse di navigazione a
  vuoto. "Controlla aggiornamenti" è già funzionante end-to-end con un `QThread` dedicato
  (`_UpdateCheckWorker`, mirror di `_check_update_worker`/`@work(thread=True)`) e un
  `QMessageBox` per l'esito: la Fase 11 (App update screen) lo sostituirà con una schermata
  dedicata (note di rilascio + apertura browser), ma il flusso end-to-end è già verificato.
  Tutto verificato sia in `uv run` sia nel binario impacchettato (nessun errore, build locale
  reale).
- **Fase 4 (Update screen) — completata.** `cartellino/gui/workers.py`
  (`QtLogHandler`+`DownloadWorker`, mirror di `RichLogHandler`+
  `@work(thread=True)`): il download Selenium (`get.ottieni_cartellino`) gira in un
  `QThread` dedicato, il log viene inoltrato in tempo reale a un `QPlainTextEdit` via
  `Signal` — Qt trasforma automaticamente l'emissione cross-thread in una
  `QueuedConnection`, niente equivalente esplicito di `call_from_thread` da scrivere a
  mano. `cartellino/gui/screens/update.py`: stessi tre metodi di autenticazione
  (`QRadioButton`, "Credenziali UNISA" disabilitato se non sulla rete UniSA, stessa
  `is_on_unisa_network()`), pulsante "Indietro" in più rispetto alla TUI (che usa
  `Escape`, qui serve un widget esplicito) che torna alla Dashboard senza scaricare.
  `MainWindow.on_download_succeeded`/`on_update_back` sostituiscono
  `self.app.pop_screen()`, con lo stesso comportamento (torna alla Dashboard, che si
  riaggiorna). `packaging/cartellino.spec`: hiddenimports selenium duplicati anche
  nell'`Analysis` della GUI (necessari perché `workers.py` importa `get.py`, stesso
  problema di lazy import PEP 562 già noto per la TUI). Verificato con build locale
  reale (nessun `ModuleNotFoundError`, entrambi gli eseguibili partono senza errori) —
  **non verificato manualmente un download reale end-to-end** (richiede rete UniSA e
  interazione con una finestra Chrome vera): da fare in QA (Fase 14).
- **Fase 5 (Reports screen) — completata.** `cartellino/gui/screens/reports.py`: stessi quattro
  report on-demand della TUI (riposo compensativo, credito ore, statistiche, ore giornaliere),
  stesse chiamate sincrone al layer di dominio (nessun worker thread, scelta coerente col piano
  — "miglioria opzionale, non requisito"). Aggiunto un pulsante "Indietro" esplicito (la TUI usa
  `Escape`, qui serve un widget). `MainWindow.show_dashboard()` sostituisce sia
  `on_update_back` sia `on_download_succeeded` di prima (stesso comportamento, un solo metodo
  condiviso invece di due alias — refactor di Fase 4 fatto qui perché `ReportsScreen` aveva
  bisogno dello stesso "torna alla Dashboard"). Il pulsante "Genera report" della Dashboard
  (Fase 3, prima disabilitato con tooltip) ora è collegato e funzionante. Verificato sia in
  `uv run` (navigazione avanti/indietro, formato export letto da `Config`) sia nel binario
  impacchettato.
- **Fase 6 (Timesheet screen) — completata.** `cartellino/gui/screens/timesheet.py`: stessa
  logica della TUI (`esegui_timesheet_progetto`, elenco YAML in `timesheet/`), `QComboBox` al
  posto di `Select`. Aggiunto un pulsante "Sfoglia..." (`QFileDialog.getOpenFileName`) non
  presente nella TUI, per selezionare uno YAML fuori dalla cartella di default — piccola
  estensione naturale visto il widget nativo disponibile, nessun cambio alla logica di dominio.
  Pulsante "Genera timesheet" della Dashboard ora collegato e funzionante. Verificato in `uv run`
  e nel binario impacchettato.
- **Fase 7 (Statistiche screen) — completata.** `cartellino/gui/screens/statistiche.py`: stesse 7
  categorie (`Statistiche.calcola()`), un pulsante per categoria disabilitato se il DataFrame è
  vuoto, esattamente come la TUI. `_DataFrameTableModel(QAbstractTableModel)` — piccolo modello
  scritto ad hoc per esporre un `pd.DataFrame` a `QTableView` (non esiste un drop-in Qt per
  questo, a differenza della `DataTable` di Textual che accetta righe direttamente), più lavoro
  della TUI come già previsto dal piano. Ottavo pulsante "Riposo compensativo" mostra un
  `QTextBrowser` con `setMarkdown()` (supporto Markdown nativo Qt, nessuna libreria aggiuntiva)
  al posto della tabella — stessa fonte dati (`OreEccedenti.riposi_markdown()`, riusata
  identica) e stesso pulsante di export in `riposi_compensativi.txt` accanto. Verificato con
  dati reali sia in `uv run` (popolamento tabella e markdown da un click reale) sia nel binario
  impacchettato.
- **Fase 8 (Settings screen) — completata.** `cartellino/gui/screens/settings.py`: tutti i campi
  della TUI tranne il "Terminale (solo macOS)", omesso di proposito (non applicabile — lancio
  come app nativa, nessuna scelta di terminale). `QFileDialog.getExistingDirectory` nativo per
  cartella dati/output, senza scrivere nessun equivalente del `FolderPickerScreen` custom
  (semplificazione già prevista dal piano). "Gestisci date escluse" e "Modifica credenziali"
  restano disabilitati con tooltip (Fasi 9/10, non ancora scritte); "Rimuovi credenziali" è già
  funzionante (nessuna schermata dedicata necessaria, stessa `delete_credentials()`). Stessa
  validazione della TUI per anno/data ticket/cartella dati, stesso salvataggio
  (`UserConfig.save()`) e stesso `reload_config_and_route()` finale. Verificato con dati reali
  (letture, non salvataggi, per non toccare la config reale della macchina di sviluppo): tutti
  e tre i percorsi di errore di validazione producono il messaggio atteso senza chiamare
  `UserConfig.save()`. Verificato anche il binario impacchettato (nessun errore).
- **Fase 9 (Date escluse screen) — completata.** `cartellino/gui/screens/date_escluse.py`: stesso
  formato file (`DD-MM-YYYY[ HH:MM]`), stesso parsing/scrittura (`_VoceEsclusa`/`_parse_riga`
  identici alla TUI). `QTableWidget` con un pulsante "Rimuovi" per riga (`setCellWidget`) al
  posto della lista di `Horizontal` Textual, per add/remove — come indicato dal piano. Il
  pulsante "Gestisci date escluse" di Impostazioni (Fase 8, prima disabilitato) è ora collegato
  e funzionante. Verificato aggiunta/rimozione su un file temporaneo isolato (non il
  `date_escluse.txt` reale della macchina di sviluppo, per non alterare dati utente): scrittura
  corretta per entrambi i formati (giornata intera e con orario), rimozione per indice corretta.
  Verificato anche il binario impacchettato.
- **Fase 10 (Credentials screen) — completata.** `cartellino/gui/screens/credentials.py`:
  `QDialog` modale con `QDialogButtonBox` (Salva/Annulla) al posto dello `Screen[bool]` con
  `dismiss(True/False)` — stesso pattern valore di ritorno (`exec()` bloccante +
  `result() == Accepted`), stessa validazione (username e password obbligatori) e stessa
  `set_credentials()`. Il pulsante "Modifica credenziali" di Impostazioni (Fase 8, prima
  disabilitato) è ora collegato e funzionante. Verificata solo la costruzione/validazione del
  dialog (senza chiamare `exec()`, bloccante, e senza scrivere credenziali reali nel keyring di
  sviluppo). Verificato anche il binario impacchettato.
- **Fase 11 (App update screen) — completata.** `cartellino/gui/screens/app_update.py`
  (`AppUpdateDialog`): `QTextBrowser` con `setMarkdown()` per le note di rilascio,
  `QDesktopServices.openUrl` al posto di `webbrowser.open` per aprire la pagina GitHub Release —
  stesso "niente self-update automatico" della TUI (stessi motivi: onedir, `.pkg`
  firmato/notarizzato, `.exe` in esecuzione). Sostituisce il `QMessageBox` provvisorio di
  `DashboardScreen._mostra_esito_aggiornamento` (Fase 3). Refactor di supporto: `_UpdateCheckWorker`
  spostato da `dashboard.py` a `cartellino/gui/workers.py` come `UpdateCheckWorker` (classe
  pubblica, condivisa) — necessario perché ora serve anche a `MainWindow` per il controllo
  automatico all'avvio, mirror di `CartellinoApp._controlla_aggiornamenti_avvio`/`on_mount`
  (chiamato solo se non è il primo avvio/onboarding e solo se
  `UserConfig.check_updates_on_startup` è vero; fallisce silenziosamente, solo un `log.warning`,
  se la rete non è disponibile — stesso comportamento della TUI, per non degradare l'avvio
  offline). Verificato che il controllo all'avvio non blocchi il rendering della Dashboard (gira
  in `QThread` separato, la finestra è già interattiva mentre il worker è ancora in esecuzione).
  Verificato anche il binario impacchettato.
- **Fase 12 (Packaging) — completata.** Il grosso del lavoro era già stato fatto dallo spike di
  Fase 0 (`MERGE` di due `Analysis`/`EXE` in un unico onedir); questa fase ha verificato che non
  restasse nient'altro. `hiddenimports` mancanti per PySide6: **nessuno** — PySide6 ha già hook
  PyInstaller propri (bundled in `PySide6-Essentials`/`PySide6-Addons`, non serve
  `pyinstaller-hooks-contrib`), confermato dal file dei warning di build
  (`build/cartellino/warn-cartellino.txt`) dopo undici build locali consecutive (una per fase,
  Fase 1-11): l'unico avviso presente riguarda import condizionali di `pandas.io.clipboard`
  verso `PyQt4`/`qtpy` (irrilevanti, non toccano PySide6). Cartella onedir combinata: ~306 MB
  (macOS arm64, debug build locale non firmata/notarizzata — le dimensioni reali della Release
  dipendono anche da UPX/firma, verificabili solo in CI).
- **Fase 13 (CI/release) — completata (in attesa di validazione con una release `-rc` reale).**
  Decisione presa con l'utente prima di procedere (naming dei due launcher macOS): la GUI
  eredita il nome "Cartellino UniSA.app" (comportamento atteso da un doppio click), il launcher
  Terminale/TUI esistente è stato **rinominato** in "Cartellino UniSA (Terminale).app" — cambia
  il comportamento per chi ha già installato l'app da release precedenti (v2.0.x).
  - `packaging/macos/gui_launcher/`: nuovo bundle `.app` minimale per il lancio diretto della GUI
    — niente AppleScript/picker "quale terminale" (non applicabile, la GUI è già una finestra
    nativa): `Contents/MacOS/cartellino-unisa-gui-launcher` è un semplice script di shell che fa
    `exec` del binario installato (path assoluto, stesso motivo del launcher TUI), niente
    entitlement Apple Events. Verificato funzionante con un `open` reale su una copia di test
    puntata al binario buildato localmente (processo GUI effettivamente avviato).
  - `.github/workflows/release.yml`: step di firma "Genera e firma il launcher .app" rinominato/
    duplicato in due step distinti (TUI: invariato salvo il nuovo nome file; GUI: nuovo, firma
    senza `launcher-entitlements.plist` — non serve, nessun Apple Event); step di notarizzazione
    unificato in un loop sui due `.app`; step "Firma tutte le librerie native e l'eseguibile"
    esteso con firma/verifica esplicita anche di `cartellino-unisa-gui` (il loop esistente lo
    firmava già implicitamente, essendo un altro file di primo livello nell'onedir — l'aggiunta è
    per parità/verifica esplicita, stesso trattamento già riservato alla CLI); step del `.pkg`
    esteso per stagare entrambi i launcher nello stesso pkgroot. **Validato con `pkgbuild` reale
    in locale (senza firma/notarizzazione, nessun certificato disponibile qui)**: struttura del
    payload verificata via `pkgutil --expand` — entrambi i launcher e i due binari
    (`cartellino-unisa`/`cartellino-unisa-gui`) sono presenti al posto giusto. Sintassi YAML e di
    tutti gli step shell validata (`yaml.safe_load` + `bash -n` su ogni blocco `run`).
  - `packaging/macos/postinstall`: aggiunto symlink `/usr/local/bin/cartellino-unisa-gui` in
    parità con quello CLI esistente (comodo da riga di comando, non il modo principale di
    lanciare la GUI).
  - `packaging/linux/postinstall.sh`: stesso symlink aggiuntivo per `fpm`; **nessuna icona/voce
    desktop per la GUI su Linux** (fuori scope, richiederebbe un file `.desktop` e
    l'installazione nel tema icone di sistema — infrastruttura non ancora nel repo, coerente con
    la nota già presente in TODO_gui.md per le icone Linux in generale). I `.deb`/`.rpm`
    includono comunque `cartellino-unisa-gui` senza modifiche allo script `fpm` (pacchettizza
    già l'intera cartella onedir).
  - `packaging/windows/installer.iss`: `[Icons]` esteso con una voce "Cartellino UniSA" (ora la
    GUI, con icona sul Desktop opzionale) e una voce separata "Cartellino UniSA (Terminale)" per
    la TUI — nessun cambiamento allo step `[Files]` (già copia l'intera cartella onedir, include
    `cartellino-unisa-gui.exe` automaticamente); l'icona incorporata nell'eseguibile da
    PyInstaller (`icon=` in `cartellino.spec`, già condivisa tra i due `EXE()` dalla Fase 0) vale
    per entrambi senza bisogno di `IconFilename` esplicito.
  - `README.md`: sezione "Eseguibili standalone" aggiornata per macOS/Windows/Linux con le nuove
    istruzioni GUI+TUI (due launcher macOS, due voci Menu Start Windows, due binari Linux).
  - **Non ancora validato**: firma/notarizzazione/stapling reali (richiedono i secrets Apple, non
    disponibili in locale), build Windows/Linux reali in CI (Inno Setup, fpm), e l'intera catena
    end-to-end su GitHub Actions. Per costruzione questa fase **non può essere verificata
    interamente in locale come le precedenti** — il piano stesso lo segnala come rischio più alto
    ("procedere con una release `-rc` di prova dedicata"). Prossimo passo pratico: bump versione
    in `pyproject.toml` + tag `-rc` di prova (es. `v3.0.0-rc1`, da confermare con l'utente prima
    di pushare) per validare l'intera pipeline su CI reale, seguendo lo stesso schema già usato
    per v2.0.1/v2.0.2.
- **Fase 14 (QA manuale end-to-end) — completata (primo giro; da ripetere ad ogni fase futura per
  costruzione, come nota il piano).** Nessun framework di test automatico nel repo (`pytest-qt`
  resta un'opportunità futura, fuori scope): QA fatta catturando uno screenshot reale di ogni
  schermata (`QWidget.grab()`, funziona anche con `QT_QPA_PLATFORM=offscreen` — rendering
  software, non serve un vero window server) con dati reali dell'ambiente di sviluppo, poi
  ispezionati visivamente uno per uno — non solo "non va in crash" come le verifiche fatte nelle
  fasi precedenti, ma "si vede giusto". Trovati e corretti **due bug reali**, non solo cosmetici
  degli screenshot:
  1. **`CredentialsDialog` (Fase 10) usava `QDialogButtonBox` con pulsanti standard "Save"/
     "Cancel" in inglese** — le stringhe standard di Qt richiedono le traduzioni Qt integrate
     (`qttranslations`), non bundled nell'app, quindi restano in inglese di default; incoerente
     con un'app interamente in italiano. Sostituiti con `QPushButton` custom ("Salva"/"Annulla"),
     stesso pattern già usato in ogni altra schermata del progetto — nessun'altra schermata usava
     `QDialogButtonBox`, quindi il bug era isolato a questo dialog.
  2. **`CredentialsDialog` e `AppUpdateDialog` (caso "nessun aggiornamento", Fase 11): nessun
     widget "expanding" nel layout quando il dialog viene ridimensionato manualmente dall'utente**
     — lo spazio extra si distribuiva tra i singoli campi/etichette invece che raccogliersi in
     fondo, risultato visivamente rotto (verificato ridimensionando i dialog a mano nello script
     di QA: a dimensione naturale il bug non è visibile, si manifesta solo se l'utente allarga la
     finestra). Corretto con un `layout.addStretch()` prima della riga dei pulsanti in entrambi i
     casi — lo stesso pattern già presente "gratuitamente" nel ramo con release disponibile
     grazie al `QTextBrowser` con `stretch=1`, che assorbe già lo spazio extra.
  3. **Miglioria preventiva (non un bug osservato in produzione, ma un rischio concreto
     individuato durante la QA)**: `SettingsScreen` (Fase 8) e `DashboardScreen` (Fase 3) non
     avevano scroll — su una finestra piccola (es. laptop con schermo ridotto) il layout
     costringeva la finestra a crescere oltre la dimensione richiesta pur di mostrare tutti i
     campi, invece di offrire uno scroll come fa la TUI (`VerticalScroll`) per le stesse due
     schermate. Avvolti in `QScrollArea` (`setWidgetResizable(True)`): per la Dashboard solo il
     testo delle sezioni scorre, i pulsanti di navigazione restano sempre visibili in fondo (una
     scelta migliore della TUI, dove scrollano via anche i pulsanti); per Impostazioni scorre
     tutto il form. Verificato ridimensionando la finestra a 700×350/400: senza il fix la finestra
     si allargava oltre la dimensione richiesta, con il fix compare una scrollbar e la dimensione
     richiesta viene rispettata.
  Tutte le 12 schermate/dialog verificate visivamente con dati reali: Dashboard, Reports,
  Timesheet (mostra un file YAML di progetto reale), Statistiche (tutte e 8 le categorie,
  inclusa la vista Markdown dei riposi con tabelle/checkmark renderizzate correttamente),
  Settings (tutti i campi popolati), Date escluse, Update, Onboarding, CredentialsDialog,
  AppUpdateDialog (entrambi i casi). Rebuild PyInstaller ripetuta dopo ogni fix per confermare
  nessuna regressione nel binario impacchettato. Non testato in questo giro (richiede hardware/
  rete non disponibili qui): download Selenium reale end-to-end, generazione report/timesheet
  reale su disco, interazione da tastiera/mouse reale (solo `grab()` programmatico, non click
  reali) — da fare con un giro di QA umano prima di una release definitiva.
- **Prossimo passo**: Fase 15 (aggiornare `CLAUDE.md` con l'architettura `cartellino/gui/`, da
  fare "a fine sviluppo" per non documentare un'API ancora instabile — valutare se questo è già
  il momento giusto) oppure una release `-rc` di prova per validare la Fase 13 in CI reale.

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
