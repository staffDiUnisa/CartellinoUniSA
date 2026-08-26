# TODO — Roadmap verso v2.0.0

> Stato attuale rilasciato come [`v1.2.0`](https://github.com/staffDiUnisa/CartellinoUniSA/releases/tag/v1.2.0).
> Obiettivo v2.0.0: TUI (Textual) al posto dei prompt CLI, credenziali in OS keyring,
> tooling `mise`/`uv` al posto di `pip`/`venv`, dashboard iniziale sullo stato del cartellino,
> eseguibili standalone per macOS/Windows/Linux.

Decisioni prese:
- La v2 avrà **sia TUI che flag CLI non interattivi** (per uso scriptato).
- Credenziali salvate nel **keyring nativo del SO** (libreria `keyring`), non file cifrato custom.
- Eseguibili generati con **PyInstaller in CI (GitHub Actions)**, un job per OS, allegati alla Release.
  Chrome resta dipendenza esterna obbligatoria (Selenium non è bundlabile).
- **Niente SQLite/DB relazionale.** Il file scaricato è già la cache persistente tra un'esecuzione
  e l'altra (nessun re-download necessario per vedere la dashboard). I calcoli derivati (riposi,
  credito ore, statistiche) sono ricalcolati in memoria ad ogni avvio: dataset piccolo (poche
  centinaia di righe/anno), pandas ricalcola in <1s.
- **Storage dati grezzi**: da `cartellino.xlsx` a **Feather** (`pyarrow`) — preserva meglio i dtype
  del DataFrame ed è più veloce da leggere/scrivere di un roundtrip Excel. **xlsx/csv diventano
  solo formati di export on-demand**, selezionabili da Impostazioni (default xlsx).

## Dashboard iniziale (mostrata subito all'avvio della TUI)

Legge direttamente il Feather già su disco, **senza forzare un nuovo download**:

1. **Eccezioni del mese corrente** su codici configurabili (default `ERIT`, `SCN`)
2. **Saldo ore del mese corrente**, somma di codici configurabili (default `CRE`, `OE-DIU`, `SCN`)
3. **Riepilogo riposi compensativi**, per categoria:
   - completi e confermati (tutte le ore `[OK]`, cioè `stato == "ELAB P1"`)
   - completi ma non confermati (soglia 7h12m raggiunta, ma almeno un'ora `"ELAB GG"` → `[NO]`)
   - da completare (indicando le ore mancanti, `RiposoCompensativo.ore_mancanti()`)
   - già usati (`riposo.data` valorizzata, matchata con `SRC`)
4. **Giorni di ferie già utilizzati** nell'anno corrente (`FER`/`FEV`/`FST`)
5. **Permessi per gravi motivi familiari (PMF)** utilizzati nell'anno corrente
6. Data/ora dell'ultimo download (mtime del file Feather), per capire se i dati sono freschi
7. Se il Feather non esiste ancora (primo avvio), stato vuoto che invita al download

### Note tecniche sulla categorizzazione dei riposi compensativi

`OreEccedenti.raggruppa()` (esistente, `cartellino/ore_eccedenti.py`) già restituisce
`list[RiposoCompensativo]`. La categorizzazione per la dashboard è puro post-processing su quel
risultato, nessuna modifica alla logica di raggruppamento:

```
per ogni riposo in riposi:
    se riposo.data è valorizzata            -> USATO (SRC)
    altrimenti se riposo.ore_mancanti() <= 0:
        se tutte le ore_inserite hanno stato == "ELAB P1"  -> COMPLETO E CONFERMATO
        altrimenti                                          -> COMPLETO NON CONFERMATO
    altrimenti                               -> DA COMPLETARE (mancano riposo.ore_mancanti())
```

I due soli valori di stato realmente usati nel cartellino sono `"ELAB P1"` (confermato) e
`"ELAB GG"` (non confermato) — vedi confronto letterale già esistente in
`cartellino/ore_eccedenti.py` (`salva_testo`, formattazione `[OK]`/`[NO]`).

### Note su SCN/CRE e saldo mensile configurabile

- `SCN` non esiste ancora nel codice: stesso formato di `OE-DIU` nel testo "Voci Base"
  (pattern numerico `HH.MM`), stessa logica di estrazione già in `OreEccedenti._elabora`.
- `CRE` è già presente come codice raw nel cartellino ma non filtrato (elencato tra i "codici non
  usati" da `process.py`); trattato con lo stesso pattern di estrazione.
- Serve un helper condiviso che, dato un elenco di codici, filtra le righe
  (`Cartellino._filter`, già supporta codici arbitrari) e somma le ore estratte con lo stesso
  pattern regex oggi hardcoded per OE-DIU — riusato per il saldo mensile dashboard.

### Note su ferie/PMF "utilizzati"

`cartellino/statistiche.py` oggi espone solo elenchi grezzi (`Stato`, `Data`, `Voci Base`) per
ferie e PMF, senza logica di "usato/non usato" (a differenza di `TCK`, che ha già `data_ticket.txt`
come cutoff). Per la dashboard, "giorni utilizzati" è semplicemente il conteggio delle righe già
presenti nel cartellino per quei codici — nessuna proiezione futura richiesta.

---

## Fase 1 — Migrazione ambiente: pip/venv → mise/uv ✅

- [x] Creare `pyproject.toml` (metadati progetto, `requires-python = ">=3.12"`, dipendenze da
      `requirements.txt` + nuove: `textual`, `keyring`, `platformdirs`, `pyarrow` (per Feather))
- [x] Generare `uv.lock` (`uv lock`)
- [x] Aggiungere `.mise.toml` (pin versione Python, tool `uv`, task `install`/`app`)
- [x] Rimuovere `requirements.txt` (nessun bisogno di compatibilità con `pip` legacy)
- [x] Aggiornare `README.md` / `CLAUDE.md` con le nuove istruzioni di setup
      (`mise install`, `uv sync`, `uv run ...`)
- [x] Aggiornare eventuale CI esistente per usare `mise`/`uv` invece di `pip`
      (nessuna CI esistente nel repo, nulla da migrare)

## Fase 2 — Credenziali sicure (OS keyring) + config utente ✅

- [x] Modulo `cartellino/credentials.py` con `keyring.set_password`/`get_password`
      (service name dedicato, `"cartellino-unisa"`) per USERNAME/PASSWORD UniSA
- [x] File di config TOML in cartella utente standard (via `platformdirs`,
      `cartellino/user_config.py::UserConfig`) per: `current_year`, `min_date_riposi_usati`,
      `headless`, **formato di export** (xlsx/csv, default xlsx), **codici eccezione dashboard**
      (default `["ERIT", "SCN"]`), **codici saldo mensile** (default `["CRE", "OE-DIU", "SCN"]`)
- [x] Import automatico da `.env` legacy alla prima esecuzione v2
      (`migrate_from_env_if_needed`, invocato da `Config.load()`), con raccomandazione di
      eliminare `.env` dopo la migrazione. Nota: l'"offerto da TUI" del testo originale diventa
      "automatico e silenzioso" finché la TUI (Fase 4) non esiste ancora
- [x] Aggiornare `get.py` / `cartellino/config.py` per leggere da keyring/config
      (`Config.load()`, con fallback su `Config.from_env()` se manca sia `config.toml` che `.env`)
- [x] Aggiornare `env.template`, `README.md`, `CLAUDE.md`

## Fase 3 — Storage dati: Feather per l'import, xlsx/csv solo on-demand (parziale) ✅

- [x] `get.py`: dopo lo scraping, salvare il DataFrame grezzo in
      `data/v2/{anno}/input/cartellino.feather` (via `df.to_feather`) invece di scrivere
      direttamente `cartellino.xlsx`
- [x] `cartellino/cartellino.py`: generalizzato `Cartellino.from_excel`/`from_feather`/`load`,
      con fallback di migrazione one-shot da un `cartellino.xlsx` legacy se il Feather non esiste
- [ ] Tutte le pipeline di output (`Cartellino.salva`, `OreEccedenti.salva_dettaglio`,
      `salva_testo`, `CreditoOre.salva`, `Statistiche.salva`) smettono di scrivere
      automaticamente su disco ad ogni esecuzione: restano metodi disponibili, ma vengono
      invocati **on demand** dalla TUI/CLI (un'azione per report), nel formato scelto in
      Impostazioni (xlsx o csv — per csv, un file per foglio dove il report è multi-sheet)

      **Deciso di rimandare** questo punto a quando esisteranno TUI (Fase 4) o CLI con flag per
      report singolo (Fase 5): oggi `cartellino_v2.py` è l'unico entrypoint utilizzabile, e
      disaccoppiare la scrittura automatica ora lo renderebbe silenzioso/inutile senza un modo
      per invocare i report singolarmente. `Config.export_format` esiste già lato config per
      quando questo punto verrà ripreso.
- [x] Helper condiviso per estrarre ore da "Voci Base" dato un elenco di codici
      (`cartellino/ore_helpers.py::estrai_ore_minuti`/`somma_ore_per_codici`, generalizzazione del
      pattern regex prima duplicato in `OreEccedenti._elabora`), riusabile per il saldo mensile
      dashboard (Fase 4)

## Fase 4 — Fondamenta TUI con Textual

Nuovo entrypoint `cartellino_tui` (Textual `App`). File principali:
`cartellino/tui/app.py`, `cartellino/tui/screens/*.py`, `cartellino/tui/widgets/*.py`.

- [ ] Schermata **Onboarding/Setup**: form per credenziali/config se mancanti
- [ ] **Schermata Dashboard/Home** (vedi sezione dedicata sopra), con **versione app sempre
      visibile** in header/footer (letta da `pyproject.toml` via `importlib.metadata`)
- [ ] **Scelta aggiornamento**: azione esplicita "Aggiorna cartellino" (mai automatica
      all'apertura) con `Switch`/pulsante al posto del prompt `y/N`
- [ ] **Scelta metodo di autenticazione**: `RadioSet` (Credenziali UNISA / SPID / CIE),
      opzione UNISA disabilitata se `is_on_unisa_network()` è False (funzione esistente in
      `get.py`, da riusare)
- [ ] **Log/Progress view**: `RichLog` per output in tempo reale — richiede refactor di
      `get.py`/`cartellino/*.py` per usare `logging` invece di `print()` diretti; operazioni
      lunghe (Selenium, elaborazione) lanciate via `App.run_worker`
- [ ] **Schermata Impostazioni**: anno, min date, formato export, liste codici configurabili
      (eccezioni + saldo mensile), gestione credenziali (keyring)
- [ ] **Report on-demand**: schermata/menu per generare singolarmente i report (riposo
      compensativo, credito ore, statistiche, ore giornaliere) nel formato scelto
- [ ] **Timesheet di progetto**: selezione/creazione YAML da `timesheet/`
      (riusa `ConfigTimesheet.from_yaml`)

## Fase 5 — Parità funzionale CLI non interattiva

- [ ] Entrypoint CLI (Typer) con flag equivalenti (`--no-aggiorna-cartellino`,
      `--timesheet-progetto`, `--auth-method {unisa,spid,cie}`, `--export-format {xlsx,csv}`)
- [ ] CLI e TUI condividono le stesse funzioni di dominio e lo stesso storage
      credenziali/config/dati (Fasi 2-3)
- [ ] Rimuovere/sostituire `cartellino_v2.py` legacy con entrypoint unico non interattivo
      + entrypoint TUI separato

## Fase 6 — Packaging multipiattaforma (PyInstaller + GitHub Actions)

- [ ] `packaging/cartellino.spec` per PyInstaller (entrypoint TUI), con hidden-imports per
      Textual, `pyarrow` e Selenium/webdriver-manager
- [ ] Workflow `.github/workflows/release.yml`: matrix macOS/Windows/Linux, ognuno esegue
      `mise install && uv sync && uv run pyinstaller packaging/cartellino.spec`, allega il
      binario alla GitHub Release (trigger su push tag `v2.*`)
- [ ] Documentare nel `README.md`: Chrome resta dipendenza esterna obbligatoria; binari non
      firmati/notarizzati possono generare avvisi Gatekeeper (macOS) / SmartScreen (Windows),
      con istruzioni per sbloccarli

## Fase 7 — Rilascio v2.0.0

- [ ] Bump versione a `2.0.0` in `pyproject.toml`
- [ ] Tag `v2.0.0` + GitHub Release con i binari allegati dalla pipeline CI

---

## Analisi dipendenze tra fasi

```
Fase 1 (mise/uv)
  ├─→ Fase 2 (keyring/config)  ──┐
  └─→ Fase 3 (Feather/export)  ──┼─→ Fase 4 (TUI) ──┬─→ Fase 6 (packaging) ─→ Fase 7 (release)
                                  │                    │
                                  └─→ Fase 5 (CLI) ────┘
```

- **Fase 1** è prerequisito puro per 2, 3, 6 (dichiara le nuove dipendenze `textual`, `keyring`,
  `platformdirs`, `pyarrow` nel `pyproject.toml`). Nessuna dipendenza in ingresso.
- **Fase 2** e **Fase 3** sono indipendenti tra loro — possono procedere **in parallelo** una
  volta chiusa la Fase 1 (toccano moduli diversi: credenziali/config vs. storage dati/pipeline
  di output). Entrambe sono prerequisito per la Fase 4 (la dashboard iniziale legge sia il
  Feather sia i codici configurabili da Fase 2) e per la Fase 5 (CLI legge lo stesso storage).
- **Fase 4** dipende da 2+3 completate (non ha senso costruire onboarding/dashboard su uno
  storage o un formato di credenziali ancora instabile). Durante la Fase 4, i `print()` in
  `get.py`/`cartellino/*.py` vengono sostituiti con `logging` — questo refactor va fatto una
  sola volta e **beneficia anche la Fase 5** (stesso layer di dominio, niente duplicazione).
- **Fase 5** può partire in parallelo alla Fase 4 (stessa base 2+3), ma il taglio finale di
  `cartellino_v2.py` legacy conviene farlo solo dopo che il layer di dominio condiviso è stato
  stabilizzato durante la Fase 4, per evitare di rifare la stessa rifattorizzazione due volte.
- **Fase 6** dipende da Fase 1 (build tool) e Fase 4 (serve un entrypoint TUI funzionante da
  impacchettare); beneficia anche del completamento di Fase 5 per impacchettare/validare pure
  il percorso CLI non interattivo.
- **Fase 7** dipende dal completamento di tutte le fasi precedenti.

**Percorso critico**: Fase 1 → (Fase 2 ∥ Fase 3) → Fase 4 → Fase 6 → Fase 7. La Fase 5 non è sul
percorso critico se sviluppata in parallelo alla Fase 4, ma richiede comunque che 2+3 siano
chiuse prima di partire.

## Stima di complessità e impatto

Stima relativa (non ore precise), pensata per sviluppo part-time da parte di una persona sola:
`S` = 1-2 giorni, `M` = 3-5 giorni, `L` = 6-10 giorni, `XL` = 10+ giorni.

| Fase | Complessità | Impatto utente | Rischio principale |
|------|:---:|:---:|---|
| 1. mise/uv | **S** | Basso (solo setup) | Basso — cambio tooling ben documentato, reversibile |
| 2. Keyring + config | **M** | Medio (cambia il flusso di setup credenziali) | Backend keyring assente su Linux headless/minimale; migrazione da `.env` da testare bene |
| 3. Feather + export on-demand | **L** | Alto (cambia formato dati e comportamento di scrittura file) | **Rischio più alto di regressione**: tocca tutta la pipeline core (`Cartellino`, `OreEccedenti`, `CreditoOre`, `Statistiche`); serve fallback di migrazione da xlsx legacy e writer CSV nuovi (oggi esiste solo il path xlsx via `apply_table_format`) |
| 4. TUI Textual | **XL** | **Alto — è il cuore della richiesta** | Superficie più ampia (più schermate, worker thread per Selenium/elaborazione bloccanti, refactor `print()`→`logging`); maggiore effort totale di tutta la roadmap |
| 5. CLI non interattiva | **M** | Medio (solo utenti che scriptano) | Duplicazione di logica se non si riusa bene il layer condiviso costruito in Fase 4 |
| 6. Packaging PyInstaller | **L** | Alto (rende l'app installabile senza Python) | Quirk specifici per OS: hidden-imports per Textual/pyarrow/Selenium, percorso cache di `webdriver-manager` in binario "frozen", avvisi Gatekeeper/SmartScreen non firmati |
| 7. Release v2.0.0 | **S** | Alto (simbolico: consegna finale) | Nessuno, è solo tagging/release una volta che 1-6 sono verdi |

**Nota**: la Fase 4 è di gran lunga la più corposa (stimabile quanto tutte le altre fasi messe
insieme) perché non è solo "wrapping" delle classi esistenti in widget, ma richiede: gestione
asincrona delle operazioni bloccanti (Selenium `WebDriverWait`, I/O su disco) tramite
`App.run_worker`, un logging bridge per il `RichLog`, e la costruzione ex-novo di 6+ schermate.
Vale la pena valutare se spezzarla in sotto-milestone incrementali (es. prima Dashboard+Onboarding
in sola lettura, poi le azioni di download/export) invece di consegnarla in un unico blocco.
