# Timesheet e rendiconto di progetto

Genera i fogli di rendicontazione mensile del progetto a partire dal cartellino elaborato.
Produce due tipologie di output nella cartella
`data/v2/{anno}/output/ore_svolte_per_giorno/{nome_progetto}/`:

| File | Descrizione |
|------|-------------|
| `{MM}_{mese}.xlsx` | Fogli mensili semplificati (uno per mese) |
| `TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx` | Rendiconto formale compilato dal template istituzionale |

Il rendiconto formale è opzionale: viene generato solo se si specifica `template_rendiconto`
nella configurazione YAML.

## 1. Configurazione YAML

Copia il template nella cartella `timesheet/` e adattalo:

```bash
cp templates/timesheet_progetto_template.yaml timesheet/mio_progetto.yaml
```

I file nella cartella `timesheet/` sono ignorati da git (dati personali). Il template in
`templates/` è invece versionato.

Struttura completa del file YAML:

```yaml
progetto:
  nome: "NOME_PROGETTO"           # nome della sottocartella di output
  cup: "D43C22005040001"          # CUP del progetto
  codice: "PNC-E3-2022-23683267"  # codice identificativo del progetto
  anno: 2025                      # anno da elaborare (deve coincidere con current_year)

  # (opzionale) Template Excel istituzionale per il rendiconto formale.
  # Se presente, genera anche TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx
  template_rendiconto: "templates/TS_DHEAL_COM_2025_Nome_Cognome.xlsx"

  # (opzionale) Dati anagrafici del dipendente per il rendiconto
  persona:
    figura_professionale: "Personale Tecnico Amministrativo (PTA)"
    nome: "Mario"
    cognome: "Rossi"
    codice_fiscale: "RSSMRA80A01F839X"

mesi:                        # mesi da includere (1-12)
  - 1
  - 2
  - 3

ore_totali: 100.0            # ore totali da distribuire

# (opzionale) Intervalli di giorni in cui TUTTE le ore lavorate vanno al progetto
giorni_interi:
  - da: "2025-01-15"
    a:  "2025-01-17"         # 15, 16, 17 gennaio: ore_progetto = ore_svolte
  - da: "2025-03-10"
    a:  "2025-03-10"         # singolo giorno

# (opzionale) Ore fisse su singole giornate
ore_fisse:
  - data: "2025-05-05"
    ore: 3.0                 # 3 ore esatte il 5 maggio
  - data: "2025-06-20"
    ore: 2.5
```

## 2. Esecuzione

```bash
# Passa solo il nome del file: viene cercato automaticamente in timesheet/
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto mio_progetto.yaml

# Oppure passa un percorso completo o relativo
uv run python cartellino_v2.py --no-aggiorna-cartellino --timesheet-progetto /percorso/assoluto/config.yaml
```

Disponibile anche da TUI/GUI, schermata **Timesheet progetto** — vedi [TUI](../usage/tui.md)/[GUI](../usage/gui.md).

## 3. Regole di distribuzione delle ore

1. Le ore dei `giorni_interi` (= ore effettivamente lavorate quel giorno) e delle `ore_fisse`
   vengono sommate e sottratte da `ore_totali` per ottenere le **ore residue**.
2. Le ore residue vengono spalmate equamente sulle giornate con **almeno 5 ore lavorate** che non
   rientrano nei punti precedenti, arrotondando alla **mezz'ora inferiore**.
3. L'eventuale resto viene sommato all'ultimo giorno idoneo in modo che il totale sia esattamente
   uguale a `ore_totali`.

## 4. Output: fogli mensili semplificati

Ogni file `{MM}_{mese}.xlsx` ha il formato:

| | 01 | 02 | 03 | ... |
|---|---|---|---|---|
| **Giorno** | 01 | 02 | 03 | ... |
| **Attività svolta sul progetto CUP: …** | 2.0 | 2.0 | 0 | ... |
| **Attività svolte su altri progetti** | 0 | 0 | 0 | ... |
| **Attività ordinaria** | 6.15 | 7.0 | 0 | ... |
| **Altro (Malattia, Ferie..)** | 0 | 0 | 0 | ... |

## 5. Output: rendiconto formale (opzionale)

Se `template_rendiconto` è impostato, viene generato `TS_{nome}_{anno}_{Cognome}_{Nome}.xlsx` a
partire dal template istituzionale `.xlsx`. Il file viene adattato all'anno di riferimento e
compilato automaticamente:

| Cella | Contenuto |
|-------|-----------|
| N12 | Nome del mese in maiuscolo (es. `FEBBRAIO`) |
| AG12 | Anno |
| C15 | CUP del progetto |
| C16 | Codice del progetto |
| C18 | Figura professionale |
| C19 | Nome |
| Y19 | Cognome |
| C20 | Codice fiscale |
| Y20 | Ore totali rendicontate nel mese |
| C22 | `Mese di Febbraio 2026` |
| Righe 24–27 | Ore progetto/ordinarie per ogni giorno del mese |

Vengono inoltre corretti automaticamente:

- **Colori weekend**: sabati e domeniche colorati con il grigio del template, lunedì–venerdì
  senza colore, in base al calendario effettivo dell'anno (non del template originale)
- **Fogli Riassuntivo**: i riferimenti formula ai fogli mensili vengono aggiornati con i nuovi
  nomi — il layout e la logica del Riassuntivo non vengono modificati

Se il rendiconto non viene generato o mostra errori, vedi [Troubleshooting](../reference/troubleshooting.md).
