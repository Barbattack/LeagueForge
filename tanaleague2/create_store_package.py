#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TanaLeague - Store Package Creator (Franchise Tool)
====================================================

Script per creare pacchetti pronti all'uso per nuovi negozi.

PREREQUISITI:
1. config.py configurato con le TUE credenziali master
2. Il tuo Service Account deve poter creare Google Sheets

UTILIZZO:
    python create_store_package.py

COSA FA:
1. Chiede nome negozio e email
2. Crea nuovo Google Sheet per il negozio
3. Inizializza tutti i fogli necessari
4. Condivide lo Sheet con l'email del negozio
5. Genera pacchetto ZIP pre-configurato
6. Il negozio deve solo estrarre e fare doppio-click!

OUTPUT:
    packages/TanaLeague_NomeNegozio.zip
"""

import os
import sys
import shutil
import secrets
import zipfile
from pathlib import Path
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from werkzeug.security import generate_password_hash
except ImportError:
    print("❌ Errore: installa dipendenze con 'pip install gspread google-auth werkzeug'")
    sys.exit(1)

# Importa configurazione master
try:
    from config import CREDENTIALS_FILE
except ImportError:
    print("❌ Errore: config.py non trovato!")
    print("   Questo script richiede le TUE credenziali master.")
    sys.exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Cartella output
PACKAGES_DIR = Path(__file__).parent / "packages"


def get_google_client():
    """Ottiene client Google autenticato."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def create_store_sheet(client, store_name: str, store_email: str) -> str:
    """
    Crea un nuovo Google Sheet per il negozio.

    Returns:
        SHEET_ID del nuovo foglio
    """
    sheet_title = f"TanaLeague - {store_name}"

    print(f"\n📊 Creazione Google Sheet: {sheet_title}")

    # Crea nuovo spreadsheet
    spreadsheet = client.create(sheet_title)
    sheet_id = spreadsheet.id

    print(f"   ✅ Creato! ID: {sheet_id[:20]}...")

    # Condividi con il service account (già fatto automaticamente)

    # Condividi con l'email del negozio
    if store_email:
        try:
            spreadsheet.share(store_email, perm_type='user', role='writer')
            print(f"   ✅ Condiviso con: {store_email}")
        except Exception as e:
            print(f"   ⚠️  Impossibile condividere con {store_email}: {e}")
            print(f"      Condividi manualmente dopo.")

    return sheet_id


def initialize_store_sheets(client, sheet_id: str):
    """Inizializza tutti i fogli nel nuovo Google Sheet."""
    from init_database import SHEETS_STRUCTURE, get_achievement_data

    print(f"\n📋 Inizializzazione fogli...")

    spreadsheet = client.open_by_key(sheet_id)

    # Rinomina Sheet1 in Config
    first_sheet = spreadsheet.sheet1
    first_sheet.update_title("Config")

    for name, config in SHEETS_STRUCTURE.items():
        if name == "Config":
            ws = first_sheet
        else:
            ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(config["headers"]) + 2)

        # Scrivi headers
        ws.update(values=[config["headers"]], range_name="A1")
        ws.format("A1:Z1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

        # Popola dati speciali
        if config.get("special") == "achievements":
            achievements = get_achievement_data()
            if achievements:
                ws.update(values=achievements, range_name="A2")

        elif config.get("sample_data"):
            ws.update(values=config["sample_data"], range_name="A2")

        print(f"   ✅ {name}")

    print(f"   🎉 Tutti i fogli creati!")


def generate_config_file(store_name: str, sheet_id: str, admin_password: str) -> str:
    """Genera contenuto config.py per il negozio."""

    password_hash = generate_password_hash(admin_password)
    secret_key = secrets.token_hex(32)

    return f'''# -*- coding: utf-8 -*-
"""
TanaLeague - Configurazione {store_name}
=========================================
Generato automaticamente - NON modificare SHEET_ID o CREDENTIALS_FILE!
"""

import os

# ==============================================================================
# PERSONALIZZAZIONE NEGOZIO
# ==============================================================================
STORE_NAME = "{store_name}"
STORE_LOGO = "static/logo.png"
STORE_TAGLINE = "Sistema di gestione classifiche TCG"

STORE_PRIMARY_COLOR = "#1a73e8"
STORE_SECONDARY_COLOR = "#34a853"

STORE_INSTAGRAM = ""
STORE_WHATSAPP = ""
STORE_WEBSITE = ""

# ==============================================================================
# GOOGLE SHEETS - NON MODIFICARE!
# ==============================================================================
SHEET_ID = "{sheet_id}"
CREDENTIALS_FILE = "credentials.json"

# ==============================================================================
# ADMIN LOGIN
# ==============================================================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "{password_hash}"
SESSION_TIMEOUT = 30

# ==============================================================================
# CACHE & APP SETTINGS
# ==============================================================================
CACHE_REFRESH_MINUTES = 5
CACHE_FILE = "cache_data.json"
SECRET_KEY = "{secret_key}"
DEBUG = False

# ==============================================================================
# TCG SETTINGS
# ==============================================================================
ENABLE_ONEPIECE = True
ENABLE_POKEMON = True
ENABLE_RIFTBOUND = True
'''


def create_package(store_name: str, sheet_id: str, admin_password: str):
    """Crea il pacchetto ZIP per il negozio."""

    # Crea cartella packages se non esiste
    PACKAGES_DIR.mkdir(exist_ok=True)

    # Nome file sicuro
    safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in store_name)
    safe_name = safe_name.replace(" ", "_")

    package_name = f"TanaLeague_{safe_name}"
    package_dir = PACKAGES_DIR / package_name
    zip_path = PACKAGES_DIR / f"{package_name}.zip"

    print(f"\n📦 Creazione pacchetto: {package_name}.zip")

    # Rimuovi cartella temporanea se esiste
    if package_dir.exists():
        shutil.rmtree(package_dir)

    # Crea struttura cartelle
    tanaleague_dir = package_dir / "tanaleague2"
    tanaleague_dir.mkdir(parents=True)

    # Copia file essenziali
    source_dir = Path(__file__).parent

    files_to_copy = [
        "app.py",
        "cache.py",
        "achievements.py",
        "auth.py",
        "logger.py",
        "stats_builder.py",
        "stats_cache.py",
        "import_onepiece.py",
        "import_pokemon.py",
        "import_riftbound.py",
        "import_validator.py",
        "backup_sheets.py",
        "api_utils.py",
        "wsgi_config.py",
        "requirements.txt",
    ]

    for f in files_to_copy:
        src = source_dir / f
        if src.exists():
            shutil.copy(src, tanaleague_dir / f)

    # Copia requirements.txt dalla root se esiste
    root_req = source_dir.parent / "requirements.txt"
    if root_req.exists():
        shutil.copy(root_req, tanaleague_dir / "requirements.txt")

    # Copia cartelle
    for folder in ["routes", "templates", "static"]:
        src_folder = source_dir / folder
        if src_folder.exists():
            shutil.copytree(src_folder, tanaleague_dir / folder)

    # Genera config.py
    config_content = generate_config_file(store_name, sheet_id, admin_password)
    (tanaleague_dir / "config.py").write_text(config_content, encoding='utf-8')

    # Copia credenziali (rinominate)
    creds_src = Path(CREDENTIALS_FILE)
    if not creds_src.is_absolute():
        creds_src = source_dir / CREDENTIALS_FILE
    if creds_src.exists():
        shutil.copy(creds_src, tanaleague_dir / "credentials.json")
    else:
        print(f"   ⚠️  File credenziali non trovato: {CREDENTIALS_FILE}")
        print(f"      Dovrai copiarlo manualmente come 'credentials.json'")

    # Crea install.bat
    install_bat = '''@echo off
chcp 65001 >nul
echo ========================================
echo    TanaLeague - Installazione
echo ========================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato!
    echo.
    echo Scarica Python da: https://www.python.org/downloads/
    echo Assicurati di selezionare "Add Python to PATH" durante l'installazione!
    echo.
    pause
    exit /b 1
)

echo [OK] Python trovato
echo.
echo Installazione dipendenze...
cd tanaleague2
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo    Installazione completata!
echo ========================================
echo.
echo Per avviare TanaLeague:
echo   1. Apri questa cartella
echo   2. Doppio click su "avvia.bat"
echo.
echo Oppure da terminale:
echo   cd tanaleague2
echo   python app.py
echo.
pause
'''
    (package_dir / "install.bat").write_text(install_bat, encoding='utf-8')

    # Crea avvia.bat
    avvia_bat = '''@echo off
chcp 65001 >nul
cd tanaleague2
echo Avvio TanaLeague...
echo.
echo Apri nel browser: http://localhost:5000
echo.
echo Premi CTRL+C per chiudere
echo.
python app.py
pause
'''
    (package_dir / "avvia.bat").write_text(avvia_bat, encoding='utf-8')

    # Crea LEGGIMI.txt
    leggimi = f'''========================================
   TanaLeague - {store_name}
========================================

INSTALLAZIONE (una volta sola):
1. Estrai questo ZIP in una cartella
2. Doppio click su "install.bat"
3. Attendi che finisca

AVVIO QUOTIDIANO:
1. Doppio click su "avvia.bat"
2. Apri nel browser: http://localhost:5000
3. Per chiudere: premi CTRL+C nel terminale

ACCESSO ADMIN:
- URL: http://localhost:5000/admin/login
- Username: admin
- Password: {admin_password}

IMPORTARE TORNEI:
1. Accedi come admin
2. Clicca su "Import" per il TCG desiderato
3. Seleziona il file (CSV o TDF)
4. Attendi completamento

SUPPORTO:
- Documentazione nella cartella docs/
- Per problemi contatta chi ti ha fornito questo pacchetto

========================================
Buon divertimento con TanaLeague!
========================================
'''
    (package_dir / "LEGGIMI.txt").write_text(leggimi, encoding='utf-8')

    # Crea ZIP
    print(f"   📁 Compressione...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, arcname)

    # Pulisci cartella temporanea
    shutil.rmtree(package_dir)

    print(f"   ✅ Pacchetto creato: {zip_path}")

    return zip_path


def main():
    print("=" * 60)
    print("🏪 TANALEAGUE - STORE PACKAGE CREATOR")
    print("=" * 60)
    print()
    print("Questo script crea un pacchetto pronto all'uso per un nuovo negozio.")
    print()

    # Input dati negozio
    store_name = input("Nome del negozio: ").strip()
    if not store_name:
        print("❌ Nome negozio obbligatorio!")
        return

    store_email = input("Email del negozio (per condividere Google Sheet): ").strip()

    admin_password = input("Password admin per il negozio [default: tanaleague123]: ").strip()
    if not admin_password:
        admin_password = "tanaleague123"

    print()
    print("─" * 60)
    print("📋 RIEPILOGO")
    print("─" * 60)
    print(f"  Nome negozio:    {store_name}")
    print(f"  Email:           {store_email or '(nessuna)'}")
    print(f"  Password admin:  {admin_password}")
    print()

    resp = input("Procedere? (y/n): ").strip().lower()
    if resp != 'y':
        print("❌ Operazione annullata.")
        return

    # Connetti a Google
    print("\n🔗 Connessione a Google...")
    try:
        client = get_google_client()
        print("   ✅ Connesso!")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return

    # Crea Google Sheet
    try:
        sheet_id = create_store_sheet(client, store_name, store_email)
    except Exception as e:
        print(f"❌ Errore creazione Sheet: {e}")
        return

    # Inizializza fogli
    try:
        initialize_store_sheets(client, sheet_id)
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return

    # Crea pacchetto
    try:
        zip_path = create_package(store_name, sheet_id, admin_password)
    except Exception as e:
        print(f"❌ Errore creazione pacchetto: {e}")
        return

    # Riepilogo finale
    print()
    print("=" * 60)
    print("🎉 PACCHETTO CREATO CON SUCCESSO!")
    print("=" * 60)
    print()
    print(f"📦 File: {zip_path}")
    print()
    print("📧 Invia questo file al negozio con le istruzioni:")
    print("   1. Estrai lo ZIP")
    print("   2. Doppio click su install.bat")
    print("   3. Doppio click su avvia.bat")
    print()
    print(f"🔑 Credenziali admin:")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print()
    print(f"📊 Google Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print()


if __name__ == "__main__":
    main()
