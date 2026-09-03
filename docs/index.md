# Cartellino UniSA

Strumento Python per il download automatico e l'elaborazione del cartellino presenze da
[presenze.unisa.it](https://presenze.unisa.it). Calcola ore eccedenti, riposi compensativi,
credito ore mensile e genera timesheet per progetti di ricerca.

Disponibile come:

- **GUI** desktop ([PySide6](https://doc.qt.io/qtforpython-6/))
- **TUI** (interfaccia testuale interattiva, [Textual](https://textual.textualize.io/))
- **CLI** scriptabile, per uso non interattivo/automatizzato

Tutte e tre scaricabili come eseguibile standalone, senza installare Python — vedi
[Eseguibili standalone](getting-started/standalone-executables.md).

Il codice sorgente è su GitHub:
[staffDiUnisa/CartellinoUniSA](https://github.com/staffDiUnisa/CartellinoUniSA).

## Funzionalità

- **Download automatico** del cartellino da `presenze.unisa.it` tramite Selenium
- **Autenticazione** con Credenziali UNISA, SPID o CIE
- **Ore eccedenti** (`OE-DIU`): calcolo con esclusione date configurabili, anche con sottrazione
  parziale
- **Riposi compensativi**: raggruppamento automatico (soglia: 7h 12m per riposo) e correlazione
  con i riposi già fruiti
- **Credito ore** mensile per stato di elaborazione (`OO-DIU`)
- **Statistiche** multi-foglio: ticket mensa, visite specialistiche, straordinari, malattia,
  ferie, vigilanza concorsi, permessi gravi motivi, entrata in ritardo
- **Ore giornaliere** lavorate per mese
- **Timesheet di progetto**: distribuzione configurabile delle ore su mesi selezionati, con
  giorni interi e ore fisse, output in Excel mensile per subfolder di progetto
- **Rendiconto formale**: compilazione automatica del template Excel istituzionale (`TS_*.xlsx`)

## Da dove iniziare

- Prima installazione: [Prerequisiti e installazione](getting-started/installation.md)
- Non vuoi installare Python: [Eseguibili standalone](getting-started/standalone-executables.md)
- Configurare credenziali e opzioni: [Configurazione](getting-started/configuration.md)
- Uso quotidiano: [TUI](usage/tui.md), [GUI](usage/gui.md), [CLI](usage/cli.md)
- Qualcosa non funziona: [Troubleshooting](reference/troubleshooting.md)
- Hai trovato un bug: [Segnalare un bug](reference/troubleshooting.md#segnalare-un-bug)

!!! note "Documentazione interna"
    Questo sito copre l'uso dell'applicazione. Per i dettagli implementativi interni (packaging,
    firma/notarizzazione, decisioni architetturali minute) la fonte di verità resta
    [`CLAUDE.md`](https://github.com/staffDiUnisa/CartellinoUniSA/blob/master/CLAUDE.md) nel
    repository — vedi anche la [Guida per sviluppatori](developer-guide/architecture.md).
