# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge - Import Controller
=================================================================================

Orchestratore centrale per import tornei TCG.
Coordina validazione, parsing, preview e scrittura per tutti i TCG supportati.

FUNZIONI PRINCIPALI:
- validate(tcg, files) → Valida formato/encoding/struttura
- parse(tcg, season_id, files) → Parse + calcolo W/T/L/punti
- preview(parsed_data) → Genera dati per preview (FASE 3)
- write(sheet, parsed_data, test_mode) → Scrittura su Sheets
- import_tournament(tcg, season_id, files, test_mode) → Import completo

UTILIZZO:
    from import_controller import import_tournament

    result = import_tournament(
        tcg='pokemon',
        season_id='PKM-FS25',
        files={'tdf': '/path/to/file.tdf'},
        test_mode=False
    )

    if result['success']:
        print(f"Import completato: {result['message']}")
    else:
        print(f"Errore: {result['error']}")

=================================================================================
"""

import os
import sys
from typing import Dict, List, Optional, Union
from io import StringIO
import contextlib

# Import moduli specifici TCG
try:
    from import_onepiece import import_tournament as import_onepiece_tournament
    from import_pokemon import parse_tdf, import_to_sheet as import_pokemon_to_sheet
    from import_riftbound import import_tournament as import_riftbound_tournament
    from import_base import connect_sheet
except ImportError as e:
    print(f"❌ Errore import moduli: {e}")
    sys.exit(1)


# =============================================================================
# VALIDATION
# =============================================================================

def validate(tcg: str, files: Dict[str, str]) -> Dict:
    """
    Valida i file prima del parsing.

    Args:
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
        files: Dict con path ai file
               - One Piece: {'rounds': [path1, path2, ...], 'classifica': path}
               - Pokemon: {'tdf': path}
               - Riftbound: {'rounds': [path1, path2, ...]}

    Returns:
        Dict con:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # Check TCG supportato
    if tcg not in ['onepiece', 'pokemon', 'riftbound']:
        result['valid'] = False
        result['errors'].append(f"TCG non supportato: {tcg}")
        return result

    # Validazione specifica per TCG
    if tcg == 'onepiece':
        if 'rounds' not in files or not files['rounds']:
            result['valid'] = False
            result['errors'].append("One Piece: nessun file round fornito")
        if 'classifica' not in files or not files['classifica']:
            result['valid'] = False
            result['errors'].append("One Piece: file ClassificaFinale obbligatorio")

        # Check file esistono
        if 'rounds' in files:
            for f in files['rounds']:
                if not os.path.exists(f):
                    result['valid'] = False
                    result['errors'].append(f"File non trovato: {f}")
        if 'classifica' in files and not os.path.exists(files['classifica']):
            result['valid'] = False
            result['errors'].append(f"File non trovato: {files['classifica']}")

    elif tcg == 'pokemon':
        if 'tdf' not in files or not files['tdf']:
            result['valid'] = False
            result['errors'].append("Pokemon: file TDF obbligatorio")
        elif not os.path.exists(files['tdf']):
            result['valid'] = False
            result['errors'].append(f"File non trovato: {files['tdf']}")

    elif tcg == 'riftbound':
        if 'rounds' not in files or not files['rounds']:
            result['valid'] = False
            result['errors'].append("Riftbound: nessun file round fornito")

        # Check file esistono
        if 'rounds' in files:
            for f in files['rounds']:
                if not os.path.exists(f):
                    result['valid'] = False
                    result['errors'].append(f"File non trovato: {f}")

    return result


# =============================================================================
# PARSE
# =============================================================================

def parse(tcg: str, season_id: str, files: Dict[str, str]) -> Dict:
    """
    Parse i file e calcola dati torneo (NO scrittura su Sheets).

    Args:
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
        season_id: ID stagione (es. 'OP12', 'PKM-FS25', 'RFB01')
        files: Dict con path ai file

    Returns:
        Dict con:
        - success: bool
        - data: Dict con dati parsati (tournament_data)
        - error: str (se success=False)
    """
    try:
        if tcg == 'pokemon':
            # Pokemon: usa parse_tdf
            data = parse_tdf(files['tdf'], season_id)
            return {
                'success': True,
                'data': data,
                'tcg': 'pokemon'
            }

        # OnePlace e Riftbound: per ora non hanno funzione parse separata
        # Useremo import_tournament con test_mode per preview in FASE 3
        return {
            'success': False,
            'error': f"Parse separato non implementato per {tcg} (verrà fatto in FASE 3)"
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Errore parsing: {str(e)}"
        }


# =============================================================================
# PREVIEW
# =============================================================================

def preview(parsed_data: Dict) -> Dict:
    """
    Genera dati per preview tabella (FASE 3).

    Args:
        parsed_data: Dati da parse()

    Returns:
        Dict con:
        - participants: List[Dict] con dati giocatori
        - stats: Dict con statistiche (n_players, winner, date, etc.)
    """
    # TODO: Implementare in FASE 3
    # Per ora restituisce struttura base

    if 'data' not in parsed_data:
        return {'participants': [], 'stats': {}}

    data = parsed_data['data']

    # Pokemon
    if parsed_data.get('tcg') == 'pokemon':
        participants = []
        for result in data.get('results', []):
            participants.append({
                'rank': result[3],
                'name': result[9],
                'membership': result[2],
                'win_points': result[4],
                'wins': result[10] if len(result) > 10 else 0,
                'ties': result[11] if len(result) > 11 else 0,
                'losses': result[12] if len(result) > 12 else 0,
            })

        tournament = data.get('tournament', [])
        stats = {
            'n_participants': tournament[3] if len(tournament) > 3 else 0,
            'winner': tournament[7] if len(tournament) > 7 else '',
            'date': tournament[2] if len(tournament) > 2 else '',
            'tournament_id': tournament[0] if len(tournament) > 0 else ''
        }

        return {
            'participants': participants,
            'stats': stats
        }

    return {'participants': [], 'stats': {}}


# =============================================================================
# WRITE
# =============================================================================

def write(sheet, parsed_data: Dict, test_mode: bool = False) -> Dict:
    """
    Scrive dati su Google Sheets.

    Args:
        sheet: Google Sheet connesso
        parsed_data: Dati da parse()
        test_mode: Se True, simula scrittura

    Returns:
        Dict con:
        - success: bool
        - message: str
        - error: str (se success=False)
    """
    try:
        # Pokemon
        if parsed_data.get('tcg') == 'pokemon':
            import_pokemon_to_sheet(parsed_data['data'], test_mode=test_mode)
            return {
                'success': True,
                'message': f"Import completato{' (TEST MODE)' if test_mode else ''}"
            }

        return {
            'success': False,
            'error': f"Write non implementato per {parsed_data.get('tcg')}"
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Errore scrittura: {str(e)}"
        }


# =============================================================================
# IMPORT TOURNAMENT (funzione comoda per FASE 2)
# =============================================================================

def import_tournament(
    tcg: str,
    season_id: str,
    files: Dict[str, Union[str, List[str]]],
    test_mode: bool = False,
    allow_reimport: bool = False
) -> Dict:
    """
    Import completo di un torneo (validazione + parsing + scrittura).
    Funzione comoda per admin panel FASE 2.

    Args:
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
        season_id: ID stagione (es. 'OP12', 'PKM-FS25', 'RFB01')
        files: Dict con path ai file
               - One Piece: {'rounds': [path1, ...], 'classifica': path}
               - Pokemon: {'tdf': path}
               - Riftbound: {'rounds': [path1, ...]}
        test_mode: Se True, simula import senza scrivere
        allow_reimport: Se True, permette reimport torneo esistente

    Returns:
        Dict con:
        - success: bool
        - message: str
        - output: str (log completo)
        - error: str (se success=False)

    Example:
        result = import_tournament(
            tcg='pokemon',
            season_id='PKM-FS25',
            files={'tdf': '/tmp/tournament.tdf'},
            test_mode=False
        )
    """
    # Cattura output per log
    output_buffer = StringIO()

    try:
        # 1. Validazione
        validation = validate(tcg, files)
        if not validation['valid']:
            return {
                'success': False,
                'error': '; '.join(validation['errors']),
                'output': ''
            }

        # 2. Connetti a Google Sheets
        sheet = connect_sheet()

        # 3. Chiama funzione import specifica per TCG
        with contextlib.redirect_stdout(output_buffer):
            if tcg == 'onepiece':
                import_onepiece_tournament(
                    sheet=sheet,
                    season_id=season_id,
                    round_files=files['rounds'],
                    classifica_file=files['classifica'],
                    test_mode=test_mode,
                    allow_reimport=allow_reimport
                )

            elif tcg == 'pokemon':
                data = parse_tdf(files['tdf'], season_id)
                import_pokemon_to_sheet(data, test_mode=test_mode)

            elif tcg == 'riftbound':
                import_riftbound_tournament(
                    sheet=sheet,
                    season_id=season_id,
                    csv_files=files['rounds'],
                    test_mode=test_mode,
                    allow_reimport=allow_reimport
                )

        output = output_buffer.getvalue()

        return {
            'success': True,
            'message': f'Import {tcg.upper()} completato{"(TEST MODE)" if test_mode else ""}',
            'output': output
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'output': output_buffer.getvalue()
        }


# =============================================================================
# UTILITY
# =============================================================================

def get_tcg_from_season(season_id: str) -> str:
    """
    Estrae TCG type da season_id.

    Args:
        season_id: ID stagione (es. 'OP12', 'PKM-FS25', 'RFB01')

    Returns:
        TCG type: 'onepiece', 'pokemon', 'riftbound'
    """
    if season_id.startswith('OP'):
        return 'onepiece'
    elif season_id.startswith('PKM'):
        return 'pokemon'
    elif season_id.startswith('RFB'):
        return 'riftbound'
    else:
        raise ValueError(f"Season ID non riconosciuto: {season_id}")


# =============================================================================
# DUPLICATE CHECK (80% same players)
# =============================================================================

def check_duplicate_participants(sheet, tournament_id: str, participants: List[Dict]) -> Dict:
    """
    Check se esiste già un torneo con stessi giocatori (>80%).

    Args:
        sheet: Google Sheet connesso
        tournament_id: ID torneo proposto
        participants: Lista giocatori [{membership, name, ...}]

    Returns:
        Dict con:
        - is_duplicate: bool
        - duplicate_type: str ('tournament_id' o 'participants')
        - message: str
        - existing_tournament_id: str (se duplicato)
    """
    from import_base import safe_api_call, api_delay

    try:
        ws_tournaments = sheet.worksheet("Tournaments")
        ws_results = sheet.worksheet("Results")

        # Check 1: Tournament ID già esistente
        api_delay()
        existing_ids = safe_api_call(ws_tournaments.col_values, 1)[3:]  # Skip header

        if tournament_id in existing_ids:
            return {
                'is_duplicate': True,
                'duplicate_type': 'tournament_id',
                'message': f'Torneo {tournament_id} già esistente!',
                'existing_tournament_id': tournament_id
            }

        # Check 2: Stessa data + >80% stessi giocatori
        # Estrai data da tournament_id (formato: SEASON_YYYYMMDD)
        if '_' in tournament_id:
            date_part = tournament_id.split('_')[1]

            # Leggi tutti i tornei della stessa data
            api_delay()
            all_tournaments = safe_api_call(ws_tournaments.get_all_values)[3:]

            for t_row in all_tournaments:
                if not t_row or len(t_row) < 3:
                    continue

                existing_tid = t_row[0]
                existing_date_raw = t_row[2]  # YYYY-MM-DD

                # Converti existing_date to YYYYMMDD
                existing_date = existing_date_raw.replace('-', '')

                if existing_date == date_part:
                    # Stesso giorno! Check partecipanti
                    api_delay()
                    all_results = safe_api_call(ws_results.get_all_values)[3:]

                    existing_participants = set()
                    for r_row in all_results:
                        if r_row and len(r_row) > 2 and r_row[1] == existing_tid:
                            existing_participants.add(r_row[2])  # membership

                    new_participants = set(p.get('membership', p.get('Membership Number', '')) for p in participants)

                    if existing_participants and new_participants:
                        overlap = len(existing_participants & new_participants)
                        total = len(new_participants)
                        overlap_pct = (overlap / total * 100) if total > 0 else 0

                        if overlap_pct >= 80:
                            return {
                                'is_duplicate': True,
                                'duplicate_type': 'participants',
                                'message': f'Rilevato torneo con {overlap_pct:.0f}% stessi giocatori (data: {existing_date_raw})',
                                'existing_tournament_id': existing_tid,
                                'overlap_percent': overlap_pct
                            }

        # Nessun duplicato rilevato
        return {
            'is_duplicate': False,
            'duplicate_type': None,
            'message': 'Nessun duplicato rilevato'
        }

    except Exception as e:
        return {
            'is_duplicate': False,
            'duplicate_type': None,
            'message': f'Errore check duplicati: {str(e)}'
        }


# =============================================================================
# VALIDATE ROUND ORDER (points crescenti)
# =============================================================================

def validate_round_order(round_data: List[Dict]) -> Dict:
    """
    Valida che i punti siano crescenti tra round (One Piece/Riftbound).

    Args:
        round_data: Lista di dict con dati round
                    [{'round': 1, 'max_points': 3}, {'round': 2, 'max_points': 6}, ...]

    Returns:
        Dict con:
        - valid: bool
        - errors: List[str]
    """
    result = {
        'valid': True,
        'errors': []
    }

    if len(round_data) < 2:
        # Un solo round, niente da validare
        return result

    for i in range(1, len(round_data)):
        prev_round = round_data[i-1]
        curr_round = round_data[i]

        prev_max = prev_round.get('max_points', 0)
        curr_max = curr_round.get('max_points', 0)

        if curr_max <= prev_max:
            result['valid'] = False
            result['errors'].append(
                f"Ordine round errato: Round {curr_round['round']} "
                f"ha max_points={curr_max} ma Round {prev_round['round']} "
                f"ha max_points={prev_max}. I punti devono crescere!"
            )

    return result
