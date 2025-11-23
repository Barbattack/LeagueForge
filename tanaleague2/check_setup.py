#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TanaLeague - Setup Checker
===========================

Verifica che l'installazione sia configurata correttamente.

UTILIZZO:
    python check_setup.py

COSA VERIFICA:
- config.py esiste e contiene valori validi
- File credenziali Google esiste
- Connessione a Google Sheets funziona
- Fogli necessari esistono
- Achievement sono configurati
- Dipendenze Python installate
"""

import sys
import os
from pathlib import Path

# Colori per output (se supportati)
class Colors:
    OK = '\033[92m'      # Verde
    WARN = '\033[93m'    # Giallo
    FAIL = '\033[91m'    # Rosso
    END = '\033[0m'      # Reset
    BOLD = '\033[1m'


def colorize(text, color):
    """Aggiunge colore al testo (se supportato)."""
    if sys.platform == 'win32':
        return text  # Windows non supporta bene i colori ANSI
    return f"{color}{text}{Colors.END}"


def check_ok(message):
    print(f"  {colorize('[OK]', Colors.OK)} {message}")
    return True


def check_warn(message):
    print(f"  {colorize('[WARN]', Colors.WARN)} {message}")
    return True


def check_fail(message):
    print(f"  {colorize('[FAIL]', Colors.FAIL)} {message}")
    return False


def check_dependencies():
    """Verifica dipendenze Python."""
    print("\n📦 Verifica dipendenze Python...")

    all_ok = True
    deps = {
        'flask': 'Flask',
        'gspread': 'gspread',
        'google.oauth2': 'google-auth',
        'werkzeug': 'Werkzeug',
    }

    for module, package in deps.items():
        try:
            __import__(module)
            check_ok(f"{package} installato")
        except ImportError:
            check_fail(f"{package} non trovato (pip install {package.lower()})")
            all_ok = False

    # Opzionali
    optional = {'pandas': 'pandas', 'pdfplumber': 'pdfplumber'}
    for module, package in optional.items():
        try:
            __import__(module)
            check_ok(f"{package} installato (opzionale)")
        except ImportError:
            check_warn(f"{package} non installato (opzionale, serve per alcuni import)")

    return all_ok


def check_config():
    """Verifica config.py."""
    print("\n⚙️  Verifica configurazione...")

    # Check config.py exists
    config_path = Path(__file__).parent / "config.py"
    if not config_path.exists():
        check_fail("config.py non trovato!")
        print("      → Esegui: python setup_wizard.py")
        return False

    check_ok("config.py trovato")

    # Check config values
    try:
        from config import SHEET_ID, CREDENTIALS_FILE, ADMIN_USERNAME, SECRET_KEY

        if SHEET_ID == "IL_TUO_GOOGLE_SHEET_ID_QUI" or len(SHEET_ID) < 20:
            check_fail("SHEET_ID non configurato")
            return False
        check_ok(f"SHEET_ID configurato ({SHEET_ID[:20]}...)")

        if SECRET_KEY == "genera-una-chiave-casuale-qui":
            check_warn("SECRET_KEY è ancora il valore di default!")
        else:
            check_ok("SECRET_KEY configurato")

        check_ok(f"ADMIN_USERNAME: {ADMIN_USERNAME}")

        return True

    except ImportError as e:
        check_fail(f"Errore import config: {e}")
        return False


def check_credentials():
    """Verifica file credenziali Google."""
    print("\n🔑 Verifica credenziali Google...")

    try:
        from config import CREDENTIALS_FILE
    except ImportError:
        check_fail("Impossibile leggere CREDENTIALS_FILE da config.py")
        return False

    creds_path = Path(CREDENTIALS_FILE)
    if not creds_path.is_absolute():
        creds_path = Path(__file__).parent / CREDENTIALS_FILE

    if not creds_path.exists():
        check_fail(f"File credenziali non trovato: {CREDENTIALS_FILE}")
        print("      → Scarica il file JSON dal Google Cloud Console")
        return False

    check_ok(f"File credenziali trovato: {creds_path.name}")

    # Verifica che sia un JSON valido
    import json
    try:
        with open(creds_path) as f:
            creds_data = json.load(f)

        if 'client_email' in creds_data:
            check_ok(f"Service Account: {creds_data['client_email']}")
        else:
            check_warn("File credenziali potrebbe non essere valido")

        return True
    except json.JSONDecodeError:
        check_fail("File credenziali non è un JSON valido")
        return False


def check_google_sheets():
    """Verifica connessione a Google Sheets."""
    print("\n📊 Verifica connessione Google Sheets...")

    try:
        from config import SHEET_ID, CREDENTIALS_FILE
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)

        sheet = client.open_by_key(SHEET_ID)
        check_ok(f"Connesso a: {sheet.title}")

        # Verifica fogli esistenti
        worksheets = [ws.title for ws in sheet.worksheets()]

        required = ['Config', 'Tournaments', 'Results', 'Players']
        optional = ['Achievement_Definitions', 'Player_Achievements', 'Seasonal_Standings_PROV']

        all_required_ok = True
        for ws_name in required:
            if ws_name in worksheets:
                check_ok(f"Foglio '{ws_name}' presente")
            else:
                check_fail(f"Foglio '{ws_name}' mancante!")
                all_required_ok = False

        for ws_name in optional:
            if ws_name in worksheets:
                check_ok(f"Foglio '{ws_name}' presente")
            else:
                check_warn(f"Foglio '{ws_name}' mancante (opzionale)")

        if not all_required_ok:
            print("      → Esegui: python init_database.py")

        return all_required_ok

    except Exception as e:
        check_fail(f"Errore connessione: {e}")
        print("      → Verifica SHEET_ID e credenziali")
        return False


def check_achievements():
    """Verifica sistema achievement."""
    print("\n🏆 Verifica sistema achievement...")

    try:
        from config import SHEET_ID, CREDENTIALS_FILE
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)

        try:
            ws = sheet.worksheet("Achievement_Definitions")
            records = ws.get_all_values()
            n_achievements = len(records) - 1  # Escludi header

            if n_achievements > 0:
                check_ok(f"{n_achievements} achievement definiti")
            else:
                check_warn("Achievement_Definitions è vuoto")
                print("      → Esegui: python init_database.py")

            return True
        except gspread.exceptions.WorksheetNotFound:
            check_warn("Foglio Achievement_Definitions non trovato")
            print("      → Esegui: python init_database.py")
            return True  # Non bloccante

    except Exception as e:
        check_fail(f"Errore verifica achievement: {e}")
        return False


def check_app_startup():
    """Verifica che l'app Flask si avvii."""
    print("\n🚀 Verifica avvio applicazione...")

    try:
        # Prova solo l'import, non l'avvio completo
        sys.path.insert(0, str(Path(__file__).parent))
        from app import app
        check_ok("Applicazione Flask importata correttamente")
        return True
    except Exception as e:
        check_fail(f"Errore import app: {e}")
        return False


def main():
    print("=" * 60)
    print("🔍 TANALEAGUE - SETUP CHECKER")
    print("=" * 60)

    results = {}

    # Check 1: Dipendenze
    results['deps'] = check_dependencies()

    # Check 2: Config
    results['config'] = check_config()

    if not results['config']:
        print("\n⛔ Setup interrotto: config.py non valido")
        print("   Esegui: python setup_wizard.py")
        return

    # Check 3: Credenziali
    results['creds'] = check_credentials()

    if not results['creds']:
        print("\n⛔ Setup interrotto: credenziali non trovate")
        return

    # Check 4: Google Sheets
    results['sheets'] = check_google_sheets()

    # Check 5: Achievement
    results['achievements'] = check_achievements()

    # Check 6: App
    results['app'] = check_app_startup()

    # === RIEPILOGO ===
    print("\n" + "=" * 60)
    print("📋 RIEPILOGO")
    print("=" * 60)

    all_ok = all(results.values())

    if all_ok:
        print(colorize("\n✅ SETUP COMPLETO! Tutto funziona correttamente.", Colors.OK))
        print("\nPuoi avviare l'applicazione con:")
        print("  python app.py")
        print("\nPoi apri: http://localhost:5000")
    else:
        print(colorize("\n⚠️  SETUP INCOMPLETO", Colors.WARN))
        print("\nProblemi trovati:")
        for name, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {name}")
        print("\nRisolvi i problemi ed esegui nuovamente questo script.")

    print()


if __name__ == "__main__":
    main()
