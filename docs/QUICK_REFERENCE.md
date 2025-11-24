# Quick Reference - TanaLeague

Cheatsheet rapido per le operazioni comuni.

---

## Comandi Frequenti

### Test

```bash
# Esegui tutti i test
pytest

# Test con output dettagliato
pytest -v

# Solo un file specifico
pytest tests/test_app.py

# Solo test con nome specifico
pytest -k "landing"

# Ferma al primo errore
pytest -x

# Coverage report
pytest --cov=tanaleague2
```

### Git

```bash
# Stato corrente
git status

# Pull ultimi cambiamenti
git pull origin main

# Commit e push
git add .
git commit -m "Descrizione cambiamenti"
git push origin main

# Vedere log commit
git log --oneline -10
```

### Avvio Locale

```bash
# Naviga alla cartella
cd tanaleague2

# Avvia app Flask
python app.py

# Apri browser: http://localhost:5000
```

---

## URL Principali

| URL | Descrizione |
|-----|-------------|
| `/` | Homepage |
| `/classifiche` | Lista stagioni |
| `/classifica/<id>` | Classifica stagione |
| `/achievements` | Catalogo achievement |
| `/achievement/<id>` | Dettaglio achievement |
| `/players` | Lista giocatori |
| `/player/<nome>` | Profilo giocatore |
| `/admin/login` | Login admin |
| `/admin/` | Dashboard admin |

---

## File Importanti

### Codice Principale

| File | Scopo |
|------|-------|
| `tanaleague2/app.py` | Applicazione Flask principale |
| `tanaleague2/cache.py` | Gestione cache Google Sheets |
| `tanaleague2/achievements.py` | Logica achievement |
| `tanaleague2/routes/admin.py` | Route admin panel |
| `tanaleague2/routes/achievements.py` | Route achievement |

### Script Import (v2)

| File | Scopo |
|------|-------|
| `tanaleague2/import_base.py` | Funzioni comuni import |
| `tanaleague2/import_onepiece_v2.py` | Import One Piece multi-round |
| `tanaleague2/import_riftbound_v2.py` | Import Riftbound multi-round |
| `tanaleague2/import_pokemon.py` | Import Pokemon TDF |
| `tanaleague2/sheet_utils.py` | Mappature colonne sheets |
| `tanaleague2/player_stats.py` | CRUD Player_Stats |

### Configurazione

| File | Scopo |
|------|-------|
| `tanaleague2/config.py` | Credenziali e settings (NON su Git!) |
| `tanaleague2/config.example.py` | Template config |
| `tanaleague2/service_account_credentials.json` | Credenziali Google (NON su Git!) |
| `requirements.txt` | Dipendenze Python |

### Test

| File | Scopo |
|------|-------|
| `tests/conftest.py` | Fixtures e mock data |
| `tests/test_app.py` | Test route Flask |
| `tests/test_achievements.py` | Test achievement |

---

## Import Tornei (v2)

### One Piece (Multi-Round)

```bash
cd tanaleague2
python import_onepiece_v2.py --rounds R1.csv,R2.csv,R3.csv,R4.csv --classifica ClassificaFinale.csv --season OP12
```

### Riftbound (Multi-Round)

```bash
cd tanaleague2
python import_riftbound_v2.py --rounds R1.csv,R2.csv,R3.csv --season RFB01
```

### Pokemon (TDF)

```bash
cd tanaleague2
python import_pokemon.py --tdf file.tdf --season PKM01
```

### Parametri comuni
- `--test`: Dry run senza scrittura
- `--reimport`: Sovrascrivi torneo esistente

---

## Operazioni Admin

### Login Admin
1. Vai a `/admin/login`
2. Inserisci username e password
3. Sessione valida 30 minuti

### Importare Dati
1. Login admin
2. Dashboard `/admin/`
3. Click pulsante import gioco
4. Attendi completamento

### Refresh Cache Manuale
La cache si aggiorna automaticamente ogni 5 minuti.
Per forzare refresh: riavvia app o usa import admin.

---

## PythonAnywhere

### Struttura Cartelle

```
/home/Pulci/
└── TanaLeague/
    ├── tanaleague2/      # Codice Python
    │   ├── app.py
    │   ├── config.py     # File segreto
    │   ├── routes/       # Blueprint routes
    │   └── templates/
    └── tests/            # Test automatici
```

### Reload Webapp

1. Dashboard PythonAnywhere
2. Tab "Web"
3. Click "Reload" (pulsante verde)

### Vedere Logs

1. Tab "Web"
2. Click su "Error log" o "Server log"
3. Oppure: Files → `tanaleague2/logs/`

### Aggiornare Codice

```bash
# Da console PythonAnywhere
cd ~/TanaLeague
git pull origin main
# Poi reload webapp
```

---

## Generare Credenziali

### SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### ADMIN_PASSWORD_HASH

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('nuova_password'))"
```

---

## Backup

### Backup Google Sheets

```bash
cd tanaleague2
python backup_sheets.py
# File salvati in backups/
```

### Backup Manuale Files

Scarica da PythonAnywhere:
- `tanaleague2/config.py`
- `tanaleague2/service_account_credentials.json`

---

## Troubleshooting Veloce

| Problema | Soluzione |
|----------|-----------|
| App non parte | Verifica `config.py` esiste |
| Google Sheets errore | Verifica credenziali service account |
| Import fallisce | Controlla nome worksheet |
| 500 error | Guarda error log su PythonAnywhere |
| Test falliscono | `pip install -r requirements.txt` |
| Cache vecchia | Reload webapp |

---

## Links Utili

- **Repository**: GitHub TanaLeague
- **PythonAnywhere**: pythonanywhere.com
- **Google Sheet**: Link nel config.py (SHEET_ID)
- **pytest docs**: docs.pytest.org
- **Flask docs**: flask.palletsprojects.com

---

**Ultimo aggiornamento:** Novembre 2025
