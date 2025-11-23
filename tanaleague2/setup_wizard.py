#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TanaLeague - Setup Wizard
==========================

Configurazione interattiva guidata per TanaLeague.
Genera automaticamente config.py con i valori inseriti.

UTILIZZO:
    python setup_wizard.py

COSA FA:
1. Chiede nome negozio e personalizzazioni
2. Chiede SHEET_ID del Google Sheet
3. Chiede path del file credenziali
4. Chiede username e password admin
5. Genera automaticamente:
   - SECRET_KEY (casuale)
   - ADMIN_PASSWORD_HASH (da password inserita)
6. Salva tutto in config.py
"""

import os
import sys
import secrets
from pathlib import Path

# Verifica dipendenze
try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("❌ Errore: installa werkzeug con 'pip install werkzeug'")
    sys.exit(1)


def clear_screen():
    """Pulisce lo schermo."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Stampa header wizard."""
    print("=" * 60)
    print("🎮 TANALEAGUE - SETUP WIZARD")
    print("=" * 60)
    print()


def get_input(prompt, default=None, required=True, password=False):
    """Input con default e validazione."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        if password:
            import getpass
            try:
                value = getpass.getpass(prompt)
            except:
                value = input(prompt)
        else:
            value = input(prompt).strip()

        if not value and default:
            return default
        if not value and required:
            print("  ⚠️  Questo campo è obbligatorio!")
            continue
        return value


def validate_sheet_id(sheet_id):
    """Valida formato SHEET_ID."""
    # Google Sheet IDs sono stringhe alfanumeriche di ~44 caratteri
    if len(sheet_id) < 20:
        return False, "SHEET_ID troppo corto. Verifica l'URL del Google Sheet."
    if " " in sheet_id:
        return False, "SHEET_ID non può contenere spazi."
    return True, ""


def validate_credentials_file(path):
    """Verifica che il file credenziali esista."""
    if os.path.exists(path):
        return True, ""
    return False, f"File non trovato: {path}"


def generate_config(data):
    """Genera contenuto config.py."""
    config_content = f'''# -*- coding: utf-8 -*-
"""
TanaLeague - Configuration
===========================
Generato automaticamente da setup_wizard.py
Data: {data["timestamp"]}

NON caricare questo file su GitHub!
"""

import os

# ==============================================================================
# PERSONALIZZAZIONE NEGOZIO
# ==============================================================================
STORE_NAME = "{data["store_name"]}"
STORE_LOGO = "static/logo.png"
STORE_TAGLINE = "{data["store_tagline"]}"

STORE_PRIMARY_COLOR = "{data["primary_color"]}"
STORE_SECONDARY_COLOR = "{data["secondary_color"]}"

STORE_INSTAGRAM = "{data["instagram"]}"
STORE_WHATSAPP = "{data["whatsapp"]}"
STORE_WEBSITE = "{data["website"]}"

# ==============================================================================
# GOOGLE SHEETS
# ==============================================================================
SHEET_ID = "{data["sheet_id"]}"
CREDENTIALS_FILE = "{data["credentials_file"]}"

# ==============================================================================
# ADMIN LOGIN
# ==============================================================================
ADMIN_USERNAME = "{data["admin_username"]}"
ADMIN_PASSWORD_HASH = "{data["admin_password_hash"]}"
SESSION_TIMEOUT = 30

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================
CACHE_REFRESH_MINUTES = 5
CACHE_FILE = "cache_data.json"

# ==============================================================================
# APP SETTINGS
# ==============================================================================
SECRET_KEY = "{data["secret_key"]}"
DEBUG = False

# ==============================================================================
# TCG SETTINGS
# ==============================================================================
ENABLE_ONEPIECE = True
ENABLE_POKEMON = True
ENABLE_RIFTBOUND = True
'''
    return config_content


def main():
    clear_screen()
    print_header()

    print("Benvenuto nel Setup Wizard di TanaLeague!")
    print("Ti guiderò nella configurazione del sistema.")
    print()
    print("Premi INVIO per usare i valori predefiniti [tra parentesi]")
    print()

    # Verifica se config.py esiste già
    config_path = Path(__file__).parent / "config.py"
    if config_path.exists():
        print("⚠️  ATTENZIONE: config.py esiste già!")
        resp = input("Vuoi sovrascriverlo? (y/n): ").strip().lower()
        if resp != 'y':
            print("❌ Setup annullato.")
            return
        print()

    data = {}
    data["timestamp"] = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # === SEZIONE 1: PERSONALIZZAZIONE NEGOZIO ===
    print("─" * 60)
    print("📌 SEZIONE 1: PERSONALIZZAZIONE NEGOZIO")
    print("─" * 60)
    print()

    data["store_name"] = get_input("Nome del tuo negozio/lega", default="TanaLeague")
    data["store_tagline"] = get_input("Slogan/descrizione breve", default="Sistema di gestione classifiche TCG")

    print()
    print("Colori tema (formato esadecimale, es. #1a73e8):")
    data["primary_color"] = get_input("Colore principale", default="#1a73e8")
    data["secondary_color"] = get_input("Colore secondario", default="#34a853")

    print()
    print("Link social (lascia vuoto se non li usi):")
    data["instagram"] = get_input("Link Instagram", default="", required=False)
    data["whatsapp"] = get_input("Link WhatsApp", default="", required=False)
    data["website"] = get_input("Sito web", default="", required=False)

    # === SEZIONE 2: GOOGLE SHEETS ===
    print()
    print("─" * 60)
    print("📌 SEZIONE 2: GOOGLE SHEETS")
    print("─" * 60)
    print()
    print("Hai bisogno di:")
    print("  1. Un Google Sheet (anche vuoto)")
    print("  2. Un Service Account con accesso al Google Sheet")
    print()
    print("L'ID del Google Sheet si trova nell'URL:")
    print("  https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit")
    print()

    while True:
        sheet_id = get_input("SHEET_ID del Google Sheet")
        valid, error = validate_sheet_id(sheet_id)
        if valid:
            data["sheet_id"] = sheet_id
            break
        print(f"  ❌ {error}")

    print()
    print("Il file credenziali JSON del Service Account:")
    print("  (es. service_account_credentials.json)")
    print()

    while True:
        creds_file = get_input("Path file credenziali", default="service_account_credentials.json")
        valid, error = validate_credentials_file(creds_file)
        if valid:
            data["credentials_file"] = creds_file
            break
        print(f"  ⚠️  {error}")
        resp = input("  Vuoi usarlo comunque? (y/n): ").strip().lower()
        if resp == 'y':
            data["credentials_file"] = creds_file
            break

    # === SEZIONE 3: ADMIN LOGIN ===
    print()
    print("─" * 60)
    print("📌 SEZIONE 3: ADMIN LOGIN")
    print("─" * 60)
    print()
    print("Credenziali per accedere al pannello admin (/admin/login)")
    print()

    data["admin_username"] = get_input("Username admin", default="admin")

    while True:
        password = get_input("Password admin", password=True)
        if len(password) < 6:
            print("  ⚠️  La password deve essere di almeno 6 caratteri!")
            continue
        password2 = get_input("Conferma password", password=True)
        if password != password2:
            print("  ⚠️  Le password non coincidono!")
            continue
        break

    data["admin_password_hash"] = generate_password_hash(password)
    data["secret_key"] = secrets.token_hex(32)

    # === RIEPILOGO ===
    print()
    print("─" * 60)
    print("📋 RIEPILOGO CONFIGURAZIONE")
    print("─" * 60)
    print()
    print(f"  Nome negozio:    {data['store_name']}")
    print(f"  SHEET_ID:        {data['sheet_id'][:30]}...")
    print(f"  Credenziali:     {data['credentials_file']}")
    print(f"  Admin username:  {data['admin_username']}")
    print(f"  Admin password:  {'*' * len(password)}")
    print()

    resp = input("Salvare questa configurazione? (y/n): ").strip().lower()
    if resp != 'y':
        print("❌ Setup annullato.")
        return

    # === SALVATAGGIO ===
    config_content = generate_config(data)

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print()
        print("=" * 60)
        print("🎉 CONFIGURAZIONE COMPLETATA!")
        print("=" * 60)
        print()
        print(f"✅ File creato: {config_path}")
        print()
        print("📝 Prossimi passi:")
        print("  1. python init_database.py   → Crea i fogli nel Google Sheet")
        print("  2. python check_setup.py     → Verifica che tutto funzioni")
        print("  3. python app.py             → Avvia l'applicazione!")
        print()
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return


if __name__ == "__main__":
    main()
