# Guida Setup Nuovo Negozio

Guida completa per configurare LeagueForge da zero per il tuo negozio.

**Tempo stimato: 30-45 minuti**

---

## Indice

1. [Prerequisiti](#1-prerequisiti)
2. [Creare Google Cloud Project](#2-creare-google-cloud-project)
3. [Creare Service Account](#3-creare-service-account)
4. [Creare Google Sheet](#4-creare-google-sheet)
5. [Scaricare LeagueForge](#5-scaricare-leagueforge)
6. [Configurazione](#6-configurazione)
7. [Inizializzazione Database](#7-inizializzazione-database)
8. [Test con Dati Demo](#8-test-con-dati-demo)
9. [Deploy su Hosting](#9-deploy-su-hosting)
10. [Primo Torneo Reale](#10-primo-torneo-reale)

---

## 1. Prerequisiti

Prima di iniziare, assicurati di avere:

- [ ] Account Google (per Google Sheets e Cloud)
- [ ] Python 3.8+ installato sul tuo PC
- [ ] Connessione internet

### Verifica Python

```bash
python --version
# Deve mostrare Python 3.8 o superiore
```

Se non hai Python, scaricalo da [python.org](https://www.python.org/downloads/)

---

## 2. Creare Google Cloud Project

Il Service Account permette all'app di accedere al Google Sheet.

### Step 2.1: Vai su Google Cloud Console

1. Apri [console.cloud.google.com](https://console.cloud.google.com/)
2. Accedi con il tuo account Google

### Step 2.2: Crea Nuovo Progetto

1. Click su **"Select a project"** (in alto)
2. Click **"New Project"**
3. Nome progetto: `LeagueForge` (o nome del tuo negozio)
4. Click **"Create"**
5. Attendi creazione (30 secondi)

### Step 2.3: Abilita Google Sheets API

1. Nel menu laterale: **APIs & Services** → **Library**
2. Cerca "Google Sheets API"
3. Click sulla voce **Google Sheets API**
4. Click **"Enable"**

### Step 2.4: Abilita Google Drive API

1. Torna su **APIs & Services** → **Library**
2. Cerca "Google Drive API"
3. Click sulla voce **Google Drive API**
4. Click **"Enable"**

---

## 3. Creare Service Account

### Step 3.1: Crea Service Account

1. Menu laterale: **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"**
3. Seleziona **"Service account"**
4. Nome: `leagueforge-bot` (o simile)
5. Click **"Create and Continue"**
6. Skip ruoli (click "Continue")
7. Click **"Done"**

### Step 3.2: Scarica Chiave JSON

1. Click sul Service Account appena creato
2. Tab **"Keys"**
3. Click **"Add Key"** → **"Create new key"**
4. Seleziona **JSON**
5. Click **"Create"**
6. **SALVA il file** (si scarica automaticamente)
7. Rinomina il file in `service_account_credentials.json`

**IMPORTANTE**: Questo file contiene credenziali sensibili. NON condividerlo mai!

### Step 3.3: Copia Email Service Account

Dalla pagina del Service Account, copia l'email tipo:
```
leagueforge-bot@tuoprogetto.iam.gserviceaccount.com
```

Ti servirà nel prossimo step.

---

## 4. Creare Google Sheet

### Step 4.1: Crea Nuovo Google Sheet

1. Vai su [sheets.google.com](https://sheets.google.com/)
2. Click **"+ Blank"** (foglio vuoto)
3. Rinomina: **"LeagueForge Database"** (o nome preferito)

### Step 4.2: Condividi con Service Account

1. Click **"Share"** (in alto a destra)
2. Incolla l'email del Service Account (copiata prima)
3. Ruolo: **Editor**
4. Deseleziona "Notify people"
5. Click **"Share"**

### Step 4.3: Copia SHEET_ID

Dall'URL del Google Sheet:
```
https://docs.google.com/spreadsheets/d/ABC123XYZ.../edit
                                       ^^^^^^^^^^^
                                       Questo è lo SHEET_ID
```

Copialo, ti servirà nella configurazione.

---

## 5. Scaricare LeagueForge

### Opzione A: Con Git (consigliato)

```bash
git clone https://github.com/TUOUSER/LeagueForge.git
cd LeagueForge
```

### Opzione B: Download ZIP

1. Vai su GitHub → Repository LeagueForge
2. Click **"Code"** → **"Download ZIP"**
3. Estrai lo ZIP
4. Apri la cartella estratta

### Step 5.1: Installa Dipendenze

```bash
cd LeagueForge
pip install -r requirements.txt
```

### Step 5.2: Copia File Credenziali

Copia il file `service_account_credentials.json` nella cartella `leagueforge2/`:

```
LeagueForge/
└── leagueforge2/
    ├── app.py
    ├── service_account_credentials.json  ← QUI
    └── ...
```

---

## 6. Configurazione

### Metodo Facile: Setup Wizard

```bash
cd leagueforge2
python setup_wizard.py
```

Il wizard ti chiederà:
- Nome del tuo negozio
- SHEET_ID (copiato prima)
- Path credenziali (default: service_account_credentials.json)
- Username e password admin

### Metodo Manuale

```bash
cp config.example.py config.py
```

Poi modifica `config.py`:

```python
STORE_NAME = "Nome Tuo Negozio"
SHEET_ID = "IL_TUO_SHEET_ID"
CREDENTIALS_FILE = "service_account_credentials.json"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "..."  # Genera con comando sotto
SECRET_KEY = "..."  # Genera con comando sotto
```

**Genera SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Genera ADMIN_PASSWORD_HASH:**
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('TUA_PASSWORD'))"
```

---

## 7. Inizializzazione Database

Questo crea tutti i fogli necessari nel Google Sheet:

```bash
cd leagueforge2
python init_database.py
```

Output atteso:
```
🗄️  LEAGUEFORGE - DATABASE INITIALIZATION

📋 Creazione fogli...
  ✅ Config creato
  ✅ Tournaments creato
  ✅ Results creato
  ✅ Players creato
  ...

🎉 INIZIALIZZAZIONE COMPLETATA!
```

### Verifica Setup

```bash
python check_setup.py
```

Deve mostrare tutti `[OK]`:
```
📦 Verifica dipendenze Python...
  [OK] Flask installato
  [OK] gspread installato
  ...

⚙️  Verifica configurazione...
  [OK] config.py trovato
  [OK] SHEET_ID configurato
  ...

✅ SETUP COMPLETO!
```

---

## 8. Test con Dati Demo

Per vedere l'app in azione prima di usarla sul serio:

```bash
python load_demo_data.py
```

Questo carica:
- 2 tornei fittizi
- 8 giocatori demo
- Alcuni achievement

### Avvia l'App

```bash
python app.py
```

Apri nel browser: **http://localhost:5000**

Dovresti vedere:
- Homepage con statistiche
- Classifiche con giocatori demo
- Profili giocatori funzionanti

### Rimuovere Dati Demo

Quando sei pronto per usare dati reali:
1. Apri il Google Sheet
2. Cerca righe contenenti "DEMO"
3. Eliminale

---

## 9. Deploy su Hosting

### Opzione A: PythonAnywhere (Gratuito)

**Consigliato per iniziare!**

1. Registrati su [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Vai su **Web** → **Add a new web app**
3. Scegli **Flask** e **Python 3.10**
4. Carica i file tramite tab **Files**
5. Configura il path WSGI
6. Reload webapp

Vedi [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) per dettagli.

### Opzione B: VPS (Avanzato)

Per un server dedicato (DigitalOcean, Linode, etc.):

```bash
# Installa dipendenze
pip install gunicorn

# Avvia con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Configura nginx come reverse proxy.

### Opzione C: Heroku

1. Crea `Procfile`:
   ```
   web: gunicorn app:app
   ```
2. Deploy con git push

---

## 10. Primo Torneo Reale

### Prepara la Stagione

1. Apri Google Sheet → foglio **Config**
2. Modifica/aggiungi la tua stagione:
   ```
   Season_ID | TCG      | Name           | Status | Start_Date | End_Date
   OP01      | onepiece | Stagione 1     | ACTIVE | 2025-01-01 | 2025-06-30
   ```

### Importa Primo Torneo

```bash
cd leagueforge2

# One Piece (da CSV)
python import_onepiece.py --csv risultati.csv --season OP01

# Pokemon (da TDF)
python import_pokemon.py --tdf torneo.tdf --season PKM01

# Riftbound (da CSV)
python import_riftbound.py --csv R1.csv,R2.csv,R3.csv --season RFB01
```

### Verifica

1. Apri l'app nel browser
2. Vai su **Classifiche**
3. Verifica che il torneo sia visibile
4. Controlla i profili giocatori

---

## Checklist Finale

- [ ] Google Cloud Project creato
- [ ] Service Account con chiave JSON
- [ ] Google Sheet creato e condiviso
- [ ] LeagueForge scaricato
- [ ] config.py configurato
- [ ] Database inizializzato (init_database.py)
- [ ] check_setup.py tutto OK
- [ ] App funzionante in locale
- [ ] Deploy su hosting (opzionale)
- [ ] Primo torneo importato

---

## Troubleshooting

### "config.py non trovato"

```bash
python setup_wizard.py
# Oppure
cp config.example.py config.py
```

### "Errore connessione Google Sheets"

1. Verifica che SHEET_ID sia corretto
2. Verifica che il file credenziali esista
3. Verifica che il Service Account abbia accesso al Google Sheet (condiviso come Editor)

### "Foglio X non trovato"

```bash
python init_database.py
```

### "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### L'app non si avvia

```bash
python check_setup.py
```

Leggi gli errori e risolvi uno alla volta.

---

## Supporto

- **Documentazione**: Cartella `docs/`
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Buon divertimento con LeagueForge!** 🎮🏆
