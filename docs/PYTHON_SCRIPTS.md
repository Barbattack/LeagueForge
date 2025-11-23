# Script Python - TanaLeague

Guida completa a tutti gli script Python eseguibili da terminale.

---

## Indice

- [Panoramica Script](#-panoramica-script)
- [Backup Database](#-backup-database)
- [Setup Achievement](#-setup-achievement)
- [Import Tornei](#-import-tornei)
- [Avvio Applicazione](#-avvio-applicazione)
- [Utility Python](#-utility-python)

---

## Panoramica Script

| Script | Scopo | Comando |
|--------|-------|---------|
| `app.py` | Avvia webapp Flask | `python app.py` |
| `backup_sheets.py` | Backup Google Sheets → CSV | `python backup_sheets.py` |
| `setup_achievements.py` | Crea fogli achievement | `python setup_achievements.py` |
| `import_onepiece.py` | Import tornei One Piece | `python import_onepiece.py --csv file.csv --season OP12` |
| `import_pokemon.py` | Import tornei Pokemon | `python import_pokemon.py --tdf file.tdf --season PKM01` |
| `import_riftbound.py` | Import tornei Riftbound | `python import_riftbound.py --csv file.csv --season RFB01` |

**Posizione**: Tutti gli script sono in `tanaleague2/`

---

## Backup Database

### backup_sheets.py

Crea backup completo del database Google Sheets in formato CSV.

### Comandi

```bash
cd tanaleague2

# Backup completo (tutti i fogli)
python backup_sheets.py

# Backup foglio specifico
python backup_sheets.py --sheet Results

# Backup in cartella specifica
python backup_sheets.py --output /path/to/backups
```

### Parametri

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `--sheet` | Nome foglio specifico da backuppare | Tutti i fogli |
| `--output` | Cartella destinazione backup | `backups/` |

### Output

```
backups/
└── 2025-11-23_14-30-00/
    ├── backup_info.json      # Metadati backup (data, fogli, righe)
    ├── Config.csv
    ├── Tournaments.csv
    ├── Results.csv
    ├── Players.csv
    ├── Achievement_Definitions.csv
    ├── Player_Achievements.csv
    ├── Seasonal_Standings_PROV.csv
    └── ... (altri fogli)
```

### Esempio Output Console

```
=== BACKUP GOOGLE SHEETS ===
Timestamp: 2025-11-23 14:30:00

Connessione a Google Sheets...
Sheet ID: 19ZF35DTmgZG8v...

Backup fogli:
  [1/8] Config... 15 righe
  [2/8] Tournaments... 45 righe
  [3/8] Results... 892 righe
  [4/8] Players... 67 righe
  [5/8] Achievement_Definitions... 42 righe
  [6/8] Player_Achievements... 156 righe
  [7/8] Seasonal_Standings_PROV... 234 righe
  [8/8] Vouchers... 312 righe

Backup completato!
Cartella: backups/2025-11-23_14-30-00/
Totale: 8 fogli, 1763 righe
```

### Scheduling Automatico

**Linux/Mac (crontab):**
```bash
# Backup giornaliero alle 3:00
crontab -e
0 3 * * * cd /path/to/TanaLeague/tanaleague2 && python backup_sheets.py
```

**PythonAnywhere:**
1. Vai su Dashboard → Tab "Tasks"
2. "Scheduled Tasks" → "Add new scheduled task"
3. Command: `cd ~/TanaLeague/tanaleague2 && python backup_sheets.py`
4. Time: 03:00 (o orario preferito)

---

## Setup Achievement

### setup_achievements.py

Crea i fogli necessari per il sistema achievement nel Google Sheet.

### Comando

```bash
cd tanaleague2
python setup_achievements.py
```

### Cosa Fa

1. Crea foglio `Achievement_Definitions` con 40+ achievement
2. Crea foglio `Player_Achievements` (vuoto, si popola con import)
3. Chiede conferma se i fogli esistono già

### Quando Usarlo

- **Prima volta**: Setup iniziale sistema achievement
- **Reset**: Ricreare definizioni achievement (richiede conferma)
- **Troubleshooting**: Se achievement non funzionano

### Sicurezza

- NON modifica fogli esistenti (Results, Players, etc.)
- Chiede conferma prima di sovrascrivere
- Crea solo i 2 fogli specifici per achievement

### Output Esempio

```
=== SETUP ACHIEVEMENT SYSTEM ===

Connessione a Google Sheets...

Controllo fogli esistenti...
  Achievement_Definitions: NON ESISTE
  Player_Achievements: NON ESISTE

Creazione Achievement_Definitions...
  Inseriti 42 achievement in 7 categorie

Creazione Player_Achievements...
  Foglio vuoto creato (si popola con import)

Setup completato!
```

---

## Import Tornei

Gli script di import sono documentati in dettaglio in [IMPORT_GUIDE.md](IMPORT_GUIDE.md).

### Riferimento Rapido

```bash
cd tanaleague2

# One Piece (CSV)
python import_onepiece.py --csv file.csv --season OP12
python import_onepiece.py --csv file.csv --season OP12 --test      # Dry run
python import_onepiece.py --csv file.csv --season OP12 --reimport  # Sovrascrivi

# Pokemon (TDF/XML)
python import_pokemon.py --tdf file.tdf --season PKM-FS25
python import_pokemon.py --tdf file.tdf --season PKM-FS25 --test

# Riftbound (CSV Multi-Round)
python import_riftbound.py --csv R1.csv,R2.csv,R3.csv --season RFB01
python import_riftbound.py --csv R1.csv --season RFB01 --test
```

### Parametri Comuni

| Parametro | Descrizione |
|-----------|-------------|
| `--test` | Dry run: verifica senza scrivere |
| `--reimport` | Permette sovrascrittura torneo esistente |

---

## Avvio Applicazione

### app.py

Avvia il server Flask per la webapp.

### Comando

```bash
cd tanaleague2
python app.py
```

### Output

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Opzioni Avanzate

```bash
# Porta diversa (se 5000 occupata)
flask run --port 5001

# Accessibile da rete locale
flask run --host 0.0.0.0

# Produzione con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Note

- **Sviluppo**: usa `python app.py` (debug mode on)
- **Produzione**: usa gunicorn o wsgi (debug mode off)
- **PythonAnywhere**: non serve avviare manualmente, usa il tab Web

---

## Utility Python

### Comandi Python One-Liner

Comandi utili eseguibili direttamente da terminale.

#### Generare SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Output esempio:
```
a3b7c9d1e5f2g8h4i6j0k2l8m4n6o1p3q5r7s9t1u3v5w7x9y1z3
```

#### Generare ADMIN_PASSWORD_HASH

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('LA_TUA_PASSWORD'))"
```

Output esempio:
```
pbkdf2:sha256:600000$abc123def456$789xyz...
```

#### Test Connessione Google Sheets

```bash
cd tanaleague2
python -c "from cache import cache; print('Connesso!' if cache.connect_sheet() else 'Errore')"
```

#### Verificare Versione Python

```bash
python --version
# Output: Python 3.11.4
```

#### Verificare Dipendenze Installate

```bash
pip list | grep -E "flask|gspread|pytest"
```

#### Test Import Moduli

```bash
cd tanaleague2
python -c "import app; print('App OK')"
python -c "import cache; print('Cache OK')"
python -c "import achievements; print('Achievements OK')"
```

---

## Troubleshooting Script

### Errore: ModuleNotFoundError

```bash
# Reinstalla dipendenze
pip install -r requirements.txt
```

### Errore: FileNotFoundError config.py

```bash
cd tanaleague2
cp config.example.py config.py
# Poi modifica config.py con i tuoi valori
```

### Errore: gspread.exceptions.SpreadsheetNotFound

1. Verifica SHEET_ID in config.py
2. Verifica accesso service account al Google Sheet
3. Controlla che credentials.json sia presente

### Errore: Permission Denied

```bash
chmod +x script.py
python script.py
```

### Script non trova moduli locali

```bash
# Assicurati di essere nella cartella giusta
cd tanaleague2
python script.py

# Oppure aggiungi al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Riepilogo Comandi

### Uso Quotidiano

```bash
cd tanaleague2

# Avvia app
python app.py

# Import torneo
python import_onepiece.py --csv file.csv --season OP12

# Backup
python backup_sheets.py
```

### Setup Iniziale

```bash
cd tanaleague2

# 1. Copia config
cp config.example.py config.py

# 2. Setup achievement (se non esistono)
python setup_achievements.py

# 3. Test connessione
python -c "from cache import cache; print(cache.connect_sheet())"

# 4. Avvia
python app.py
```

### Manutenzione

```bash
cd tanaleague2

# Backup manuale
python backup_sheets.py

# Aggiorna dipendenze
pip install -r requirements.txt --upgrade
```

---

**Ultimo aggiornamento:** Novembre 2025
