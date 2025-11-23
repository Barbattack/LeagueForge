# 🛠️ Guida Sviluppo - TanaLeague

Guida pratica per sviluppatori e manutentori di TanaLeague.

---

## 📋 Indice

- [Setup Ambiente](#-setup-ambiente)
- [Setup Locale Completo](#️-setup-locale-completo-windowsmaclinux)
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

## 🖥️ Setup Locale Completo (Windows/Mac/Linux)

Questa sezione spiega come configurare l'ambiente locale per testare TanaLeague sul tuo PC.

### Prerequisiti

- Python 3.10+ installato
- Git installato
- Accesso a PythonAnywhere (per copiare i file segreti)

### Step 1: Clona il repository

```bash
# Clona il repo
git clone https://github.com/tuousername/TanaLeague.git
cd TanaLeague

# Installa dipendenze
pip install -r requirements.txt
```

### Step 2: Copia i file segreti da PythonAnywhere

Questi file contengono credenziali e NON sono nel repository Git (sono in `.gitignore`).

**Devi copiarli manualmente da PythonAnywhere al tuo PC:**

| File su PythonAnywhere | Copia in locale |
|------------------------|-----------------|
| `~/TanaLeague/tanaleague2/config.py` | `tanaleague2/config.py` |
| `~/TanaLeague/tanaleague2/service_account_credentials.json` | `tanaleague2/service_account_credentials.json` |

**Come copiare da PythonAnywhere:**

1. Vai su PythonAnywhere → **Files**
2. Naviga a `~/TanaLeague/tanaleague2/`
3. Clicca su `config.py` → **Download**
4. Clicca su `service_account_credentials.json` → **Download**
5. Metti i file scaricati nella cartella `tanaleague2/` del tuo PC

### Step 3 (Alternativo): Crea config.py da zero

Se non vuoi copiare il config.py esistente, puoi crearne uno nuovo:

```bash
cd tanaleague2
cp config.example.py config.py
```

Poi modifica `config.py` con i tuoi valori:

```python
# config.py - Modifica questi valori

# 1. SHEET_ID - Lo trovi nell'URL del tuo Google Sheet
# URL: https://docs.google.com/spreadsheets/d/QUESTO_E_LO_SHEET_ID/edit
SHEET_ID = "IL_TUO_SHEET_ID"

# 2. SECRET_KEY - Genera una stringa casuale
# Esegui: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = "la_stringa_generata"

# 3. ADMIN_PASSWORD_HASH - Genera l'hash della password
# Vedi sezione sotto per istruzioni
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:..."
```

### Come generare ADMIN_PASSWORD_HASH

```bash
# Esegui questo comando Python
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('LA_TUA_PASSWORD'))"
```

**Esempio:**
```bash
$ python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('miapassword123'))"
pbkdf2:sha256:600000$abc123...xyz789
```

Copia l'output (inizia con `pbkdf2:`) e incollalo in `config.py` come valore di `ADMIN_PASSWORD_HASH`.

### Step 4: Avvia l'applicazione

```bash
cd tanaleague2
python app.py
```

**Output atteso:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Apri il browser su `http://localhost:5000`

### Step 5: Verifica che tutto funzioni

Testa queste pagine:

| URL | Cosa deve mostrare |
|-----|-------------------|
| `http://localhost:5000/` | Homepage con 3 TCG |
| `http://localhost:5000/classifiche` | Lista stagioni |
| `http://localhost:5000/achievements` | Catalogo achievement |
| `http://localhost:5000/admin/login` | Form login admin |
| `http://localhost:5000/players` | Lista giocatori |

### Troubleshooting

#### Errore: `ModuleNotFoundError: No module named 'xxx'`

```bash
# Reinstalla dipendenze
pip install -r requirements.txt
```

#### Errore: `FileNotFoundError: config.py`

```bash
# Crea config.py dal template
cd tanaleague2
cp config.example.py config.py
# Poi modifica config.py con i tuoi valori
```

#### Errore: `gspread.exceptions.SpreadsheetNotFound`

- Verifica che `SHEET_ID` in config.py sia corretto
- Verifica che il service account abbia accesso al Google Sheet
- Controlla che `service_account_credentials.json` sia nella cartella giusta

#### Errore: `google.auth.exceptions.DefaultCredentialsError`

```bash
# Verifica che il file credentials esista
ls tanaleague2/service_account_credentials.json

# Se non esiste, copialo da PythonAnywhere
```

#### Errore: `Address already in use` (porta 5000 occupata)

```bash
# Usa una porta diversa
python app.py --port 5001
# Oppure: flask run --port 5001
```

#### L'app parte ma le pagine mostrano errori

1. Controlla i log: `tanaleague2/logs/tanaleague.log`
2. Verifica connessione a Google Sheets
3. Verifica che il Google Sheet abbia tutti i fogli necessari

### Checklist Setup Locale

- [ ] Repository clonato
- [ ] `pip install -r requirements.txt` eseguito
- [ ] `config.py` presente in `tanaleague2/`
- [ ] `service_account_credentials.json` presente in `tanaleague2/`
- [ ] `SHEET_ID` configurato correttamente
- [ ] `SECRET_KEY` configurato
- [ ] `ADMIN_PASSWORD_HASH` configurato
- [ ] `python app.py` avvia senza errori
- [ ] Homepage carica su `http://localhost:5000`

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
├── requirements.txt              # Dipendenze Python
├── pytest.ini                    # Config test
├── .gitignore                    # File esclusi da Git
│
├── .github/
│   └── workflows/
│       └── test.yml              # CI/CD (solo GitHub)
│
├── tests/                        # Test automatici
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   └── test_achievements.py
│
├── tanaleague2/
│   ├── app.py                    # App principale (route pubbliche)
│   ├── routes/                   # ⬅️ NUOVO: Blueprint modulari
│   │   ├── __init__.py           #   Registration blueprints
│   │   ├── admin.py              #   Route admin (/admin/*)
│   │   └── achievements.py       #   Route achievement
│   ├── cache.py                  # Cache Google Sheets
│   ├── achievements.py           # Logica unlock achievement
│   ├── config.py                 # ⚠️ NON in Git (segreti)
│   ├── config.example.py         # Template per config.py
│   ├── logger.py                 # Sistema logging
│   ├── logs/                     # Cartella log (creata auto)
│   │   └── tanaleague.log
│   ├── backup_sheets.py          # Script backup Google Sheets
│   └── ... (altri file)
│
└── docs/
    ├── DEVELOPMENT.md            # Questa guida
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
