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

        elif tcg == 'riftbound':
            # Riftbound: parse CSV rounds
            from import_riftbound import parse_csv_rounds, extract_date_from_filename, generate_tournament_id
            from import_base import create_participant, create_tournament_data
            import re

            round_files = files.get('rounds', [])
            if not round_files:
                return {
                    'success': False,
                    'error': 'Nessun file round fornito per Riftbound'
                }

            # Parse CSV files
            players_list, matches_list = parse_csv_rounds(round_files)

            # Metadata
            tournament_date = extract_date_from_filename(round_files[0])
            tournament_id = generate_tournament_id(season_id, tournament_date)

            # Converti in formato standardizzato (Dict completi)
            participants = []
            for p in players_list:
                participant = create_participant(
                    membership=p['user_id'],
                    name=p['name'],
                    rank=p['rank'],
                    wins=p['wins'],
                    ties=p['ties'],
                    losses=p['losses'],
                    win_points=p['win_points'],
                    omw=p.get('omw', 0)
                )
                participants.append(participant)

            # Create tournament data (participants già hanno TUTTE le chiavi)
            source_files = [f.split('/')[-1] for f in round_files]
            tcg_code = ''.join(c for c in season_id if c.isalpha()).upper()

            tournament_data = create_tournament_data(
                tournament_id=tournament_id,
                season_id=season_id,
                date=tournament_date,
                participants=participants,  # Usa participants completi!
                tcg=tcg_code,
                source_files=source_files,
                winner_name=players_list[0]['name'] if players_list else None
            )

            data = {
                'tournament_data': tournament_data,  # Dict completo con participants dentro
                'matches': matches_list
            }

            return {
                'success': True,
                'data': data,
                'tcg': 'riftbound'
            }

        elif tcg == 'onepiece':
            # One Piece: parse CSV rounds + classifica
            from import_onepiece import (
                parse_round_files,
                parse_classifica_finale,
                merge_tournament_data,
                extract_date_from_filename,
                generate_tournament_id
            )
            from import_base import create_tournament_data

            round_files = files.get('rounds', [])
            classifica_file = files.get('classifica')

            if not round_files or not classifica_file:
                return {
                    'success': False,
                    'error': 'File mancanti per One Piece (rounds o classifica)'
                }

            # Parse files
            progression = parse_round_files(round_files)
            final_data = parse_classifica_finale(classifica_file)

            # Merge data
            participants_list = merge_tournament_data(progression, final_data)

            # Metadata
            tournament_date = extract_date_from_filename(round_files[0])
            tournament_id = generate_tournament_id(season_id, tournament_date)

            # Create tournament data
            source_files = [f.split('/')[-1] for f in round_files] + [classifica_file.split('/')[-1]]
            tcg_code = 'OP'

            tournament_data = create_tournament_data(
                tournament_id=tournament_id,
                season_id=season_id,
                date=tournament_date,
                participants=participants_list,
                tcg=tcg_code,
                source_files=source_files,
                winner_name=participants_list[0]['name'] if participants_list else None
            )

            # tournament_data già contiene i participants dentro
            # (create_tournament_data li ha aggiunti)

            data = {
                'tournament_data': tournament_data  # Dict completo con participants dentro
            }

            return {
                'success': True,
                'data': data,
                'tcg': 'onepiece'
            }

        return {
            'success': False,
            'error': f"TCG non supportato: {tcg}"
        }

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Errore parsing: {str(e)}\n{traceback.format_exc()}"
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
    if 'data' not in parsed_data:
        return {'participants': [], 'stats': {}}

    data = parsed_data['data']
    tcg = parsed_data.get('tcg')

    # Pokemon
    if tcg == 'pokemon':
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

    # Riftbound
    elif tcg == 'riftbound':
        tournament_data = data.get('tournament_data', {})
        participants_raw = tournament_data.get('participants', [])

        participants = []
        for p in participants_raw:
            participants.append({
                'rank': p.get('rank', 0),
                'name': p.get('name', ''),
                'membership': p.get('membership', ''),
                'win_points': p.get('win_points', 0),
                'wins': p.get('wins', 0),
                'ties': p.get('ties', 0),
                'losses': p.get('losses', 0),
                'omw': p.get('omw', 0)
            })

        stats = {
            'n_participants': tournament_data.get('n_participants', 0),
            'winner': tournament_data.get('winner_name', ''),
            'date': tournament_data.get('date', ''),
            'tournament_id': tournament_data.get('tournament_id', ''),
            'n_rounds': tournament_data.get('n_rounds', 0)
        }

        return {
            'participants': participants,
            'stats': stats
        }

    # One Piece
    elif tcg == 'onepiece':
        tournament_data = data.get('tournament_data', {})
        participants_raw = tournament_data.get('participants', [])

        participants = []
        for p in participants_raw:
            participants.append({
                'rank': p.get('rank', 0),
                'name': p.get('name', ''),
                'membership': p.get('membership', ''),
                'win_points': p.get('win_points', 0),
                'wins': p.get('wins', 0),
                'ties': p.get('ties', 0),
                'losses': p.get('losses', 0),
                'omw': p.get('omw', 0)
            })

        stats = {
            'n_participants': tournament_data.get('n_participants', 0),
            'winner': tournament_data.get('winner_name', ''),
            'date': tournament_data.get('date', ''),
            'tournament_id': tournament_data.get('tournament_id', ''),
            'n_rounds': tournament_data.get('n_rounds', 0)
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
        tcg = parsed_data.get('tcg')
        data = parsed_data.get('data', {})

        # Pokemon
        if tcg == 'pokemon':
            import_pokemon_to_sheet(data, test_mode=test_mode)
            return {
                'success': True,
                'message': f"Import Pokemon completato{' (TEST MODE)' if test_mode else ''}"
            }

        # Riftbound
        elif tcg == 'riftbound':
            from import_base import write_tournament_to_sheet, write_results_to_sheet
            from import_riftbound import write_matches_to_sheet

            tournament_data = data.get('tournament_data')
            matches = data.get('matches', [])
            tournament_id = tournament_data.get('tournament_id') if tournament_data else ''

            if not test_mode:
                # Scrivi Tournament (passa Dict completo)
                write_tournament_to_sheet(sheet, tournament_data, test_mode=False)

                # Scrivi Results (usa participants dentro tournament_data)
                write_results_to_sheet(sheet, tournament_data, test_mode=False)

                # Scrivi Matches (specifico Riftbound)
                write_matches_to_sheet(sheet, tournament_id, matches, test_mode=False)

            return {
                'success': True,
                'message': f"Import Riftbound completato{' (TEST MODE)' if test_mode else ''}"
            }

        # One Piece
        elif tcg == 'onepiece':
            from import_base import write_tournament_to_sheet, write_results_to_sheet

            tournament_data = data.get('tournament_data')

            if not test_mode:
                # Scrivi Tournament (passa Dict completo)
                write_tournament_to_sheet(sheet, tournament_data, test_mode=False)

                # Scrivi Results (usa participants dentro tournament_data)
                write_results_to_sheet(sheet, tournament_data, test_mode=False)

                # Note: One Piece non ha tabella Matches separata in questa versione

            return {
                'success': True,
                'message': f"Import One Piece completato{' (TEST MODE)' if test_mode else ''}"
            }

        return {
            'success': False,
            'error': f"Write non implementato per {tcg}"
        }

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Errore scrittura: {str(e)}\n{traceback.format_exc()}"
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
                    round_files=files['rounds'],
                    season_id=season_id,
                    test_mode=test_mode,
                    reimport=allow_reimport
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


# =============================================================================
# IMPORT CON PROGRESS TRACKING (FASE 5)
# =============================================================================

def import_with_progress(
    tracker_id: str,
    tcg: str,
    season_id: str,
    files: Dict[str, Union[str, List[str]]],
    test_mode: bool = False,
    allow_overwrite: bool = False
):
    """
    Esegue import con progress tracking real-time.
    Questa funzione viene eseguita in background e aggiorna un ProgressTracker.

    Args:
        tracker_id: ID del ProgressTracker da aggiornare
        tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
        season_id: ID stagione
        files: Dict con path ai file
        test_mode: Se True, simula import
        allow_overwrite: Se True, sovrascrive dati esistenti

    Returns:
        None (aggiorna il tracker)
    """
    from progress_tracker import get_tracker
    from import_base import delete_existing_tournament

    tracker = get_tracker(tracker_id)
    if not tracker:
        return

    try:
        tracker.log("🔍 Validazione file...")
        tracker.update_progress(5, "Validazione file")

        # 1. Validazione
        validation = validate(tcg, files)
        if not validation['valid']:
            error_msg = '; '.join(validation['errors'])
            tracker.log(f"❌ Errore validazione: {error_msg}", 'error')
            tracker.complete(success=False, message=error_msg)
            return

        tracker.log("✓ Validazione completata", 'success')
        tracker.update_progress(10, "File validati")

        # 2. Connessione a Google Sheets
        tracker.log("🔗 Connessione a Google Sheets...")
        tracker.update_progress(15, "Connessione Google Sheets")

        sheet = connect_sheet()
        tracker.log("✓ Connesso a Google Sheets", 'success')
        tracker.update_progress(20, "Connesso")

        # 3. Parsing
        tracker.log(f"📋 Parsing file {tcg.upper()}...")
        tracker.update_progress(25, "Parsing dati")

        parsed_result = parse(tcg, season_id, files)
        if not parsed_result['success']:
            error_msg = parsed_result.get('error', 'Errore parsing')
            tracker.log(f"❌ {error_msg}", 'error')
            tracker.complete(success=False, message=error_msg)
            return

        tracker.log("✓ Parsing completato", 'success')
        tracker.update_progress(40, "Dati parsati")

        # 4. Se overwrite, cancella dati esistenti
        if allow_overwrite:
            tournament_id = parsed_result['data']['tournament'][0]
            tracker.log(f"🗑️ Eliminazione dati esistenti per {tournament_id}...")
            tracker.update_progress(45, "Eliminazione vecchi dati")

            delete_existing_tournament(sheet, tournament_id)
            tracker.log("✓ Dati vecchi eliminati", 'success')

        tracker.update_progress(50, "Inizio scrittura")

        # 5. Scrittura su Sheets
        tracker.log("💾 Scrittura su Google Sheets...")
        tracker.log("   → Scrittura Tournaments...", 'info')
        tracker.update_progress(55, "Scrittura Tournaments")

        # Call appropriata funzione import con output capture
        with contextlib.redirect_stdout(StringIO()) as output:
            if tcg == 'pokemon':
                # Per Pokemon usiamo import_pokemon_to_sheet
                tracker.log("   → Scrittura Results...", 'info')
                tracker.update_progress(60, "Scrittura Results")

                import_pokemon_to_sheet(parsed_result['data'], test_mode=test_mode)

                tracker.log("   → Scrittura Matches...", 'info')
                tracker.update_progress(70, "Scrittura Matches")

            elif tcg == 'onepiece':
                import_onepiece_tournament(
                    sheet=sheet,
                    season_id=season_id,
                    round_files=files['rounds'],
                    classifica_file=files['classifica'],
                    test_mode=test_mode
                )

            elif tcg == 'riftbound':
                result = import_riftbound_tournament(
                    round_files=files['rounds'],
                    season_id=season_id,
                    test_mode=test_mode
                )

        tracker.log("✓ Scrittura completata", 'success')
        tracker.update_progress(80, "Dati scritti")

        # 6. Aggiornamento derivati
        tracker.log("🔄 Aggiornamento Players e Standings...")
        tracker.update_progress(85, "Aggiornamento Players")

        from import_base import update_players, update_seasonal_standings, batch_update_player_stats
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')

        # Per Riftbound, il result contiene già tournament_data
        if tcg == 'riftbound':
            tracker.log("   → update_players()...", 'info')
            # update_players già chiamato dentro import_riftbound_tournament
            tracker.log("   ✓ Players aggiornati", 'success')
        else:
            tracker.log("   → update_players()...", 'info')
            update_players(sheet, today)

        if tcg == 'riftbound':
            tracker.log("   → update_seasonal_standings()...", 'info')
            # update_seasonal_standings già chiamato dentro import_riftbound_tournament
            tracker.log("   ✓ Standings aggiornati", 'success')
        else:
            tracker.log("   → update_seasonal_standings()...", 'info')
            tracker.update_progress(90, "Aggiornamento Standings")
            update_seasonal_standings(sheet, season_id, today)

        # batch_update_player_stats non necessario - già fatto in update_players()
        # tracker.log("   → batch_update_player_stats()...", 'info')
        # tracker.update_progress(95, "Aggiornamento statistiche")
        # batch_update_player_stats(sheet, [])

        tracker.update_progress(95, "Aggiornamento completato")
        tracker.log("✓ Aggiornamenti completati", 'success')

        # 7. Achievement check (solo se NON ARCHIVED)
        tracker.log("🏆 Verifica Achievement...")
        tracker.update_progress(98, "Verifica Achievement")

        from import_base import check_and_unlock_achievements
        check_and_unlock_achievements(sheet)

        tracker.log("✓ Achievement verificati", 'success')

        # Completato!
        tracker.update_progress(100, "Import completato!")
        success_msg = f"Import {tcg.upper()} completato con successo{' (TEST MODE)' if test_mode else ''}!"
        tracker.log(f"✅ {success_msg}", 'success')
        tracker.complete(success=True, message=success_msg)

    except Exception as e:
        import traceback
        error_msg = f"Errore durante import: {str(e)}"
        error_trace = traceback.format_exc()

        tracker.log(f"❌ {error_msg}", 'error')
        tracker.log(f"Traceback: {error_trace}", 'error')
        tracker.complete(success=False, message=error_msg)
