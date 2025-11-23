# 🛠️ Guida Sviluppo - TanaLeague

Guida pratica per sviluppatori e manutentori di TanaLeague.

---

## 📋 Indice

- [Setup Ambiente](#-setup-ambiente)
- [Requirements (Dipendenze)](#-requirements-dipendenze)
- [Logging (Log dell'applicazione)](#-logging)
- [Testing (Test automatici)](#-testing)
- [CI/CD (Test automatici su GitHub)](#-cicd)
- [Struttura File](#-struttura-file)
- [Comandi Utili](#-comandi-utili)

---

## 🚀 Setup Ambiente

### Locale (sul tuo PC)

```bash
# 1. Clona il repository
git clone <url-repository>
cd TanaLeague

# 2. Crea ambiente virtuale (opzionale ma consigliato)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Avvia l'app
cd tanaleague2
python app.py
```

### PythonAnywhere

```bash
# 1. Vai nella directory del progetto
cd ~/TanaLeague

# 2. Installa/aggiorna dipendenze
pip install --user -r requirements.txt

# 3. Reload webapp dal tab Web
```

---

## 📦 Requirements (Dipendenze)

### Cos'è `requirements.txt`?

È un file che elenca tutte le librerie Python necessarie con le versioni esatte.

**Posizione:** `/home/user/TanaLeague/requirements.txt`

### Perché è importante?

| Senza requirements.txt | Con requirements.txt |
|------------------------|----------------------|
| "Sul mio PC funziona, sul server no" | Stesso codice ovunque |
| Versioni diverse = bug misteriosi | Versioni identiche = comportamento identico |
| Difficile collaborare | Chiunque può installare l'ambiente |

### Come usarlo

**Installare tutte le dipendenze:**
```bash
pip install -r requirements.txt
```

**Su PythonAnywhere:**
```bash
pip install --user -r requirements.txt
```

**Aggiungere una nuova libreria:**
```bash
# 1. Installa la libreria
pip install nome-libreria

# 2. Aggiorna requirements.txt
pip freeze > requirements.txt
```

### Contenuto attuale

```
Flask>=2.3.0          # Web framework
gspread>=5.10.0       # Google Sheets API
google-auth>=2.22.0   # Autenticazione Google
pandas>=2.0.0         # Elaborazione dati
pytest>=7.4.0         # Testing (solo sviluppo)
pytest-cov>=4.1.0     # Coverage test (solo sviluppo)
```

---

## 📝 Logging

### Cos'è il Logging?

Un sistema per registrare cosa succede nell'applicazione, salvando i messaggi su file.

**Posizione:** `/home/user/TanaLeague/tanaleague2/logger.py`

### Perché usare logging invece di print()?

| print() | logging |
|---------|---------|
| Sparisce quando chiudi il terminale | Salvato su file permanentemente |
| Tutto uguale | Livelli: DEBUG, INFO, WARNING, ERROR |
| Nessun timestamp | Data e ora automatici |
| Nessun controllo | Puoi attivare/disattivare livelli |

### Come usarlo nel codice

```python
# All'inizio del file Python
from logger import get_logger
logger = get_logger(__name__)

# Nel codice, invece di print()
logger.info("Torneo importato con successo")
logger.warning("Cache scaduta, ricarico dati")
logger.error("Errore durante import")
```

### Livelli di log

| Livello | Quando usarlo | Esempio |
|---------|---------------|---------|
| `DEBUG` | Dettagli tecnici per debugging | `logger.debug(f"Variabile x = {x}")` |
| `INFO` | Operazioni normali completate | `logger.info("Import completato")` |
| `WARNING` | Situazione anomala ma gestita | `logger.warning("Retry connessione")` |
| `ERROR` | Errore che impedisce operazione | `logger.error("File non trovato")` |

### Dove vanno i log

```
tanaleague2/logs/
├── tanaleague.log        # Log principale (INFO e superiori)
└── tanaleague_debug.log  # Log dettagliato (solo in debug mode)
```

### Attivare modalità debug

```bash
# Linux/Mac
export TANALEAGUE_DEBUG=true
python app.py

# Windows
set TANALEAGUE_DEBUG=true
python app.py
```

### Leggere i log

```bash
# Ultimi 50 messaggi
tail -50 tanaleague2/logs/tanaleague.log

# Seguire in tempo reale
tail -f tanaleague2/logs/tanaleague.log

# Cercare errori
grep "ERROR" tanaleague2/logs/tanaleague.log
```

---

## 🧪 Testing

### Cosa sono i test?

Codice che verifica automaticamente che l'applicazione funzioni correttamente.

**Posizione:** `/home/user/TanaLeague/tests/`

### Perché sono importanti?

- **Sicurezza**: Ogni modifica viene verificata
- **Regressioni**: Se rompi qualcosa, lo sai subito
- **Documentazione**: I test mostrano come dovrebbe funzionare il codice

### Struttura file test

```
tests/
├── __init__.py           # File vuoto (necessario per Python)
├── conftest.py           # Configurazione e dati finti per i test
├── test_app.py           # Test delle pagine web
└── test_achievements.py  # Test del sistema achievement
```

### Come eseguire i test

**Tutti i test:**
```bash
cd /home/user/TanaLeague
pytest
```

**Output esempio (tutto OK):**
```
tests/test_app.py::TestPublicPages::test_landing_page_loads PASSED
tests/test_app.py::TestPublicPages::test_classifiche_page_loads PASSED
tests/test_app.py::TestSeasonIdValidation::test_valid_base_format PASSED
==================== 15 passed in 2.34s ====================
```

**Output esempio (errore):**
```
tests/test_app.py::TestPublicPages::test_landing_page_loads FAILED
E       AssertionError: Expected 200, got 500
==================== 1 failed, 14 passed in 2.45s ====================
```

**Comandi utili:**
```bash
pytest -v                      # Output dettagliato
pytest tests/test_app.py       # Solo test specifici
pytest -k "landing"            # Solo test con "landing" nel nome
pytest --cov=tanaleague2       # Mostra quanto codice è testato
```

### Quando eseguire i test

- ✅ Prima di fare push su GitHub
- ✅ Dopo aver modificato codice importante
- ✅ Prima di deployare su PythonAnywhere
- ✅ Quando qualcosa non funziona (per capire cosa è rotto)

---

## 🔄 CI/CD

### Cos'è CI/CD?

**CI** = Continuous Integration: Test automatici ad ogni push
**CD** = Continuous Deployment: Deploy automatico (non ancora attivo)

**Posizione:** `/home/user/TanaLeague/.github/workflows/test.yml`

### Come funziona

```
1. Tu fai push su GitHub
       ↓
2. GitHub legge .github/workflows/test.yml
       ↓
3. GitHub avvia una macchina virtuale Ubuntu
       ↓
4. Installa Python e dipendenze
       ↓
5. Esegue pytest
       ↓
6. Mostra risultato: ✅ o ❌
```

### Dove vedere i risultati

1. Vai su **GitHub** → Il tuo repository
2. Clicca tab **"Actions"** (in alto)
3. Vedi lista esecuzioni:
   - ✅ Verde = Test passati, tutto OK
   - ❌ Rosso = Test falliti, clicca per dettagli

### Quando si attiva automaticamente

- Push su branch: `main`, `master`, `develop`, `feature/*`, `claude/*`
- Pull Request verso `main` o `master`

### Eseguire manualmente

1. GitHub → Actions → "Tests" workflow
2. Click "Run workflow" → "Run workflow"

---

## 📁 Struttura File

### File da caricare su PythonAnywhere

| File locale | Destinazione PythonAnywhere |
|-------------|----------------------------|
| `requirements.txt` | `~/TanaLeague/requirements.txt` |
| `tanaleague2/logger.py` | `~/TanaLeague/tanaleague2/logger.py` |
| `tests/` (cartella) | `~/TanaLeague/tests/` (opzionale, solo per test) |
| `.github/` (cartella) | NON serve su PythonAnywhere (solo GitHub) |

### Struttura completa progetto

```
TanaLeague/
├── requirements.txt              # ⬅️ NUOVO: Dipendenze
├── pytest.ini                    # ⬅️ NUOVO: Config test
│
├── .github/
│   └── workflows/
│       └── test.yml              # ⬅️ NUOVO: CI/CD (solo GitHub)
│
├── tests/                        # ⬅️ NUOVO: Test automatici
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   └── test_achievements.py
│
├── tanaleague2/
│   ├── logger.py                 # ⬅️ NUOVO: Sistema logging
│   ├── logs/                     # ⬅️ NUOVO: Cartella log (creata auto)
│   │   └── tanaleague.log
│   ├── app.py
│   ├── cache.py
│   ├── achievements.py
│   └── ... (altri file)
│
└── docs/
    ├── DEVELOPMENT.md            # ⬅️ NUOVO: Questa guida
    └── ... (altre guide)
```

---

## ⌨️ Comandi Utili

### Cheatsheet rapido

| Cosa vuoi fare | Comando |
|----------------|---------|
| Installare dipendenze | `pip install -r requirements.txt` |
| Eseguire test | `pytest` |
| Test con dettagli | `pytest -v` |
| Test con coverage | `pytest --cov=tanaleague2` |
| Vedere ultimi log | `tail -50 tanaleague2/logs/tanaleague.log` |
| Seguire log live | `tail -f tanaleague2/logs/tanaleague.log` |
| Cercare errori nei log | `grep "ERROR" tanaleague2/logs/tanaleague.log` |
| Attivare debug | `export TANALEAGUE_DEBUG=true` |
| Avviare app locale | `cd tanaleague2 && python app.py` |

### Workflow tipico di sviluppo

```bash
# 1. Fai le tue modifiche al codice
# 2. Testa in locale
pytest

# 3. Se i test passano, committa
git add .
git commit -m "Descrizione modifica"

# 4. Pusha su GitHub
git push

# 5. Controlla che i test passino su GitHub (tab Actions)
# 6. Se tutto OK, aggiorna PythonAnywhere
```

---

## ❓ FAQ

### I test falliscono, cosa faccio?

1. Leggi l'errore: dice quale test è fallito e perché
2. Cerca la riga indicata nel codice
3. Correggi il problema
4. Riesegui `pytest`

### I log non vengono creati

1. Verifica che la cartella `tanaleague2/logs/` esista
2. Se non esiste, creala: `mkdir tanaleague2/logs`
3. Verifica permessi di scrittura

### GitHub Actions mostra errore

1. Vai su GitHub → Actions → Click sull'esecuzione fallita
2. Espandi il job "test"
3. Leggi l'errore nello step che ha fallito
4. Correggi e fai push di nuovo

---

## 💾 Backup Google Sheets

### Cos'è?

Script che scarica tutti i dati dal Google Sheet e li salva in locale come file CSV.

**Posizione:** `/home/user/TanaLeague/tanaleague2/backup_sheets.py`

### Perché è importante?

- **Sicurezza**: Se cancelli qualcosa per sbaglio, hai una copia
- **Storico**: Puoi vedere come erano i dati in passato
- **Indipendenza**: Non dipendi solo da Google

### Come usarlo

**Backup completo (tutti i fogli):**
```bash
cd tanaleague2
python backup_sheets.py
```

**Output:**
```
🔄 BACKUP GOOGLE SHEETS - TanaLeague
📅 Data: 2025-11-23 14:30:00
📁 Output: backups/2025-11-23_14-30-00

📋 Backup fogli...
   ✅ Config: 15 righe
   ✅ Tournaments: 45 righe
   ✅ Results: 1250 righe
   ✅ Players: 52 righe
   ...

✅ BACKUP COMPLETATO
```

**Dove vanno i backup:**
```
tanaleague2/backups/
├── 2025-11-23_14-30-00/
│   ├── backup_info.json
│   ├── Config.csv
│   ├── Results.csv
│   └── ...
├── 2025-11-22_10-00-00/
│   └── ...
```

### Comandi utili

```bash
# Backup completo
python backup_sheets.py

# Backup solo un foglio
python backup_sheets.py --sheet Results

# Backup in cartella specifica
python backup_sheets.py --output /path/to/backups

# Vedere fogli disponibili
python backup_sheets.py --list
```

### Backup automatico (scheduling)

**Su Linux/Mac (crontab):**
```bash
# Apri crontab
crontab -e

# Aggiungi questa riga per backup giornaliero alle 3:00
0 3 * * * cd /path/to/TanaLeague/tanaleague2 && python backup_sheets.py
```

**Su PythonAnywhere:**
1. Vai al tab **Tasks**
2. Aggiungi nuovo task schedulato
3. Comando: `cd ~/TanaLeague/tanaleague2 && python backup_sheets.py`
4. Imposta orario (es. 03:00)

### Ripristino da backup

I file CSV possono essere:
1. Aperti con Excel/Google Sheets
2. Reimportati manualmente se necessario
3. Usati come riferimento per recuperare dati

---

**Ultimo aggiornamento:** Novembre 2025
