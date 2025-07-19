![License](https://img.shields.io/badge/License-GPL_3.0_license-badge?style=plastic&logo=unlicense&logoColor=white&link=.%2FLICENSE) ![Python >=3.12](https://img.shields.io/badge/Python-_>=_3.12-3670A0?style=plastic&logo=python&logoColor=ffdd54) ![PyCharm](https://img.shields.io/badge/pycharm-143?style=plastic&logo=pycharm&logoColor=black&color=black&labelColor=green) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=plastic&logo=linux&logoColor=black) ![macOS](https://img.shields.io/badge/mac%20os-000000?style=plastic&logo=macos&logoColor=F0F0F0) ![Selenium](https://img.shields.io/badge/selenium-python_selenium-%43B02A?style=plastic&logo=selenium&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=plastic&logo=github&logoColor=white)


# Elaborazione cartellino UniSA
Applicazione per l'estrazione di informazioni dal proprio cartellino UniSA

## Installazione
***Richiede Python >= 3.12***
1. Create un virtual environment Python e installare tutti i pacchetti richiesti

```bash
python3 -m venv .venv
source .venv/activate
python3 -m pip install -r requirements.txt
```
2. Creare il file `.env` a partire dal file `env.template` 

```bash
cp env.template .env
```

3. Editare il file `.env` per settare il valore delle variabili `USERNAME` e `PASSWORD` per inserire le proprie credenziali UniSA.
4. Eseguire lo script `main.py` e attendere che venga scaricato il proprio cartellino, si aprirà una finestra di Firefox e l'applicazione scorrerà i dettagli del cartellino ***ATTENZIONE:*** Questo script funziona solo dalla rete interna dell'università
```bash
python main.py
```
5. [OPZIONALE] Nella cartella `data`, creata dallo script del punto precedente aprire la cartella `input` e creare il file `date_escluse.txt` che contiene le date in cui si sa che ci sono delle Ore di Eccedenza che devono essere scluse dal conto, esempio per dello straordinario fatto in quel giorno. Le date devono essere nel formato ggg dd mmm, ed una per riga
```bash
vim data/input/date_escluse.txt
```

_es:_

```
gio 16 gen
ven 17 gen
```
6. [OPZIONALE] Nella cartella `data`, creata dallo script del punto precedente aprire la cartella `input` e creare il file `riposi_usati.txt` che contiene le date di Rriposi compensativi già usati. Le date devono essere nel formato YYYY-MM-DD, ed una per riga
```bash
vim data/input/riposi_usati.txt
```

_es:_

```
2025-06-26
2025-06-27
```

7. Eseguire lo script `process.py`per l'elaborazione del cartellino, i risutati saranno nella cartella `data/output` ***ATTENZIONE:*** Questo script non accede ai datid el cartellino online, ma lavora su quelli scaricati nel punto 4 e può essere esguito anche fuori della rete universitaria
```bash
python process.py
```
## Esecuzione
1. Una volta al giorno eseguire lo script `main.py`per aggiornare i dati del cartellino ***ATTENZIONE:*** Questo script funziona solo dalla rete interna dell'università, si sconsiglia di eseguirlo più di una volta al giorno
```bash
python main.py
```
2. Se necessario aggiornare i file `date_escluse.txt`e `riposi_usati.txt`
3. Eseguire lo script `process.py`per elaborare i dati del cartellino. ***ATTENZIONE:*** Questo script non accede ai datid el cartellino online, ma lavora su quelli scaricati nel punto 1 e può essere esguito anche fuori della rete universitaria
```bash
python process.py
```
