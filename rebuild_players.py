#!/usr/bin/env python3
"""
Ricostruisce Players da Results (fix dati corrotti)
"""
import gspread
from google.oauth2.service_account import Credentials
from sheet_utils import COL_RESULTS
from api_utils import safe_api_call
import time

def safe_get(row, col_map, key, default=''):
    try:
        idx = col_map.get(key)
        return row[idx] if idx is not None and idx < len(row) else default
    except (IndexError, KeyError):
        return default

def safe_int(row, col_map, key, default=0):
    val = safe_get(row, col_map, key, default)
    try:
        return int(float(val)) if val else default
    except:
        return default

def safe_float(row, col_map, key, default=0.0):
    val = safe_get(row, col_map, key, default)
    try:
        return float(val) if val else default
    except:
        return default

print("🔧 REBUILD PLAYERS da Results...")

from config import SHEET_ID, CREDENTIALS_FILE

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# Leggi Results
ws_results = sheet.worksheet("Results")
print("  📖 Lettura Results...")
time.sleep(1.2)
all_results = safe_api_call(ws_results.get_all_values)[3:]

# Calcola stats per (membership, tcg)
print("  🧮 Calcolo stats...")
player_stats = {}

for row in all_results:
    if not row or len(row) < 3:
        continue
    
    membership = row[2]  # Col C
    tid = row[1] if len(row) > 1 else ''
    tcg = ''.join(c for c in tid.split('_')[0] if c.isalpha()).upper()
    name = row[3] if len(row) > 3 else ''
    
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
            'total_points': 0,
            'first_seen': None,
            'last_seen': None
        }
    
    stats = player_stats[key]
    stats['total_tournaments'] += 1
    
    rank = safe_int(row, COL_RESULTS, 'rank', 999)
    if rank == 1:
        stats['tournament_wins'] += 1
    
    stats['match_w'] += safe_int(row, COL_RESULTS, 'match_w', 0)
    stats['match_t'] += safe_int(row, COL_RESULTS, 'match_t', 0)
    stats['match_l'] += safe_int(row, COL_RESULTS, 'match_l', 0)
    stats['total_points'] += safe_float(row, COL_RESULTS, 'points_total', 0)
    
    # Date da tournament_id
    date = tid.split('_')[1] if '_' in tid else ''
    if date:
        if not stats['first_seen'] or date < stats['first_seen']:
            stats['first_seen'] = date
        if not stats['last_seen'] or date > stats['last_seen']:
            stats['last_seen'] = date

print(f"  ✅ {len(player_stats)} giocatori trovati")

# Scrivi Players
ws_players = sheet.worksheet("Players")
print("  🗑️  Cancellazione Players vecchi...")
time.sleep(1.2)
safe_api_call(ws_players.batch_clear, ["A4:K1000"])

# Prepara righe
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

print(f"  💾 Scrittura {len(rows)} righe...")
time.sleep(1.2)
safe_api_call(ws_players.append_rows, rows, value_input_option='RAW')

print("✅ REBUILD COMPLETATO!")
