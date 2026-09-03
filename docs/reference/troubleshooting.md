# Troubleshooting

**Chrome non si avvia / ChromeDriver non trovato**

- Assicurarsi che Google Chrome sia installato
- Il driver viene scaricato automaticamente da `webdriver_manager`; verificare la connessione
  internet al primo avvio

**Timeout durante il login con SPID o CIE**

- Il browser rimane aperto per 10 minuti in attesa del completamento del login; completare
  l'autenticazione entro quel tempo

**"Credenziali UNISA" non disponibile**

- L'opzione compare solo se si è connessi alla rete universitaria (VPN compresa)

**Date non riconosciute in `date_escluse.txt`**

- Verificare il formato: `DD-MM-YYYY` oppure `DD-MM-YYYY HH:MM` — vedi
  [File di input](../dati-cartellino/input-files.md)

**`min_date_riposi_usati`/`MIN_DATE_RIPOSI_USATI` non riconosciuta**

- Il formato è `MM-DD` (mese-giorno), es. `06-01` per il 1° giugno
- In caso di errore, viene usato automaticamente `riposi_usati.txt`

**Totale timesheet non corrisponde**

- Se le ore dei `giorni_interi` e `ore_fisse` superano `ore_totali`, viene stampato un avviso e
  le ore residue sono azzerate
- Se il resto da aggiungere all'ultimo giorno è ≥ 30 min, viene stampato un avviso (il totale è
  comunque corretto)
- Vedi [Timesheet e rendiconto](../dati-cartellino/timesheet.md)

**Il rendiconto non viene generato**

- Verificare che `template_rendiconto` sia presente nel YAML e che il file `.xlsx` esista al
  percorso indicato
- Il template deve essere un file `.xlsx` (non `.xlsm`) con i fogli mensili rinominati nel
  formato `{Mese} {anno}` (es. `Gennaio 2025`)

**Errori `#REF!` nel foglio Riassuntivo**

- Non si verifica con i file generati dallo script, che aggiorna automaticamente i riferimenti
  formula
- Può accadere se si rinominano manualmente i fogli mensili senza aggiornare il Riassuntivo

**Eseguibile standalone non firmato/verificato (macOS, Windows)**

- Vedi le note specifiche per sistema operativo in [Eseguibili standalone](../getting-started/standalone-executables.md)

## Segnalare un bug

Se un problema non è tra quelli elencati sopra, o pensi di aver trovato un bug, apri una
[issue su GitHub](https://github.com/staffDiUnisa/CartellinoUniSA/issues/new) — è il canale
ufficiale per le segnalazioni, permette di tenere traccia dello stato (in lavorazione, risolto,
in quale release) e di collegare la segnalazione al commit/release che la risolve.

Per una segnalazione utile, includi quando possibile:

- **Versione** dell'applicazione (mostrata nell'header della TUI, nel titolo della finestra GUI,
  o `cartellino-unisa --version` per la CLI) e **sistema operativo**
- **Come stai eseguendo l'app**: eseguibile standalone (installer/`.pkg`/`.deb`/`.rpm`/zip) oppure
  da sorgente (`uv run ...`)
- **Passi per riprodurre** il problema, e cosa ti aspettavi che succedesse invece
- Se disponibile, il **log**: `cartellino_tui.log`/`cartellino_gui.log` nella cartella dati
  dell'app (vedi [Struttura dati](../dati-cartellino/data-layout.md)) — **verifica prima di
  allegarlo che non contenga dati personali** (credenziali, dati del cartellino)
