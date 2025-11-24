#!/usr/bin/env python3
"""Ricostruisce Players da Results (FIXED)"""
import gspread
from google.oauth2.service_account import Credentials
from sheet_utils import COL_RESULTS, safe_get, safe_int, safe_float
from api_utils import safe_api_call
import time

print("🔧 REBUILD PLAYERS da Results (VERSIONE CORRETTA)...")

from config import SHEET_ID, CREDENTIALS_FILE

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

ws_results = sheet.worksheet("Results")
print("  📖 Lettura Results...")
time.sleep(1.2)
all_results = safe_api_call(ws_results.get_all_values)[3:]

print(f"  📊 {len(all_results)} risultati trovati")

# Calcola stats
player_stats = {}

for row in all_results:
    if not row or len(row) < 6:
        continue

    membership = safe_get(row, COL_RESULTS, 'membership')
    tid = safe_get(row, COL_RESULTS, 'tournament_id')
    name = safe_get(row, COL_RESULTS, 'name')

    tcg = ''.join(c for c in tid.split('_')[0] if c.isalpha()).upper() if tid else ''

    if not membership or not tcg:
        continue

    key = (membership, tcg)

    if key not in player_stats:
        player_stats[key] = {
            'name': name,
            'total_tournaments': 0,
            'tournament_wins': 0,
            'match_w': 0,
            'match_t': 0,
            'match_l': 0,
            'total_points': 0.0,
            'first_seen': None,
            'last_seen': None
        }

    stats = player_stats[key]
    if name:
        stats['name'] = name

    stats['total_tournaments'] += 1

    rank = safe_int(row, COL_RESULTS, 'rank', 999)
    if rank == 1:
        stats['tournament_wins'] += 1

    stats['match_w'] += safe_int(row, COL_RESULTS, 'match_w', 0)
    stats['match_t'] += safe_int(row, COL_RESULTS, 'match_t', 0)
    stats['match_l'] += safe_int(row, COL_RESULTS, 'match_l', 0)
    stats['total_points'] += safe_float(row, COL_RESULTS, 'points', 0)

    date = tid.split('_')[1] if '_' in tid else ''
    if date:
        if not stats['first_seen'] or date < stats['first_seen']:
            stats['first_seen'] = date
        if not stats['last_seen'] or date > stats['last_seen']:
            stats['last_seen'] = date

print(f"  ✅ {len(player_stats)} giocatori processati")

# Scrivi Players
ws_players = sheet.worksheet("Players")
print("  🗑️  Cancellazione vecchi dati...")
time.sleep(1.2)
safe_api_call(ws_players.batch_clear, ["A4:K1000"])

rows = []
for (membership, tcg), stats in sorted(player_stats.items()):
    rows.append([
        membership,
        stats['name'],
        tcg,
        stats.get('first_seen', ''),
        stats.get('last_seen', ''),
        stats['total_tournaments'],
        stats['tournament_wins'],
        stats['match_w'],
        stats['match_t'],
        stats['match_l'],
        stats['total_points']
    ])

print(f"  💾 Scrittura {len(rows)} giocatori...")
time.sleep(1.2)
safe_api_call(ws_players.append_rows, rows, value_input_option='RAW')

print("✅ REBUILD COMPLETATO!")
print(f"   Primi 3: {[(r[0], r[1], r[2]) for r in rows[:3]]}")
