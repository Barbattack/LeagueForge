#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge v2.0 - Riftbound TCG Tournament Import (v2 - Refactored)
=================================================================================

Import tornei Riftbound da CSV multi-round (formato tournament software).
Ogni file contiene i match del singolo round.

FORMATO CSV:
Table Number, Feature Match, Ghost Match, ..., Player 1 Info, Player 2 Info,
Match Status, Match Result, Round Record, Event Record, ...

UTILIZZO:
    python import_riftbound_v2.py --rounds RFB_2025_11_17_R1.csv,R2.csv,R3.csv \\
                                   --season RFB01

    # Test mode
    python import_riftbound_v2.py --rounds R1.csv,R2.csv --season RFB01 --test
=================================================================================
"""

import csv
import re
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Import modulo base
from import_base import (
    connect_sheet,
    check_duplicate_tournament,
    delete_existing_tournament,
    write_tournament_to_sheet,
    write_results_to_sheet,
    update_players,
    update_seasonal_standings,
    finalize_import,
    get_season_config,
    increment_season_tournament_count,
    create_participant,
    create_tournament_data,
    format_summary
)

from sheet_utils import fuzzy_match


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def parse_wld_record(record: str) -> Tuple[int, int, int]:
    """
    Parsing record W-L-D da stringa.

    Args:
        record: Stringa formato "3-1-0" o "3-1"

    Returns:
        Tuple[wins, losses, draws]
    """
    if not record:
        return 0, 0, 0

    match = re.match(r'(\d+)-(\d+)(?:-(\d+))?', record.strip())
    if match:
        w = int(match.group(1))
        l = int(match.group(2))
        d = int(match.group(3)) if match.group(3) else 0
        return w, l, d

    return 0, 0, 0


def parse_csv_rounds(csv_files: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """
    Legge tutti i CSV dei round e aggrega i risultati.

    Args:
        csv_files: Lista di path ai CSV (uno per round)

    Returns:
        Tuple[players_list, matches_list]
    """
    players_data = {}  # user_id -> {name, event_record, rounds_played}
    matches_data = []  # Lista di match

    for csv_idx, csv_path in enumerate(csv_files, 1):
        print(f"   📄 Round {csv_idx}: {csv_path.split('/')[-1]}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header

            match_count = 0
            for row in reader:
                if len(row) < 18:
                    continue

                # Player 1 (colonne 4-6)
                p1_id = row[4].strip()
                p1_first = row[5].strip()
                p1_last = row[6].strip()
                p1_event_record = row[16].strip() if len(row) > 16 else ""

                # Player 2 (colonne 8-10)
                p2_id = row[8].strip()
                p2_first = row[9].strip()
                p2_last = row[10].strip()
                p2_event_record = row[17].strip() if len(row) > 17 else ""

                # Match data
                table_number = row[0].strip() if row[0] else ""
                match_status = row[14].strip() if len(row) > 14 else ""  # Colonna 15: Match Status
                match_result = row[15].strip() if len(row) > 15 else ""  # Colonna 16: Match Result

                # Gestione BYE: se p2_id è vuoto ma c'è "has a bye", è un bye valido
                is_bye = "has a bye" in match_result.lower()

                if not p1_id:
                    continue

                # Se non è un bye e non c'è p2, skip
                if not is_bye and not p2_id:
                    continue

                match_count += 1

                # Memorizza dati giocatori
                p1_name = f"{p1_first} {p1_last}".strip()
                p2_name = f"{p2_first} {p2_last}".strip() if p2_id else ""

                if p1_id:
                    players_data[p1_id] = {
                        'name': p1_name,
                        'event_record': p1_event_record,
                        'rounds_played': csv_idx
                    }

                if p2_id:
                    players_data[p2_id] = {
                        'name': p2_name,
                        'event_record': p2_event_record,
                        'rounds_played': csv_idx
                    }

                # Determina vincitore
                winner_id = ""

                if is_bye:
                    # BYE = vittoria automatica per p1
                    winner_id = p1_id
                elif match_result and ":" in match_result:
                    # Fuzzy matching normale
                    winner_name = match_result.split(":")[0].strip()

                    if fuzzy_match(winner_name, p1_name):
                        winner_id = p1_id
                    elif p2_name and fuzzy_match(winner_name, p2_name):
                        winner_id = p2_id
                    elif fuzzy_match(winner_name, p1_last, 80):
                        winner_id = p1_id
                    elif p2_name and fuzzy_match(winner_name, p2_last, 80):
                        winner_id = p2_id

                matches_data.append({
                    'round': csv_idx,
                    'table': table_number,
                    'p1_id': p1_id,
                    'p1_name': p1_name,
                    'p2_id': p2_id if not is_bye else '',
                    'p2_name': p2_name if not is_bye else '',
                    'winner_id': winner_id,
                    'result': match_result,
                    'is_bye': is_bye
                })

            print(f"      ✅ {match_count} matches")

    if not players_data:
        raise ValueError("❌ Nessun giocatore trovato nei CSV!")

    # Calcola W-L-D contando i match vinti/persi (Event Record è incomprensibile)
    match_record = {}  # user_id -> {wins, losses, ties}
    for user_id in players_data.keys():
        match_record[user_id] = {'wins': 0, 'losses': 0, 'ties': 0}

    for match in matches_data:
        p1_id = match['p1_id']
        p2_id = match['p2_id']
        winner_id = match['winner_id']
        is_bye = match.get('is_bye', False)

        if winner_id == p1_id:
            match_record[p1_id]['wins'] += 1
            # Solo se NON è un bye, aggiorna p2
            if p2_id and not is_bye:
                match_record[p2_id]['losses'] += 1
        elif winner_id == p2_id:
            match_record[p2_id]['wins'] += 1
            match_record[p1_id]['losses'] += 1
        elif not winner_id and not is_bye:
            # Nessun vincitore = pareggio (raro in best of 3)
            match_record[p1_id]['ties'] += 1
            if p2_id:
                match_record[p2_id]['ties'] += 1

    # Converti in lista e calcola ranking
    players_list = []
    for user_id, data in players_data.items():
        record = match_record.get(user_id, {'wins': 0, 'losses': 0, 'ties': 0})
        w = record['wins']
        l = record['losses']
        d = record['ties']
        win_points = w * 3 + d * 1

        players_list.append({
            'user_id': user_id,
            'name': data['name'],
            'wins': w,
            'losses': l,
            'ties': d,
            'win_points': win_points,
            'rounds_played': data['rounds_played']
        })

    # Ordina per punti, poi per vittorie
    players_list.sort(key=lambda x: (x['win_points'], x['wins']), reverse=True)

    # Assegna rank
    for rank, player in enumerate(players_list, 1):
        player['rank'] = rank

    return players_list, matches_data


def extract_date_from_filename(filename: str) -> str:
    """
    Estrae data dal nome file.

    Formati:
    - RFB_2025_11_17_R1.csv -> 2025-11-17
    """
    match = re.search(r'(\d{4})[_-](\d{2})[_-](\d{2})', filename)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    return datetime.now().strftime('%Y-%m-%d')


def generate_tournament_id(season_id: str, date: str) -> str:
    """Genera tournament_id."""
    date_compact = date.replace('-', '')
    return f"{season_id}_{date_compact}"


# =============================================================================
# WRITE MATCHES
# =============================================================================

def write_matches_to_sheet(
    sheet,
    tournament_id: str,
    matches: List[Dict],
    test_mode: bool = False
) -> int:
    """
    Scrive i match nel foglio Riftbound_Matches.

    Args:
        sheet: Google Sheet
        tournament_id: ID torneo
        matches: Lista match
        test_mode: Se True, non scrive

    Returns:
        int: Numero match scritti
    """
    if test_mode:
        print(f"✅ Matches: {len(matches)} (test mode)")
        return 0

    try:
        ws_matches = sheet.worksheet("Riftbound_Matches")
    except Exception:
        print("⚠️  Foglio Riftbound_Matches non trovato, skip")
        return 0

    rows = []
    for m in matches:
        rows.append([
            tournament_id,
            m['p1_id'],
            m['p1_name'],
            m['p2_id'],
            m['p2_name'],
            m['winner_id'],
            m['round'],
            m['table'],
            m['result']
        ])

    if rows:
        ws_matches.append_rows(rows, value_input_option='RAW')

    print(f"✅ Matches: {len(rows)} salvati")
    return len(rows)


# =============================================================================
# MAIN IMPORT FUNCTION
# =============================================================================

def import_tournament(
    round_files: List[str],
    season_id: str,
    test_mode: bool = False,
    reimport: bool = False
) -> Optional[Dict]:
    """
    Importa un torneo Riftbound.

    Args:
        round_files: Lista path CSV round
        season_id: ID stagione (es. RFB01)
        test_mode: Se True, non scrive
        reimport: Se True, permette reimport

    Returns:
        Dict con dati torneo o None
    """
    print("=" * 60)
    print("🚀 IMPORT TORNEO RIFTBOUND (v2)")
    print("=" * 60)
    print(f"📊 Stagione: {season_id}")
    print(f"📁 Round files: {len(round_files)}")
    print("")

    # 1. Connessione
    print("📡 Connessione Google Sheets...")
    sheet = connect_sheet()
    print("   ✅ Connesso")

    # 2. Parsing
    print("\n📂 Parsing files...")
    players_list, matches_list = parse_csv_rounds(round_files)
    print(f"\n   📊 {len(players_list)} giocatori, {len(matches_list)} match")

    # 3. Metadata
    tournament_date = extract_date_from_filename(round_files[0])
    tournament_id = generate_tournament_id(season_id, tournament_date)

    print(f"\n📅 Data: {tournament_date}")
    print(f"🆔 Tournament ID: {tournament_id}")

    # 4. Check duplicate
    can_proceed, existing = check_duplicate_tournament(sheet, tournament_id, allow_reimport=reimport)
    if not can_proceed:
        return None

    if existing.get('exists') and reimport:
        print(f"\n🔄 Reimport richiesto...")
        delete_existing_tournament(sheet, tournament_id)

    # 5. Converti in formato standardizzato
    participants = []
    for p in players_list:
        participant = create_participant(
            membership=p['user_id'],  # Riftbound usa user_id
            name=p['name'],
            rank=p['rank'],
            wins=p['wins'],
            ties=p['ties'],
            losses=p['losses'],
            win_points=p['win_points'],
            omw=0  # Non disponibile per Riftbound
        )
        participants.append(participant)

    # 6. Create tournament data
    source_files = [f.split('/')[-1] for f in round_files]

    # Estrai TCG code da season_id (es. RFB01 -> RFB)
    tcg = ''.join(c for c in season_id if c.isalpha()).upper()

    tournament_data = create_tournament_data(
        tournament_id=tournament_id,
        season_id=season_id,
        date=tournament_date,
        participants=participants,
        tcg=tcg,
        source_files=source_files
    )

    # 7. Write to sheets
    print("\n💾 Scrittura dati...")

    write_tournament_to_sheet(sheet, tournament_data, test_mode)
    write_results_to_sheet(sheet, tournament_data, test_mode)
    write_matches_to_sheet(sheet, tournament_id, matches_list, test_mode)

    if not test_mode:
        update_players(sheet, tournament_data, test_mode)

        print("\n📈 Aggiornamento standings...")
        update_seasonal_standings(sheet, season_id, tournament_date)

        increment_season_tournament_count(sheet, season_id)

    # 8. Finalize
    print("\n🎮 Finalizzazione...")
    finalize_import(sheet, tournament_data, test_mode)

    # 9. Summary
    print(format_summary(tournament_data))

    if test_mode:
        print("\n⚠️  TEST MODE - Nessun dato scritto")
    else:
        print("\n✅ IMPORT COMPLETATO!")

    print("=" * 60)

    return tournament_data


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Import Riftbound tournament (v2)'
    )
    parser.add_argument(
        '--rounds',
        required=True,
        help='Round CSV files comma-separated (es: R1.csv,R2.csv,R3.csv)'
    )
    parser.add_argument(
        '--season',
        required=True,
        help='Season ID (es: RFB01)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (no write)'
    )
    parser.add_argument(
        '--reimport',
        action='store_true',
        help='Allow reimport'
    )

    args = parser.parse_args()

    round_files = [f.strip() for f in args.rounds.split(',')]

    result = import_tournament(
        round_files=round_files,
        season_id=args.season,
        test_mode=args.test,
        reimport=args.reimport
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
