# -*- coding: utf-8 -*-
from api_utils import safe_api_call
import time

API_DELAY_MS = 300
def api_delay():
    time.sleep(API_DELAY_MS / 1000.0)
"""
Player Stats - Funzioni CRUD per Player_Stats sheet.

Questo modulo fornisce accesso veloce alle statistiche pre-calcolate,
evitando di ricalcolare tutto da Results ad ogni richiesta.

Pattern CQRS-like:
  - Results = write model (dati grezzi)
  - Player_Stats = read model (aggregati)
"""

from datetime import datetime
from sheet_utils import COL_PLAYER_STATS, safe_get, safe_int


def get_player_stats(sheet, membership: str, tcg: str = None) -> dict:
    """
    Legge stats pre-calcolate per un giocatore.

    Args:
        sheet: Google Sheet connesso
        membership: Membership number
        tcg: TCG specifico (opzionale, se None ritorna primo match)

    Returns:
        Dict con stats o None se non trovato
    """
    try:
        ws = sheet.worksheet("Player_Stats")
        data = safe_api_call(ws.get_all_values)[3:]  # Skip header
    except Exception:
        return None

    for row in data:
        row_membership = safe_get(row, COL_PLAYER_STATS, 'membership')
        row_tcg = safe_get(row, COL_PLAYER_STATS, 'tcg')

        if row_membership == membership:
            if tcg is None or row_tcg == tcg:
                return {
                    'membership': row_membership,
                    'name': safe_get(row, COL_PLAYER_STATS, 'name', ''),
                    'tcg': row_tcg,
                    'total_tournaments': safe_int(row, COL_PLAYER_STATS, 'total_tournaments', 0),
                    'total_wins': safe_int(row, COL_PLAYER_STATS, 'total_wins', 0),
                    'current_streak': safe_int(row, COL_PLAYER_STATS, 'current_streak', 0),
                    'best_streak': safe_int(row, COL_PLAYER_STATS, 'best_streak', 0),
                    'top8_count': safe_int(row, COL_PLAYER_STATS, 'top8_count', 0),
                    'last_rank': safe_int(row, COL_PLAYER_STATS, 'last_rank', 999),
                    'last_date': safe_get(row, COL_PLAYER_STATS, 'last_date', ''),
                    'seasons_count': safe_int(row, COL_PLAYER_STATS, 'seasons_count', 0),
                    'updated_at': safe_get(row, COL_PLAYER_STATS, 'updated_at', '')
                }

    return None


def get_all_player_stats(sheet, tcg: str = None) -> list:
    """
    Legge tutte le stats, opzionalmente filtrate per TCG.

    Args:
        sheet: Google Sheet connesso
        tcg: Filtra per TCG (opzionale)

    Returns:
        Lista di dict con stats
    """
    try:
        ws = sheet.worksheet("Player_Stats")
        data = safe_api_call(ws.get_all_values)[3:]  # Skip header
    except Exception:
        return []

    results = []
    for row in data:
        row_tcg = safe_get(row, COL_PLAYER_STATS, 'tcg')

        if tcg and row_tcg != tcg:
            continue

        results.append({
            'membership': safe_get(row, COL_PLAYER_STATS, 'membership'),
            'name': safe_get(row, COL_PLAYER_STATS, 'name', ''),
            'tcg': row_tcg,
            'total_tournaments': safe_int(row, COL_PLAYER_STATS, 'total_tournaments', 0),
            'total_wins': safe_int(row, COL_PLAYER_STATS, 'total_wins', 0),
            'current_streak': safe_int(row, COL_PLAYER_STATS, 'current_streak', 0),
            'best_streak': safe_int(row, COL_PLAYER_STATS, 'best_streak', 0),
            'top8_count': safe_int(row, COL_PLAYER_STATS, 'top8_count', 0),
            'last_rank': safe_int(row, COL_PLAYER_STATS, 'last_rank', 999),
            'last_date': safe_get(row, COL_PLAYER_STATS, 'last_date', ''),
            'seasons_count': safe_int(row, COL_PLAYER_STATS, 'seasons_count', 0),
        })

    return results


def update_player_stats_after_tournament(sheet, membership: str, tcg: str,
                                         rank: int, season_id: str,
                                         tournament_date: str = None,
                                         name: str = None):
    """
    Aggiorna stats di un giocatore DOPO un torneo (delta update).

    Questa funzione è chiamata dagli import scripts per aggiornare
    incrementalmente senza ricalcolare tutto.

    Args:
        sheet: Google Sheet connesso
        membership: Membership number
        tcg: Codice TCG (OP, RB, PKM)
        rank: Piazzamento nel torneo
        season_id: ID stagione
        tournament_date: Data torneo (YYYY-MM-DD)
        name: Nome giocatore (per nuovi record)

    Returns:
        bool: True se aggiornato, False se errore
    """
    try:
        ws = sheet.worksheet("Player_Stats")
        data = safe_api_call(ws.get_all_values)
        header_rows = 3

        # Trova riga esistente
        row_idx = None
        for i, row in enumerate(data[header_rows:], start=header_rows + 1):
            if (safe_get(row, COL_PLAYER_STATS, 'membership') == membership and
                    safe_get(row, COL_PLAYER_STATS, 'tcg') == tcg):
                row_idx = i
                break

        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        if row_idx:
            # Aggiorna riga esistente
            current = data[row_idx - 1]

            # Leggi valori attuali
            total_t = safe_int(current, COL_PLAYER_STATS, 'total_tournaments', 0) + 1
            total_w = safe_int(current, COL_PLAYER_STATS, 'total_wins', 0)
            curr_streak = safe_int(current, COL_PLAYER_STATS, 'current_streak', 0)
            best_streak = safe_int(current, COL_PLAYER_STATS, 'best_streak', 0)
            top8 = safe_int(current, COL_PLAYER_STATS, 'top8_count', 0)
            seasons = safe_int(current, COL_PLAYER_STATS, 'seasons_count', 0)
            player_name = name or safe_get(current, COL_PLAYER_STATS, 'name', '')

            # Calcola nuovi valori
            if rank == 1:
                total_w += 1
            if rank <= 8:
                top8 += 1
                curr_streak += 1
                best_streak = max(best_streak, curr_streak)
            else:
                curr_streak = 0

            # Aggiorna riga
            new_row = [
                membership,
                player_name,
                tcg,
                total_t,
                total_w,
                curr_streak,
                best_streak,
                top8,
                rank if rank < 999 else '',
                tournament_date or '',
                seasons,  # Non aggiorniamo qui, serve check stagione
                now
            ]

            safe_api_call(ws.update, f'A{row_idx}:L{row_idx}', [new_row], value_input_option='USER_ENTERED')

        else:
            # Nuovo giocatore - append
            is_top8 = rank <= 8
            new_row = [
                membership,
                name or '',
                tcg,
                1,                    # total_tournaments
                1 if rank == 1 else 0,  # total_wins
                1 if is_top8 else 0,    # current_streak
                1 if is_top8 else 0,    # best_streak
                1 if is_top8 else 0,    # top8_count
                rank if rank < 999 else '',
                tournament_date or '',
                1,                    # seasons_count
                now
            ]

            # Trova ultima riga con dati
            last_row = len(data) + 1
            safe_api_call(ws.update, f'A{last_row}:L{last_row}', [new_row], value_input_option='USER_ENTERED')

        return True

    except Exception as e:
        print(f"⚠️ Errore update_player_stats: {e}")
        return False


def batch_update_player_stats(sheet, updates: list):
    """
    Aggiorna multipli giocatori in batch VERO (1 read + 1 write).

    Args:
        sheet: Google Sheet connesso
        updates: Lista di dict con keys: membership, tcg, rank, season_id, name, date

    Returns:
        int: Numero di aggiornamenti riusciti
    """
    if not updates:
        return 0

    try:
        ws = sheet.worksheet("Player_Stats")
        api_delay()
        data = safe_api_call(ws.get_all_values)
        header_rows = 3
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Mappa membership+tcg -> row_idx
        existing = {}
        for i, row in enumerate(data[header_rows:], start=header_rows + 1):
            key = (safe_get(row, COL_PLAYER_STATS, 'membership'),
                   safe_get(row, COL_PLAYER_STATS, 'tcg'))
            existing[key] = (i, row)

        # Prepara batch updates
        batch_data = []
        new_rows = []

        for u in updates:
            membership = u.get('membership')
            tcg = u.get('tcg')
            rank = u.get('rank', 999)
            date = u.get('date', '')
            name = u.get('name', '')
            key = (membership, tcg)

            if key in existing:
                # Update esistente
                row_idx, current = existing[key]
                total_t = safe_int(current, COL_PLAYER_STATS, 'total_tournaments', 0) + 1
                total_w = safe_int(current, COL_PLAYER_STATS, 'total_wins', 0)
                curr_streak = safe_int(current, COL_PLAYER_STATS, 'current_streak', 0)
                best_streak = safe_int(current, COL_PLAYER_STATS, 'best_streak', 0)
                top8 = safe_int(current, COL_PLAYER_STATS, 'top8_count', 0)
                seasons = safe_int(current, COL_PLAYER_STATS, 'seasons_count', 0)
                player_name = name or safe_get(current, COL_PLAYER_STATS, 'name', '')

                if rank == 1:
                    total_w += 1
                if rank <= 8:
                    top8 += 1
                    curr_streak += 1
                    best_streak = max(best_streak, curr_streak)
                else:
                    curr_streak = 0

                new_row = [membership, player_name, tcg, total_t, total_w, curr_streak,
                          best_streak, top8, rank if rank < 999 else '', date, seasons, now]
                batch_data.append({'range': f'A{row_idx}:L{row_idx}', 'values': [new_row]})
            else:
                # Nuovo giocatore
                is_top8 = rank <= 8
                new_row = [membership, name, tcg, 1, 1 if rank == 1 else 0,
                          1 if is_top8 else 0, 1 if is_top8 else 0, 1 if is_top8 else 0,
                          rank if rank < 999 else '', date, 1, now]
                new_rows.append(new_row)

        # Batch update esistenti
        if batch_data:
            api_delay()
            safe_api_call(ws.batch_update, batch_data, value_input_option='USER_ENTERED')

        # Append nuovi
        if new_rows:
            api_delay()
            safe_api_call(ws.append_rows, new_rows, value_input_option='USER_ENTERED')

        return len(updates)

    except Exception as e:
        print(f"⚠️ Errore batch_update_player_stats: {e}")
        return 0
