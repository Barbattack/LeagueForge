#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge v2.0 - Import Base Module
=================================================================================

Modulo base condiviso tra tutti gli import scripts (One Piece, Pokemon, Riftbound).
Contiene funzioni comuni per evitare duplicazione di codice.

FUNZIONI:
- connect_sheet(): Connessione a Google Sheets
- check_duplicate_tournament(): Verifica torneo esistente
- write_results_to_sheet(): Scrittura Results (formato 13 colonne)
- update_players(): Aggiornamento lifetime stats Players
- update_seasonal_standings(): Aggiornamento classifica stagionale
- finalize_import(): Achievement check + Player_Stats update
- calculate_leagueforge_points(): Formula punti LeagueForge

UTILIZZO:
    from import_base import (
        connect_sheet,
        check_duplicate_tournament,
        write_results_to_sheet,
        update_players,
        update_seasonal_standings,
        finalize_import
    )
=================================================================================
"""

import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Moduli mancanti. Esegui: pip install gspread google-auth")
    sys.exit(1)

# Import API retry utilities
from api_utils import safe_api_call

# Delay tra operazioni API per evitare rate limit (millisecondi)
API_DELAY_MS = 1200  # 1.2 secondi per rispettare 60 req/min

def api_delay():
    """Breve pausa tra chiamate API per rispettare rate limits"""
    time.sleep(API_DELAY_MS / 1000.0)

try:
    from config import SHEET_ID, CREDENTIALS_FILE
except ImportError:
    print("❌ config.py non trovato. Copia config_example.py e configura.")
    sys.exit(1)

from sheet_utils import (
    COL_CONFIG, COL_RESULTS, COL_PLAYERS, COL_PLAYER_STATS,
    safe_get, safe_int, safe_float, fuzzy_match
)
from achievements import check_and_unlock_achievements
from player_stats import update_player_stats_after_tournament, batch_update_player_stats

# =============================================================================
# CONSTANTS
# =============================================================================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# =============================================================================
# STANDARDIZED DATA STRUCTURE
# =============================================================================

def create_participant(
    membership: str,
    name: str,
    rank: int,
    wins: int = 0,
    ties: int = 0,
    losses: int = 0,
    win_points: int = 0,
    omw: float = 0.0
) -> Dict:
    """
    Crea struttura dati standardizzata per un partecipante.
    Usata da tutti i parser (OP, RFB, PKM).
    """
    return {
        'membership': str(membership).zfill(10),
        'name': name.strip(),
        'rank': rank,
        'wins': wins,
        'ties': ties,
        'losses': losses,
        'win_points': win_points if win_points else (wins * 3 + ties * 1),
        'omw': omw
    }


def create_tournament_data(
    tournament_id: str,
    season_id: str,
    date: str,
    participants: List[Dict],
    tcg: str,
    source_files: List[str] = None,
    winner_name: str = None
) -> Dict:
    """
    Crea struttura dati standardizzata per un torneo.
    """
    n_participants = len(participants)
    n_rounds = _estimate_rounds(n_participants)

    # Trova vincitore se non specificato
    if not winner_name and participants:
        winner = next((p for p in participants if p['rank'] == 1), participants[0])
        winner_name = winner['name']

    return {
        'tournament_id': tournament_id,
        'season_id': season_id,
        'date': date,
        'tcg': tcg,
        'n_participants': n_participants,
        'n_rounds': n_rounds,
        'winner_name': winner_name,
        'source_files': source_files or [],
        'participants': participants
    }


def _estimate_rounds(n_participants: int) -> int:
    """Stima numero round da partecipanti (Swiss system)."""
    if n_participants <= 4:
        return 3
    elif n_participants <= 8:
        return 3
    elif n_participants <= 16:
        return 4
    elif n_participants <= 32:
        return 5
    elif n_participants <= 64:
        return 6
    elif n_participants <= 128:
        return 7
    else:
        return 8


# =============================================================================
# CONNECTION
# =============================================================================

def connect_sheet():
    """
    Connette a Google Sheets.

    Returns:
        gspread.Spreadsheet: Oggetto spreadsheet connesso
    """
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


# =============================================================================
# DUPLICATE CHECK
# =============================================================================

def check_duplicate_tournament(sheet, tournament_id: str, allow_reimport: bool = False) -> Tuple[bool, Optional[Dict]]:
    """
    Verifica se un torneo esiste già.

    Args:
        sheet: Google Sheet connesso
        tournament_id: ID torneo da verificare
        allow_reimport: Se True, ritorna info per reimport invece di bloccare

    Returns:
        Tuple[bool, Dict]: (can_proceed, existing_data)
        - can_proceed: True se si può procedere
        - existing_data: Dati esistenti se torneo già presente
    """
    ws_tournaments = sheet.worksheet("Tournaments")
    api_delay()
    existing_ids = safe_api_call(ws_tournaments.col_values, 1)[3:]  # Skip header

    if tournament_id in existing_ids:
        if allow_reimport:
            return True, {'exists': True, 'tournament_id': tournament_id}
        else:
            print(f"⚠️  Torneo {tournament_id} già esistente!")
            return False, {'exists': True, 'tournament_id': tournament_id}

    return True, {'exists': False}


def delete_existing_tournament(sheet, tournament_id: str) -> bool:
    """
    Elimina dati di un torneo esistente per reimport.

    Args:
        sheet: Google Sheet connesso
        tournament_id: ID torneo da eliminare

    Returns:
        bool: True se eliminato con successo
    """
    try:
        # 1. Elimina da Results
        ws_results = sheet.worksheet("Results")
        api_delay()
        results = safe_api_call(ws_results.get_all_values)
        rows_to_delete = []
        for i, row in enumerate(results[3:], start=4):
            if row and len(row) > 1 and row[1] == tournament_id:
                rows_to_delete.append(i)

        if rows_to_delete:
            # Elimina dal basso verso l'alto
            for row_idx in sorted(rows_to_delete, reverse=True):
                ws_results.delete_rows(row_idx)
            print(f"   🗑️  Eliminati {len(rows_to_delete)} risultati")

        # 2. Elimina da Tournaments
        ws_tournaments = sheet.worksheet("Tournaments")
        api_delay()
        tournaments = safe_api_call(ws_tournaments.get_all_values)
        for i, row in enumerate(tournaments[3:], start=4):
            if row and row[0] == tournament_id:
                ws_tournaments.delete_rows(i)
                print(f"   🗑️  Eliminato torneo")
                break

        # 3. Elimina da Vouchers (se esiste)
        try:
            ws_vouchers = sheet.worksheet("Vouchers")
            api_delay()
            vouchers = safe_api_call(ws_vouchers.get_all_values)
            voucher_rows = []
            for i, row in enumerate(vouchers[3:], start=4):
                if row and len(row) > 1 and row[1] == tournament_id:
                    voucher_rows.append(i)
            for row_idx in sorted(voucher_rows, reverse=True):
                ws_vouchers.delete_rows(row_idx)
            if voucher_rows:
                print(f"   🗑️  Eliminati {len(voucher_rows)} voucher")
        except gspread.WorksheetNotFound:
            pass

        return True

    except Exception as e:
        print(f"❌ Errore eliminazione torneo: {e}")
        return False


# =============================================================================
# POINTS CALCULATION
# =============================================================================

def calculate_leagueforge_points(rank: int, wins: int, n_participants: int) -> Dict:
    """
    Calcola punti LeagueForge.

    Formula:
    - Points_Victory = numero vittorie (W)
    - Points_Ranking = n_participants - (rank - 1)
    - Points_Total = Victory + Ranking

    Args:
        rank: Piazzamento finale
        wins: Numero vittorie
        n_participants: Numero partecipanti

    Returns:
        Dict con points_victory, points_ranking, points_total
    """
    points_victory = wins
    points_ranking = n_participants - (rank - 1)
    points_total = points_victory + points_ranking

    return {
        'points_victory': points_victory,
        'points_ranking': points_ranking,
        'points_total': points_total
    }


# =============================================================================
# WRITE RESULTS
# =============================================================================

def write_results_to_sheet(sheet, tournament_data: Dict, test_mode: bool = False) -> int:
    """
    Scrive i risultati nel foglio Results.
    Formato standard 13 colonne.

    Args:
        sheet: Google Sheet connesso
        tournament_data: Dati torneo standardizzati
        test_mode: Se True, non scrive

    Returns:
        int: Numero righe scritte
    """
    if test_mode:
        print(f"✅ Results: {len(tournament_data['participants'])} giocatori (test mode)")
        return 0

    ws_results = sheet.worksheet("Results")

    tournament_id = tournament_data['tournament_id']
    n_participants = tournament_data['n_participants']

    rows = []
    for p in tournament_data['participants']:
        points = calculate_leagueforge_points(
            rank=p['rank'],
            wins=p['wins'],
            n_participants=n_participants
        )

        result_row = [
            f"{tournament_id}_{p['membership']}",  # Result_ID
            tournament_id,
            p['membership'],
            p['rank'],
            p['win_points'],
            p['omw'],
            points['points_victory'],
            points['points_ranking'],
            points['points_total'],
            p['name'],
            p['wins'],      # Match_W
            p['ties'],      # Match_T
            p['losses']     # Match_L
        ]
        rows.append(result_row)

    if rows:
        api_delay()
        safe_api_call(ws_results.append_rows, rows, value_input_option='RAW')

    print(f"✅ Results: {len(rows)} giocatori")
    return len(rows)


def write_tournament_to_sheet(sheet, tournament_data: Dict, test_mode: bool = False) -> bool:
    """
    Scrive i metadati del torneo nel foglio Tournaments.

    Args:
        sheet: Google Sheet connesso
        tournament_data: Dati torneo standardizzati
        test_mode: Se True, non scrive

    Returns:
        bool: True se scritto con successo
    """
    if test_mode:
        print(f"✅ Tournament: {tournament_data['tournament_id']} (test mode)")
        return True

    ws_tournaments = sheet.worksheet("Tournaments")

    tournament_row = [
        tournament_data['tournament_id'],
        tournament_data['season_id'],
        tournament_data['date'],
        tournament_data['n_participants'],
        tournament_data['n_rounds'],
        ','.join(tournament_data['source_files']),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        tournament_data['winner_name']
    ]

    api_delay()
    safe_api_call(ws_tournaments.append_row, tournament_row, value_input_option='RAW')
    print(f"✅ Tournament: {tournament_data['tournament_id']}")
    return True


# =============================================================================
# UPDATE PLAYERS
# =============================================================================

def update_players(sheet, tournament_data: Dict, test_mode: bool = False) -> Tuple[int, int]:
    """
    Aggiorna il foglio Players con lifetime stats.
    Ricalcola stats da TUTTI i Results del giocatore.

    Args:
        sheet: Google Sheet connesso
        tournament_data: Dati torneo standardizzati
        test_mode: Se True, non scrive

    Returns:
        Tuple[int, int]: (updated_count, new_count)
    """
    if test_mode:
        print(f"✅ Players: {len(tournament_data['participants'])} (test mode)")
        return 0, 0

    ws_players = sheet.worksheet("Players")
    ws_results = sheet.worksheet("Results")

    tcg = tournament_data['tcg']
    tournament_date = tournament_data['date']

    # Leggi players esistenti
    api_delay()
    existing_players = safe_api_call(ws_players.get_all_values)
    # Key: (membership, tcg) -> row_index
    existing_dict = {}
    for i, row in enumerate(existing_players[3:], start=4):
        if row and len(row) > 2:
            key = (row[0], row[2])  # membership, tcg
            existing_dict[key] = i

    # Leggi TUTTI i results per calcolare lifetime stats
    api_delay()
    all_results = safe_api_call(ws_results.get_all_values)[3:]

    # Calcola lifetime stats per TCG
    lifetime_stats = defaultdict(lambda: {
        'total_tournaments': 0,
        'tournament_wins': 0,
        'match_w': 0,
        'match_t': 0,
        'match_l': 0,
        'total_points': 0,
        'first_seen': None,
        'last_seen': None
    })

    for row in all_results:
        if len(row) < 10:
            continue

        membership = row[2]
        # Estrai TCG da tournament_id (es. OP12_20251113 -> OP)
        tid = row[1] if len(row) > 1 else ''
        row_tcg = ''.join(c for c in tid.split('_')[0] if c.isalpha()).upper()
        if not row_tcg:
            row_tcg = tcg

        key = (membership, row_tcg)
        stats = lifetime_stats[key]

        stats['total_tournaments'] += 1
        if safe_int(row, COL_RESULTS, 'rank', 999) == 1:
            stats['tournament_wins'] += 1

        stats['match_w'] += safe_int(row, COL_RESULTS, 'match_w', 0) if len(row) > 10 else 0
        stats['match_t'] += safe_int(row, COL_RESULTS, 'match_t', 0) if len(row) > 11 else 0
        stats['match_l'] += safe_int(row, COL_RESULTS, 'match_l', 0) if len(row) > 12 else 0
        stats['total_points'] += safe_float(row, COL_RESULTS, 'points_total', 0)

        # Track date
        result_date = tid.split('_')[1] if '_' in tid else ''
        if result_date:
            if not stats['first_seen'] or result_date < stats['first_seen']:
                stats['first_seen'] = result_date
            if not stats['last_seen'] or result_date > stats['last_seen']:
                stats['last_seen'] = result_date

    # Prepara update/insert
    rows_to_update = []
    rows_to_add = []

    for p in tournament_data['participants']:
        membership = p['membership']
        key = (membership, tcg)

        stats = lifetime_stats.get(key, {
            'total_tournaments': 1,
            'tournament_wins': 1 if p['rank'] == 1 else 0,
            'match_w': p['wins'],
            'match_t': p['ties'],
            'match_l': p['losses'],
            'total_points': calculate_leagueforge_points(
                p['rank'], p['wins'], tournament_data['n_participants']
            )['points_total'],
            'first_seen': tournament_date,
            'last_seen': tournament_date
        })

        player_row = [
            membership,
            p['name'],
            tcg,
            stats.get('first_seen', tournament_date),
            stats.get('last_seen', tournament_date),
            stats['total_tournaments'],
            stats['tournament_wins'],
            stats['match_w'],
            stats['match_t'],
            stats['match_l'],
            stats['total_points']
        ]

        if key in existing_dict:
            row_idx = existing_dict[key]
            rows_to_update.append({
                'range': f'A{row_idx}:K{row_idx}',
                'values': [player_row]
            })
        else:
            rows_to_add.append(player_row)

    # Batch update
    if rows_to_update:
        api_delay()
        safe_api_call(ws_players.batch_update, rows_to_update, value_input_option='RAW')

    if rows_to_add:
        api_delay()
        safe_api_call(ws_players.append_rows, rows_to_add, value_input_option='RAW')

    print(f"✅ Players: {len(rows_to_update)} aggiornati, {len(rows_to_add)} nuovi")
    return len(rows_to_update), len(rows_to_add)


# =============================================================================
# UPDATE SEASONAL STANDINGS
# =============================================================================

def update_seasonal_standings(sheet, season_id: str, tournament_date: str) -> int:
    """
    Aggiorna la classifica stagionale Seasonal_Standings_PROV.

    Applica lo scarto dinamico:
    - Se stagione < 8 tornei: conta tutto
    - Se stagione >= 8 tornei: conta (totale - 2) migliori
    - Se stagione ARCHIVED: conta tutto (dati storici)

    Args:
        sheet: Google Sheet connesso
        season_id: ID stagione
        tournament_date: Data torneo

    Returns:
        int: Numero giocatori in classifica
    """
    ws_standings = sheet.worksheet("Seasonal_Standings_PROV")
    ws_results = sheet.worksheet("Results")
    ws_tournaments = sheet.worksheet("Tournaments")
    ws_config = sheet.worksheet("Config")

    # Leggi status season dalla Config
    api_delay()
    config_data = safe_api_call(ws_config.get_all_values)
    season_status = None
    for row in config_data[4:]:
        if row and row[0] == season_id:
            season_status = row[4].strip().upper() if len(row) > 4 else ""
            break

    # Conta tornei in stagione
    api_delay()
    all_tournaments = safe_api_call(ws_tournaments.get_all_values)
    season_tournaments = [row for row in all_tournaments[3:] if row and row[1] == season_id]
    total_tournaments = len(season_tournaments)

    print(f"      Tornei stagione: {total_tournaments}")
    print(f"      Status stagione: {season_status or 'ACTIVE'}")

    # Calcola quanti tornei contare
    if season_status == "ARCHIVED":
        max_to_count = total_tournaments
        print(f"      Scarto: NESSUNO (stagione ARCHIVED)")
    elif season_status == "CLOSED" and total_tournaments >= 8:
        max_to_count = total_tournaments - 2
        print(f"      Scarto: Peggiori 2 (conta max {max_to_count})")
    else:
        max_to_count = total_tournaments
        print(f"      Scarto: NESSUNO (stagione ACTIVE o < 8 tornei)")

    # Leggi tutti i risultati della stagione
    api_delay()
    all_results = safe_api_call(ws_results.get_all_values)

    # Raggruppa per giocatore
    player_data = {}
    name_map = {}

    for row in all_results[3:]:
        if not row or len(row) < 9:
            continue

        result_tournament_id = row[1]
        if not result_tournament_id.startswith(season_id):
            continue

        membership = row[2]
        points = float(row[8]) if row[8] else 0
        ranking = int(row[3]) if row[3] else 999
        match_w = int(row[10]) if len(row) > 10 and row[10] else 0
        name = row[9] if len(row) > 9 and row[9] else membership

        name_map[membership] = name

        if membership not in player_data:
            player_data[membership] = {
                'tournaments': [],
                'best_rank': 999
            }

        player_data[membership]['tournaments'].append({
            'points': points,
            'rank': ranking,
            'match_w': match_w
        })
        player_data[membership]['best_rank'] = min(
            player_data[membership]['best_rank'], ranking
        )

    # Calcola classifica finale con scarto
    final_standings = []

    for membership, data in player_data.items():
        tournaments_played = data['tournaments']
        n_played = len(tournaments_played)

        # Ordina per punti e prendi i migliori
        sorted_t = sorted(tournaments_played, key=lambda x: x['points'], reverse=True)
        to_count = min(n_played, max_to_count)
        best_t = sorted_t[:to_count]

        total_points = sum(t['points'] for t in best_t)
        tournament_wins = sum(1 for t in tournaments_played if t['rank'] == 1)
        match_wins = sum(t.get('match_w', 0) for t in tournaments_played)
        top8_count = sum(1 for t in tournaments_played if t['rank'] <= 8)

        final_standings.append({
            'membership': membership,
            'name': name_map.get(membership, membership),
            'total_points': total_points,
            'tournaments_played': n_played,
            'tournaments_counted': to_count,
            'tournament_wins': tournament_wins,
            'match_wins': match_wins,
            'best_rank': data['best_rank'],
            'top8_count': top8_count
        })

    # Ordina per punti
    final_standings.sort(key=lambda x: x['total_points'], reverse=True)

    # Trova righe esistenti di questa stagione
    api_delay()
    existing_standings = safe_api_call(ws_standings.get_all_values)
    rows_to_delete = []
    for i, row in enumerate(existing_standings[3:], start=4):
        if row and row[0] == season_id:
            rows_to_delete.append(i)

    # Prepara righe da scrivere
    rows_to_add = []
    for i, player in enumerate(final_standings, 1):
        rows_to_add.append([
            season_id,
            player['membership'],
            player['name'],
            float(player['total_points']),
            int(player['tournaments_played']),
            int(player['tournaments_counted']),
            int(player['tournament_wins']),
            int(player['match_wins']),
            int(player['best_rank']),
            int(player['top8_count']),
            i  # Rank in season
        ])

    # Trova dove scrivere
    write_start_row = 4
    for i, row in enumerate(existing_standings[3:], start=4):
        if not row or not row[0]:
            break
        if row[0] != season_id:
            write_start_row = i + 1

    if rows_to_delete:
        write_start_row = min(rows_to_delete)

    # Batch write
    if rows_to_add:
        end_row = write_start_row + len(rows_to_add) - 1
        api_delay()
        safe_api_call(ws_standings.update, 
            values=rows_to_add,
            range_name=f"A{write_start_row}:K{end_row}",
            value_input_option='RAW'
        )

        # Pulisci righe vecchie
        if rows_to_delete and max(rows_to_delete) > end_row:
            ws_standings.batch_clear([f"A{end_row+1}:K{max(rows_to_delete)}"])

    print(f"      ✅ Classifica aggiornata: {len(final_standings)} giocatori")
    return len(final_standings)


# =============================================================================
# FINALIZE IMPORT
# =============================================================================

def finalize_import(
    sheet,
    tournament_data: Dict,
    test_mode: bool = False
) -> Dict:
    """
    Finalizza l'import: achievement check + Player_Stats update.

    Args:
        sheet: Google Sheet connesso
        tournament_data: Dati torneo standardizzati
        test_mode: Se True, non scrive

    Returns:
        Dict con statistiche finali
    """
    stats = {
        'achievements_checked': 0,
        'player_stats_updated': 0
    }

    if test_mode:
        print("✅ Finalizzazione: skip (test mode)")
        return stats

    tournament_id = tournament_data['tournament_id']
    season_id = tournament_data['season_id']
    tcg = tournament_data['tcg']
    tournament_date = tournament_data['date']

    # 1. Achievement check
    print("   🎮 Check achievement...")
    try:
        players_dict = {
            p['membership']: p['name']
            for p in tournament_data['participants']
        }

        ach_data = {
            'tournament': [
                tournament_id,
                season_id,
                tournament_date,
                tournament_data['n_participants'],
                tournament_data['n_rounds'],
                ','.join(tournament_data['source_files']),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                tournament_data['winner_name']
            ],
            'players': players_dict
        }

        check_and_unlock_achievements(sheet, ach_data)
        stats['achievements_checked'] = len(players_dict)
    except Exception as e:
        print(f"   ⚠️  Errore achievement (non bloccante): {e}")

    # 2. Player_Stats update
    print("   📊 Aggiornamento Player_Stats...")
    try:
        batch_updates = [
            {
                'membership': p['membership'],
                'tcg': tcg,
                'rank': p['rank'],
                'season_id': season_id,
                'date': tournament_date,
                'name': p['name'],
                'points_total': calculate_leagueforge_points(
                    p['rank'], p['wins'], tournament_data['n_participants']
                )['points_total']
            }
            for p in tournament_data['participants']
        ]
        stats['player_stats_updated'] = batch_update_player_stats(sheet, batch_updates)
        print(f"   ✅ {stats['player_stats_updated']} giocatori aggiornati")
    except Exception as e:
        print(f"   ⚠️  Errore Player_Stats (non bloccante): {e}")

    return stats


# =============================================================================
# SEASON CONFIG
# =============================================================================

def get_season_config(sheet, season_id: str) -> Optional[Dict]:
    """
    Legge configurazione stagione da Config sheet.

    Args:
        sheet: Google Sheet connesso
        season_id: ID stagione

    Returns:
        Dict con configurazione o None se non trovata
    """
    ws_config = sheet.worksheet("Config")
    api_delay()
    config_data = safe_api_call(ws_config.get_all_values)

    for row in config_data[4:]:
        if row and row[0] == season_id:
            return {
                'season_id': row[0],
                'tcg': row[1] if len(row) > 1 else '',
                'name': row[2] if len(row) > 2 else '',
                'start_date': row[3] if len(row) > 3 else '',
                'status': row[4].strip().upper() if len(row) > 4 else 'ACTIVE',
                'tournaments_count': int(row[5]) if len(row) > 5 and row[5] else 0,
                'entry_fee': float(row[6]) if len(row) > 6 and row[6] else 5.0,
                'pack_cost': float(row[7]) if len(row) > 7 and row[7] else 6.0,
            }

    return None


def increment_season_tournament_count(sheet, season_id: str) -> bool:
    """
    Incrementa il contatore tornei di una stagione.

    Args:
        sheet: Google Sheet connesso
        season_id: ID stagione

    Returns:
        bool: True se incrementato
    """
    ws_config = sheet.worksheet("Config")
    api_delay()
    config_data = safe_api_call(ws_config.get_all_values)

    for i, row in enumerate(config_data[4:], start=5):
        if row and row[0] == season_id:
            current_count = int(row[5]) if len(row) > 5 and row[5] else 0
            api_delay()
            safe_api_call(ws_config.update_cell, i, 6, current_count + 1)
            return True

    return False


# =============================================================================
# UTILITY
# =============================================================================

def format_summary(tournament_data: Dict) -> str:
    """
    Formatta un riassunto del torneo per output console.
    """
    lines = [
        "",
        "📊 RIASSUNTO:",
        f"   🏆 Vincitore: {tournament_data['winner_name']}",
        f"   👥 Partecipanti: {tournament_data['n_participants']}",
        f"   🎮 Round: {tournament_data['n_rounds']}",
        "",
        "🎯 TOP 5:"
    ]

    for p in sorted(tournament_data['participants'], key=lambda x: x['rank'])[:5]:
        record = f"{p['wins']}-{p['ties']}-{p['losses']}"
        lines.append(f"   {p['rank']}° {p['name']}: {record}")

    return '\n'.join(lines)
