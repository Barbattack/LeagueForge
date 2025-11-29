# 🚀 Guida Migrazione Server

Guida passo-passo per migrare LeagueForge da PythonAnywhere a un nuovo server.

---

## 📋 Checklist Pre-Migrazione

Prima di iniziare, assicurati di avere:

- [ ] Accesso al nuovo server (SSH o pannello web)
- [ ] Python 3.10+ installato sul nuovo server
- [ ] Backup completo dei dati (vedi sezione Backup)

---

## 📦 File da Copiare

### File Essenziali (OBBLIGATORI)

| File/Cartella | Descrizione | Note |
|---------------|-------------|------|
| `leagueforge2/` | Tutto il codice Python | Cartella principale |
| `leagueforge2/config.py` | Configurazione con segreti | **NON è su GitHub!** |
| `leagueforge2/service_account_credentials.json` | Credenziali Google | **NON è su GitHub!** |
| `requirements.txt` | Dipendenze Python | Nella root |

### File Opzionali

| File/Cartella | Descrizione | Note |
|---------------|-------------|------|
| `tests/` | Test automatici | Solo se vuoi eseguire test |
| `docs/` | Documentazione | Per riferimento |
| `.github/` | CI/CD | Solo se usi GitHub Actions |

---

## 🔄 Step-by-Step Migrazione

### Step 1: Backup Dati

```bash
# Su PythonAnywhere, fai backup del Google Sheet
cd ~/LeagueForge/leagueforge2
python backup_sheets.py

# Scarica la cartella backups/
```

### Step 2: Scarica File Segreti

Da PythonAnywhere → Files → `~/LeagueForge/leagueforge2/`:
1. Scarica `config.py`
2. Scarica `service_account_credentials.json`

**Salva questi file in un posto sicuro!**

### Step 3: Prepara Nuovo Server

```bash
# 1. Crea cartella progetto
mkdir -p ~/LeagueForge
cd ~/LeagueForge

# 2. Clona repository (se disponibile)
git clone https://github.com/tuousername/LeagueForge.git .

# OPPURE: carica manualmente i file
```

### Step 4: Carica File Segreti

```bash
# Carica i file segreti nella cartella leagueforge2/
# - config.py
# - service_account_credentials.json
```

### Step 5: Installa Dipendenze

```bash
# Con pip
pip install -r requirements.txt

# OPPURE con pip user (se non hai permessi root)
pip install --user -r requirements.txt

# OPPURE con virtual environment (consigliato)
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Step 6: Verifica Configurazione

```bash
cd leagueforge2

# Verifica che config.py esista
ls -la config.py

# Verifica che credentials esistano
ls -la service_account_credentials.json

# Test connessione Google Sheets
python -c "from cache import cache; print(cache.connect_sheet())"
```

### Step 7: Test Locale

```bash
cd leagueforge2
python app.py

# Apri browser su http://localhost:5000
# Verifica che tutte le pagine funzionino
```

### Step 8: Configura Web Server

#### Opzione A: Gunicorn (consigliato)

```bash
pip install gunicorn

# Avvia con gunicorn
cd leagueforge2
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Opzione B: WSGI (Apache/Nginx)

Crea file `wsgi.py`:
```python
import sys
sys.path.insert(0, '/path/to/LeagueForge/leagueforge2')

from app import app as application
```

#### Opzione C: Systemd Service

Crea `/etc/systemd/system/leagueforge.service`:
```ini
[Unit]
Description=LeagueForge Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/LeagueForge/leagueforge2
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable leagueforge
sudo systemctl start leagueforge
```

### Step 9: Configura Reverse Proxy (Opzionale)

#### Nginx

```nginx
server {
    listen 80;
    server_name tuodominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 10: Verifica Finale

Testa queste URL sul nuovo server:

| URL | Deve Funzionare |
|-----|-----------------|
| `/` | Homepage |
| `/classifiche` | Lista stagioni |
| `/achievements` | Catalogo achievement |
| `/admin/login` | Form login admin |
| `/players` | Lista giocatori |

---

## 🔧 Configurazione config.py

Se devi ricreare `config.py`:

```python
import os

# Google Sheets
SHEET_ID = "IL_TUO_GOOGLE_SHEET_ID"
CREDENTIALS_FILE = "service_account_credentials.json"

# Flask
SECRET_KEY = "genera-stringa-casuale-32-caratteri"
DEBUG = False  # True solo in sviluppo

# Admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:..."  # Genera con werkzeug

# Cache
CACHE_REFRESH_MINUTES = 5
CACHE_FILE = "cache_data.json"

# Session
SESSION_TIMEOUT = 30  # minuti
```

### Generare SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Generare ADMIN_PASSWORD_HASH

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('tua_password'))"
```

---

## 🚨 Troubleshooting Migrazione

### Errore: ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Errore: Google Sheets non trovato

1. Verifica `SHEET_ID` in config.py
2. Verifica che service account abbia accesso allo Sheet
3. Verifica path `service_account_credentials.json`

### Errore: Permission denied

```bash
# Verifica permessi cartella
chmod -R 755 ~/LeagueForge
chmod 600 leagueforge2/config.py
chmod 600 leagueforge2/service_account_credentials.json
```

### Errore: Port already in use

```bash
# Usa porta diversa
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

---

## 📝 Note Importanti

1. **Google Sheets**: Non serve migrare! I dati sono su Google Cloud
2. **Service Account**: Le credenziali funzionano ovunque
3. **Cache**: Si ricrea automaticamente al primo avvio
4. **Logs**: Si creano automaticamente in `leagueforge2/logs/`

---

## 🔙 Rollback

Se qualcosa va storto, puoi sempre tornare a PythonAnywhere:
1. Il vecchio server è ancora funzionante
2. I dati sono su Google Sheets (non perdi nulla)
3. Basta aggiornare il DNS per puntare al vecchio server

---

**Ultimo aggiornamento:** Novembre 2025
