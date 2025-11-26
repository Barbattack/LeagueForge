#!/usr/bin/env python3
"""
=================================================================================
TanaLeague v2.0 - Rebuild Player Stats
=================================================================================

Ricostruisce il foglio Player_Stats aggregando tutti i dati da Results.
Usare:
  - Alla prima installazione
  - Dopo modifiche manuali ai Results
  - Per sincronizzare dati corrotti

UTILIZZO:
    python rebuild_player_stats.py           # Rebuild completo
    python rebuild_player_stats.py --test    # Dry run (no scrittura)
=================================================================================
"""

import sys
import argparse
from datetime import datetime
from collections import defaultdict

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Moduli mancanti. Esegui: pip install gspread google-auth")
    sys.exit(1)

try:
    from config import SHEET_ID, CREDENTIALS_FILE
except ImportError:
    print("❌ config.py non trovato. Copia config_example.py e configura.")
    sys.exit(1)

from sheet_utils import COL_RESULTS, COL_CONFIG, safe_get, safe_int

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Header del foglio Player_Stats
PLAYER_STATS_HEADER = [
    "Membership", "Name", "TCG", "Total Tournaments", "Total Wins",
    "Current Streak", "Best Streak", "Top8 Count", "Last Rank",
    "Last Date", "Seasons Count", "Updated At"
]


def connect_sheet():
    """Connette al Google Sheet."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def get_tcg_from_season(season_id: str) -> str:
    """Estrae codice TCG da season_id (es. 'OP12' -> 'OP', 'RB-01' -> 'RB')."""
    if not season_id:
        return 'UNK'
    # Gestisce formati: OP12, RB-01, PKM-S1
    if '-' in season_id:
        return season_id.split('-')[0].upper()
    # Estrae lettere iniziali
    tcg = ''.join(c for c in season_id if c.isalpha()).upper()
    return tcg if tcg else 'UNK'


def rebuild_stats(sheet, test_mode=False):
    """
    Ricostruisce Player_Stats da Results.

    Returns:
        int: Numero di righe scritte
    """
    print("📊 Lettura Results...")
    ws_results = sheet.worksheet("Results")
    all_results = ws_results.get_all_values()[3:]  # Skip header
    print(f"   Trovate {len(all_results)} righe")

    # Carica stagioni ARCHIVED da escludere
    print("📋 Lettura Config (stagioni ARCHIVED)...")
    ws_config = sheet.worksheet("Config")
    config_data = ws_config.get_all_values()[4:]  # Skip header

    archived_seasons = set()
    for row in config_data:
        season_id = safe_get(row, COL_CONFIG, 'season_id')
        status = (safe_get(row, COL_CONFIG, 'status') or '').strip().upper()
        if status == "ARCHIVED":
            archived_seasons.add(season_id)
    print(f"   Stagioni ARCHIVED: {len(archived_seasons)}")

    # Aggrega stats per membership + tcg
    print("🧮 Calcolo statistiche...")
    player_data = defaultdict(lambda: {
        'name': '',
        'tournaments': [],
        'wins': 0,
        'top8': 0,
        'seasons': set(),
        'results_by_tournament': []  # [(tournament_id, rank)]
    })

    for row in all_results:
        tournament_id = safe_get(row, COL_RESULTS, 'tournament_id', '')
        # Estrai season_id da tournament_id (es. "OP12_20251113" -> "OP12")
        season_id = tournament_id.split('_')[0] if tournament_id and '_' in tournament_id else ''

        # Skip stagioni ARCHIVED
        if season_id in archived_seasons:
            continue

        membership = safe_get(row, COL_RESULTS, 'membership')
        if not membership:
            continue

        tcg = get_tcg_from_season(season_id)
        key = (membership, tcg)
        rank = safe_int(row, COL_RESULTS, 'rank', 999)
        name = safe_get(row, COL_RESULTS, 'name', '')

        data = player_data[key]
        if name:
            data['name'] = name
        data['tournaments'].append(tournament_id)
        data['seasons'].add(season_id)
        data['results_by_tournament'].append((tournament_id, rank))

        if rank == 1:
            data['wins'] += 1
        if rank <= 8:
            data['top8'] += 1

    print(f"   Giocatori unici: {len(player_data)}")

    # Prepara righe per Player_Stats
    print("📝 Preparazione dati...")
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    rows = []

    for (membership, tcg), data in player_data.items():
        # Ordina risultati per tournament_id per calcolare streak
        sorted_results = sorted(data['results_by_tournament'], key=lambda x: x[0])

        # Calcola streak (top8 consecutivi)
        current_streak = 0
        best_streak = 0
        for _, rank in sorted_results:
            if rank <= 8:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0

        # Ultimo risultato
        last_tournament, last_rank = sorted_results[-1] if sorted_results else ('', 999)
        # Estrai data da tournament_id (formato: YYYYMMDD o simile)
        last_date = ''
        if last_tournament and '_' in last_tournament:
            # Prova a estrarre data (primi 8 caratteri se numerici)
            date_part = last_tournament.split("_")[1]  # "20251113"
            if len(date_part) == 8 and date_part.isdigit():
                try:
                    last_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                except:
                    pass

        row = [
            membership,
            data['name'],
            tcg,
            len(data['tournaments']),  # total_tournaments
            data['wins'],              # total_wins
            current_streak,            # current_streak
            best_streak,               # best_streak
            data['top8'],              # top8_count
            last_rank if last_rank < 999 else '',  # last_rank
            last_date,                 # last_date
            len(data['seasons']),      # seasons_count
            now                        # updated_at
        ]
        rows.append(row)

    # Ordina per TCG, poi per wins decrescenti
    rows.sort(key=lambda x: (x[2], -x[4], x[0]))

    if test_mode:
        print("\n🧪 TEST MODE - Nessuna scrittura")
        print(f"   Righe da scrivere: {len(rows)}")
        if rows:
            print(f"   Prima riga: {rows[0]}")
            print(f"   Ultima riga: {rows[-1]}")
        return 0

    # Scrivi su Player_Stats
    print("💾 Scrittura Player_Stats...")

    try:
        ws_stats = sheet.worksheet("Player_Stats")
    except gspread.WorksheetNotFound:
        print("   Creazione foglio Player_Stats...")
        ws_stats = sheet.add_worksheet(title="Player_Stats", rows=1000, cols=15)

    # Clear e riscrivi
    ws_stats.clear()

    # Header (righe 1-3 come altri fogli)
    header_rows = [
        ["Player Stats - Aggregati pre-calcolati"],
        ["Aggiornato automaticamente da import scripts"],
        PLAYER_STATS_HEADER
    ]

    # Batch write
    all_data = header_rows + rows
    ws_stats.update(f'A1:L{len(all_data)}', all_data, value_input_option='USER_ENTERED')

    print(f"✅ Scritte {len(rows)} righe")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description='Rebuild Player Stats')
    parser.add_argument('--test', action='store_true', help='Dry run, no write')
    args = parser.parse_args()

    print("=" * 60)
    print("🔄 REBUILD PLAYER STATS")
    print("=" * 60)

    try:
        sheet = connect_sheet()
        print("📡 Connesso a Google Sheet")

        count = rebuild_stats(sheet, test_mode=args.test)

        print("=" * 60)
        if args.test:
            print("🧪 Test completato!")
        else:
            print(f"✅ REBUILD COMPLETATO! ({count} giocatori)")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
