# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge - Season Manager
=================================================================================

Gestione stagioni TCG: creazione, chiusura, lista.

FUNZIONI:
- create_season(): Crea nuova stagione (OP/PKM/RFB)
- close_season(): Chiude stagione + ricalcolo con scarto
- get_seasons(): Lista stagioni filtrate
- validate_season_id(): Valida formato ID stagione

STATI STAGIONE:
- ACTIVE: Stagione in corso (no scarto, achievement SÌ)
- CLOSED: Stagione terminata (scarto 2 peggiori se ≥8 tornei, achievement SÌ)
- ARCHIVED: Dati storici (no scarto, achievement NO)

=================================================================================
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from import_base import safe_api_call, api_delay, update_seasonal_standings


# =============================================================================
# SEASON VALIDATION
# =============================================================================

def validate_season_id(season_id: str, tcg: str) -> Dict:
    """
    Valida formato season_id per TCG specifico.

    Args:
        season_id: ID stagione proposto
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')

    Returns:
        Dict con:
        - valid: bool
        - error: str (se non valido)
        - normalized_id: str (ID normalizzato)
    """
    season_id = season_id.strip()

    if tcg == 'onepiece':
        # Formato: OP{numero} (es. OP12, OP13)
        if not re.match(r'^OP\d+$', season_id):
            return {
                'valid': False,
                'error': 'Formato One Piece: OP{numero} (es. OP12)'
            }
        return {'valid': True, 'normalized_id': season_id}

    elif tcg == 'riftbound':
        # Formato: RFB{numero} (es. RFB01, RFB02)
        if not re.match(r'^RFB\d+$', season_id):
            return {
                'valid': False,
                'error': 'Formato Riftbound: RFB{numero} (es. RFB01)'
            }
        return {'valid': True, 'normalized_id': season_id}

    elif tcg == 'pokemon':
        # Formato: PKM-{iniziali}{anno} (es. PKM-FS25)
        if not re.match(r'^PKM-[A-Z]{2,4}\d{2}$', season_id):
            return {
                'valid': False,
                'error': 'Formato Pokémon: PKM-{INIZIALI}{ANNO} (es. PKM-FS25)'
            }
        return {'valid': True, 'normalized_id': season_id}

    return {'valid': False, 'error': 'TCG non riconosciuto'}


def generate_season_name(season_id: str, tcg: str, custom_name: str = None) -> str:
    """
    Genera nome descrittivo automatico per stagione.

    Args:
        season_id: ID stagione (es. OP12, PKM-FS25)
        tcg: TCG type
        custom_name: Nome custom per Pokemon (es. "Fiamme Spettrali 2025")

    Returns:
        Nome descrittivo (es. "One Piece - Stagione 12")
    """
    if custom_name:
        return custom_name

    if tcg == 'onepiece':
        # Estrai numero da OP12 -> "One Piece - Stagione 12"
        num = ''.join(c for c in season_id if c.isdigit())
        return f"One Piece - Stagione {num}"

    elif tcg == 'riftbound':
        # Estrai numero da RFB01 -> "Riftbound - Stagione 1"
        num = ''.join(c for c in season_id if c.isdigit())
        return f"Riftbound - Stagione {int(num)}"

    elif tcg == 'pokemon':
        # PKM-FS25 -> "Pokémon - FS25"
        return f"Pokémon - {season_id.replace('PKM-', '')}"

    return season_id


# =============================================================================
# GET SEASONS
# =============================================================================

def get_seasons(sheet, tcg: str = None, include_archived: bool = False) -> List[Dict]:
    """
    Recupera lista stagioni dal Google Sheet.

    Args:
        sheet: Google Sheet connesso
        tcg: Filtra per TCG ('onepiece', 'pokemon', 'riftbound') o None per tutte
        include_archived: Se False, nasconde stagioni ARCHIVED

    Returns:
        Lista dict [{id, name, tcg, status, start_date, tournaments_count, ...}]
    """
    ws_config = sheet.worksheet("Config")
    api_delay()
    config_data = safe_api_call(ws_config.get_all_values)

    seasons = []

    # Skip header (righe 1-4)
    for row in config_data[4:]:
        if not row or not row[0]:
            continue

        season_id = row[0]
        season_tcg = row[1] if len(row) > 1 else ''
        season_name = row[2] if len(row) > 2 else season_id
        start_date = row[3] if len(row) > 3 else ''
        status = row[4].strip().upper() if len(row) > 4 else 'ACTIVE'
        tournaments_count = int(row[5]) if len(row) > 5 and row[5] else 0
        entry_fee = float(row[6]) if len(row) > 6 and row[6] else 5.0
        pack_cost = float(row[7]) if len(row) > 7 and row[7] else 6.0

        # Filtra per TCG
        if tcg:
            tcg_prefix = {
                'onepiece': 'OP',
                'pokemon': 'PKM',
                'riftbound': 'RFB'
            }.get(tcg, '')

            if not season_id.startswith(tcg_prefix):
                continue

        # Filtra ARCHIVED
        if not include_archived and status == 'ARCHIVED':
            continue

        seasons.append({
            'id': season_id,
            'name': season_name,
            'tcg': season_tcg,
            'status': status,
            'start_date': start_date,
            'tournaments_count': tournaments_count,
            'entry_fee': entry_fee,
            'pack_cost': pack_cost
        })

    return seasons


# =============================================================================
# CREATE SEASON
# =============================================================================

def create_season(
    sheet,
    tcg: str,
    season_id: str,
    custom_name: str = None,
    entry_fee: float = 5.0,
    pack_cost: float = 6.0
) -> Dict:
    """
    Crea nuova stagione nel Google Sheet.

    Args:
        sheet: Google Sheet connesso
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
        season_id: ID stagione (es. OP13, PKM-FS25, RFB02)
        custom_name: Nome custom (opzionale, per Pokemon)
        entry_fee: Quota iscrizione torneo (default 5.0)
        pack_cost: Costo busta premio (default 6.0)

    Returns:
        Dict con:
        - success: bool
        - message: str
        - season_id: str (se success)
    """
    try:
        # 1. Valida season_id
        validation = validate_season_id(season_id, tcg)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error']
            }

        season_id = validation['normalized_id']

        # 2. Check se esiste già
        existing_seasons = get_seasons(sheet, include_archived=True)
        if any(s['id'] == season_id for s in existing_seasons):
            return {
                'success': False,
                'error': f'Stagione {season_id} già esistente!'
            }

        # 3. Genera nome
        season_name = generate_season_name(season_id, tcg, custom_name)

        # 4. Scrivi in Config sheet
        ws_config = sheet.worksheet("Config")

        # TCG full name
        tcg_full = {
            'onepiece': 'One Piece',
            'pokemon': 'Pokemon',
            'riftbound': 'Riftbound'
        }.get(tcg, tcg.upper())

        season_row = [
            season_id,              # Season_ID
            tcg_full,               # TCG
            season_name,            # Season_Name
            datetime.now().strftime('%Y-%m-%d'),  # Start_Date
            'ACTIVE',               # Status
            0,                      # Tournaments_Count
            entry_fee,              # Entry_Fee
            pack_cost               # Pack_Cost
        ]

        api_delay()
        safe_api_call(ws_config.append_row, season_row, value_input_option='RAW')

        return {
            'success': True,
            'message': f'Stagione {season_id} creata con successo!',
            'season_id': season_id,
            'season_name': season_name
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Errore creazione stagione: {str(e)}'
        }


# =============================================================================
# CLOSE SEASON
# =============================================================================

def close_season(sheet, season_id: str) -> Dict:
    """
    Chiude una stagione ACTIVE → CLOSED.
    Ricalcola classifica con scarto 2 peggiori se ≥8 tornei.

    Args:
        sheet: Google Sheet connesso
        season_id: ID stagione da chiudere

    Returns:
        Dict con:
        - success: bool
        - message: str
    """
    try:
        ws_config = sheet.worksheet("Config")

        # 1. Find season in Config
        api_delay()
        config_data = safe_api_call(ws_config.get_all_values)

        season_row_index = None
        season_status = None
        tournaments_count = 0

        for i, row in enumerate(config_data[4:], start=5):  # Start from row 5 (after header)
            if row and row[0] == season_id:
                season_row_index = i
                season_status = row[4].strip().upper() if len(row) > 4 else 'ACTIVE'
                tournaments_count = int(row[5]) if len(row) > 5 and row[5] else 0
                break

        if not season_row_index:
            return {
                'success': False,
                'error': f'Stagione {season_id} non trovata'
            }

        # 2. Check status
        if season_status != 'ACTIVE':
            return {
                'success': False,
                'error': f'Stagione {season_id} non è ACTIVE (status: {season_status})'
            }

        # 3. Update status to CLOSED
        api_delay()
        safe_api_call(ws_config.update_cell, season_row_index, 5, 'CLOSED')  # Col 5 = Status

        # 4. Ricalcola classifica (con scarto se ≥8 tornei)
        print(f"   🔄 Ricalcolo classifica con scarto...")
        api_delay()
        update_seasonal_standings(sheet, season_id, datetime.now().strftime('%Y-%m-%d'))

        message = f'Stagione {season_id} chiusa con successo!'
        if tournaments_count >= 8:
            message += f' Applicato scarto 2 peggiori tornei ({tournaments_count} tornei totali).'
        else:
            message += f' Nessuno scarto applicato ({tournaments_count} tornei < 8).'

        return {
            'success': True,
            'message': message,
            'tournaments_count': tournaments_count
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Errore chiusura stagione: {str(e)}'
        }


# =============================================================================
# UTILITY
# =============================================================================

def suggest_next_season_id(sheet, tcg: str) -> str:
    """
    Suggerisce prossimo season_id basato sulle stagioni esistenti.

    Args:
        sheet: Google Sheet connesso
        tcg: TCG type

    Returns:
        Suggestion season_id (es. "OP14" se ultimo è OP13)
    """
    seasons = get_seasons(sheet, tcg=tcg, include_archived=True)

    if tcg in ['onepiece', 'riftbound']:
        # Estrai numeri
        numbers = []
        for s in seasons:
            num_str = ''.join(c for c in s['id'] if c.isdigit())
            if num_str:
                numbers.append(int(num_str))

        if numbers:
            next_num = max(numbers) + 1
            prefix = 'OP' if tcg == 'onepiece' else 'RFB'
            return f"{prefix}{next_num:02d}" if tcg == 'riftbound' else f"{prefix}{next_num}"

        # Default
        return 'OP01' if tcg == 'onepiece' else 'RFB01'

    elif tcg == 'pokemon':
        # Pokemon: chiedi all'utente (nessun suggestion automatico)
        return ''

    return ''
