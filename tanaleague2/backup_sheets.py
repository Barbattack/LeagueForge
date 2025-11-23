"""
TanaLeague - Backup Automatico Google Sheets
=============================================

Script per creare backup completi del database Google Sheets.

USO:
    # Backup completo (tutti i fogli)
    python backup_sheets.py

    # Backup specifico foglio
    python backup_sheets.py --sheet Results

    # Backup in cartella specifica
    python backup_sheets.py --output /path/to/backups

OUTPUT:
    backups/
    └── 2025-11-23_14-30-00/
        ├── backup_info.json      # Metadati backup
        ├── Config.csv
        ├── Tournaments.csv
        ├── Results.csv
        ├── Players.csv
        ├── Achievement_Definitions.csv
        ├── Player_Achievements.csv
        └── ... (altri fogli)

SCHEDULING (opzionale):
    # Linux/Mac - Aggiungi a crontab per backup giornaliero alle 3:00
    crontab -e
    0 3 * * * cd /path/to/TanaLeague/tanaleague2 && python backup_sheets.py

    # PythonAnywhere - Usa "Scheduled Tasks" nel tab Tasks
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from pathlib import Path

# Aggiungi path per import locali
sys.path.insert(0, str(Path(__file__).parent))

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Errore: installa dipendenze con 'pip install gspread google-auth'")
    sys.exit(1)

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

# Directory backup (relativa a questo script)
DEFAULT_BACKUP_DIR = Path(__file__).parent / "backups"

# Importa configurazione da config.py
try:
    from config import SHEET_ID, CREDENTIALS_FILE
except ImportError:
    print("⚠️  config.py non trovato, alcune funzionalità potrebbero non funzionare.")
    print("   Copia config.example.py in config.py e configura i valori.")
    SHEET_ID = None
    CREDENTIALS_FILE = Path(__file__).parent / "service_account_credentials.json"

# Fogli da backuppare (in ordine di importanza)
SHEETS_TO_BACKUP = [
    "Config",
    "Tournaments",
    "Results",
    "Players",
    "Seasonal_Standings_PROV",
    "Seasonal_Standings_FINAL",
    "Achievement_Definitions",
    "Player_Achievements",
    "Vouchers",
    "Pokemon_Matches",
    "Riftbound_Matches",
    "Backup_Log",
]

# Numero massimo di backup da mantenere (i più vecchi vengono eliminati)
MAX_BACKUPS = 10


# =============================================================================
# FUNZIONI PRINCIPALI
# =============================================================================

def connect_to_sheets():
    """Connette a Google Sheets."""
    if not CREDENTIALS_FILE.exists():
        print(f"❌ File credenziali non trovato: {CREDENTIALS_FILE}")
        print("   Scarica da Google Cloud Console e salva come 'service_account_credentials.json'")
        sys.exit(1)

    if not SHEET_ID:
        print("❌ SHEET_ID non configurato")
        print("   Imposta SHEET_ID in config.py o passa --sheet-id")
        sys.exit(1)

    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
    client = gspread.authorize(creds)

    return client.open_by_key(SHEET_ID)


def backup_worksheet(worksheet, output_dir: Path) -> dict:
    """
    Backup singolo foglio in CSV.

    Returns:
        dict con info sul backup
    """
    filename = f"{worksheet.title}.csv"
    filepath = output_dir / filename

    try:
        # Scarica tutti i dati
        data = worksheet.get_all_values()
        rows = len(data)

        # Scrivi CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)

        return {
            'sheet': worksheet.title,
            'file': filename,
            'rows': rows,
            'status': 'success'
        }

    except Exception as e:
        return {
            'sheet': worksheet.title,
            'file': filename,
            'rows': 0,
            'status': 'error',
            'error': str(e)
        }


def cleanup_old_backups(backup_dir: Path, max_backups: int):
    """Elimina backup vecchi mantenendo solo gli ultimi N."""
    if not backup_dir.exists():
        return

    # Lista tutte le cartelle di backup (ordinate per data)
    backup_folders = sorted([
        d for d in backup_dir.iterdir()
        if d.is_dir() and d.name[0].isdigit()
    ])

    # Elimina i più vecchi
    while len(backup_folders) > max_backups:
        oldest = backup_folders.pop(0)
        print(f"🗑️  Eliminato backup vecchio: {oldest.name}")

        # Elimina tutti i file nella cartella
        for file in oldest.iterdir():
            file.unlink()
        oldest.rmdir()


def run_backup(output_dir: Path = None, sheets: list = None, sheet_id: str = None):
    """
    Esegue backup completo.

    Args:
        output_dir: Directory dove salvare (default: backups/)
        sheets: Lista fogli da backuppare (default: tutti)
        sheet_id: Override SHEET_ID
    """
    global SHEET_ID
    if sheet_id:
        SHEET_ID = sheet_id

    # Setup directory
    if output_dir is None:
        output_dir = DEFAULT_BACKUP_DIR

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = output_dir / timestamp
    backup_folder.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🔄 BACKUP GOOGLE SHEETS - TanaLeague")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Output: {backup_folder}")
    print()

    # Connetti
    print("🔗 Connessione a Google Sheets...")
    try:
        spreadsheet = connect_to_sheets()
        print(f"   ✅ Connesso a: {spreadsheet.title}")
    except Exception as e:
        print(f"   ❌ Errore connessione: {e}")
        sys.exit(1)

    # Lista fogli disponibili
    available_sheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    sheets_to_backup = sheets if sheets else SHEETS_TO_BACKUP

    print()
    print("📋 Backup fogli...")

    backup_info = {
        'timestamp': timestamp,
        'spreadsheet_title': spreadsheet.title,
        'spreadsheet_id': SHEET_ID,
        'sheets': []
    }

    success_count = 0
    error_count = 0

    for sheet_name in sheets_to_backup:
        if sheet_name in available_sheets:
            result = backup_worksheet(available_sheets[sheet_name], backup_folder)
            backup_info['sheets'].append(result)

            if result['status'] == 'success':
                print(f"   ✅ {sheet_name}: {result['rows']} righe")
                success_count += 1
            else:
                print(f"   ❌ {sheet_name}: {result['error']}")
                error_count += 1
        else:
            print(f"   ⚠️  {sheet_name}: foglio non trovato (skip)")

    # Salva metadati backup
    info_file = backup_folder / "backup_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, indent=2, ensure_ascii=False)

    # Cleanup vecchi backup
    cleanup_old_backups(output_dir, MAX_BACKUPS)

    # Riepilogo
    print()
    print("=" * 60)
    print(f"✅ BACKUP COMPLETATO")
    print(f"   Fogli salvati: {success_count}")
    if error_count:
        print(f"   Errori: {error_count}")
    print(f"   Cartella: {backup_folder}")
    print("=" * 60)

    return backup_info


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Backup Google Sheets TanaLeague',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python backup_sheets.py                    # Backup completo
  python backup_sheets.py --sheet Results    # Solo foglio Results
  python backup_sheets.py --output ./mybackups
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help='Directory output (default: backups/)'
    )

    parser.add_argument(
        '--sheet', '-s',
        action='append',
        help='Foglio specifico da backuppare (ripetibile)'
    )

    parser.add_argument(
        '--sheet-id',
        help='Override SHEET_ID da config'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='Mostra lista fogli disponibili ed esci'
    )

    args = parser.parse_args()

    if args.list:
        print("Fogli configurati per backup:")
        for sheet in SHEETS_TO_BACKUP:
            print(f"  - {sheet}")
        return

    run_backup(
        output_dir=args.output,
        sheets=args.sheet,
        sheet_id=args.sheet_id
    )


if __name__ == "__main__":
    main()
