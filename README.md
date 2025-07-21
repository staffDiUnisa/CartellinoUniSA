# 📊 Elaborazione Cartellino UniSA

![License](https://img.shields.io/badge/License-GPL_3.0-blue?style=for-the-badge&logo=gnu&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

Applicazione Python per l'estrazione automatica e l'elaborazione dei dati dal cartellino presenze UniSA, con calcolo automatico di ore eccedenti e riposi compensativi.

## 🎯 Funzionalità Principali

- **Download automatico** del cartellino presenze da https://presenze.unisa.it
- **Calcolo ore eccedenti** (OE-DIU) con esclusione date configurabili
- **Gestione riposi compensativi** con raggruppamento automatico (7h 12m per riposo)
- **Calcolo credito ore** mensile (OO-DIU)
- **Export dati** in Excel e file di testo formattati

## 📋 Prerequisiti

- Python >= 3.12
- Connessione alla rete universitaria (solo per il download del cartellino)
- Browser Firefox installato
- Account UniSA valido

## 🚀 Installazione

### 1. Clonazione del repository
```bash
git clone https://github.com/staffDiUnisa/CartellinoUniSA.git
cd elaborazione-cartellino-unisa
```

### 2. Creazione ambiente virtuale
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oppure
.venv\Scripts\activate  # Windows
```

### 3. Installazione dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configurazione credenziali
```bash
cp env.template .env
```

Modifica il file `.env` con i tuoi dati:
```env
USERNAME=mario.rossi@unisa.it
PASSWORD=TuaPasswordSicura
CURRENT_YEAR=2025
MIN_DATE_RIPOSI_USATI=01-01  # Formato MM-DD
```

## 📁 Struttura delle Directory

```
elaborazione-cartellino-unisa/
├── data/
│   ├── input/
│   │   ├── cartellino.xlsx        # Dati scaricati dal portale
│   │   ├── date_escluse.txt       # Date da escludere dal calcolo
│   │   └── riposi_usati.txt       # Riposi già utilizzati
│   └── output/
│       ├── cartellino.xlsx         # Cartellino elaborato
│       ├── riposo_compensativo.xlsx # Dettaglio ore eccedenti
│       ├── credito_ore.xlsx        # Credito ore mensile
│       └── riposi_compensativi.txt # Riepilogo riposi
├── model/
│   ├── ore_inserite.py
│   └── riposo_compensativo.py
├── main.py                         # Entry point principale
├── get.py                          # Modulo download cartellino
└── process.py                      # Modulo elaborazione dati
```

## 💻 Utilizzo

### Esecuzione con download cartellino (solo rete UniSA)
```bash
python main.py

# Output:
Esegue lo script per l'estrazione dei dati dal cartellino.
Se scegli di non aggiornare i dati, salterà il processo di aggiornamento i dati da https://presenze.unisa.it.
Vuoi aggiornare i dati del cartellino (L'aggiornamento funziona solo dalla rete universitaria.)? [y/N]: y
Processing page 1
Processing page 2
Processing page 3
Processing page 4
Data da cui verranno considerati i Riposi Compensativi Usati: 01-01-2025
Scrivo riposi compensativo su data/output/riposo_compensativo.xlsx
Scrivo riposi compensativi su data/output/riposi_compensativi.txt
Scrivo credito ore su data/output/credito_ore.xlsx
```

### Esecuzione solo elaborazione (senza download)
```bash
python main.py

# Rispondere 'n' al prompt per elaborare solo i dati già scaricati
Vuoi aggiornare i dati del cartellino? [y/N]: n
```

## 📝 Configurazione File di Input

### `date_escluse.txt`
Contiene le date da escludere dal calcolo ore eccedenti (es. straordinari):
```
gio 16 gen
ven 17 gen
lun 20 gen
```

### `riposi_usati.txt` (opzionale)
Usato solo se `MIN_DATE_RIPOSI_USATI` non è configurato:
```
2025-06-26
2025-06-27
2025-07-15
```

## 📊 Output Generati

### 1. `riposo_compensativo.xlsx`
Excel con due fogli:
- **dettaglio**: Elenco completo ore eccedenti giornaliere
- **riassunto**: Riepilogo per stato (ELAB GG, etc.)

### 2. `riposi_compensativi.txt`
Riepilogo testuale dei riposi compensativi:
```
_________________________________________________
Riposo compensativo 1: - usato per il 26-06-2025
_________________________________________________
	- mer 01 gen -> 2:30 [ELAB GG]
	- gio 02 gen -> 1:45 [ELAB GG]
	- ven 03 gen -> 2:57 [ELAB GG]
_________________________________________________
Riposo compensativo 2: - ore necessarie al completamento: 5:42
_________________________________________________
	- lun 06 gen -> 1:30 [ELAB GG]
_________________________________________________
```

### 3. `credito_ore.xlsx`
Credito ore mensile aggregato per stato e mese.

## ⚙️ Variabili d'Ambiente

| Variabile | Descrizione | Esempio |
|-----------|-------------|---------|
| `USERNAME` | Email UniSA | mario.rossi@unisa.it |
| `PASSWORD` | Password account UniSA | ******** |
| `CURRENT_YEAR` | Anno di elaborazione | 2025 |
| `MIN_DATE_RIPOSI_USATI` | Data minima riposi (MM-DD) | 01-01 |

## 🔧 Troubleshooting

### Errore di connessione
- Verificare di essere connessi alla rete universitaria
- Controllare le credenziali nel file `.env`

### Firefox non si apre
- Installare Firefox: `sudo apt install firefox` (Linux)
- Verificare geckodriver: `pip install --upgrade selenium`

### Date non riconosciute
- Verificare il formato in `date_escluse.txt`: `ggg DD mmm`
- Controllare che l'anno in `.env` sia corretto

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch: `git checkout -b feature/nuova-funzionalita`
3. Commit: `git commit -m 'Aggiunta nuova funzionalità'`
4. Push: `git push origin feature/nuova-funzionalita`
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è distribuito sotto licenza GPL 3.0. Vedi il file [LICENSE](LICENSE) per maggiori dettagli.

## ⚠️ Disclaimer

Questo software è fornito "così com'è", senza garanzie di alcun tipo. L'uso è a proprio rischio e responsabilità. Gli autori non sono responsabili per eventuali errori nei calcoli o nell'interpretazione dei dati.

---

**Nota**: Per motivi di sicurezza, non condividere mai il file `.env` contenente le tue credenziali!