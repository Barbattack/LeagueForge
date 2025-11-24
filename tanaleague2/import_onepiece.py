#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================================
TanaLeague v2.0 - One Piece TCG Tournament Import (v2 - Multi-Round Format)
=================================================================================

Import tornei One Piece dal NUOVO formato multi-file Bandai:
- OP_YYYY_MM_DD_R1.csv ... R4.csv (classifica progressiva per round)
- OP_YYYY_MM_DD_ClassificaFinale.csv (ranking finale con OMW%)

CALCOLI:
- W/T/L calcolati dai delta punti tra round:
  - Delta +3 = Win (o BYE)
  - Delta +1 = Tie
  - Delta +0 = Loss
- OMW% dalla ClassificaFinale
- Punti TanaLeague: Points_Victory (W) + Points_Ranking (n - rank + 1)

UTILIZZO:
    # Import con tutti i file
    python import_onepiece_v2.py --rounds OP_2025_11_13_R1.csv,R2.csv,R3.csv,R4.csv \\
                                  --classifica OP_2025_11_13_ClassificaFinale.csv \\
                                  --season OP12

    # Test mode (dry run)
    python import_onepiece_v2.py --rounds R1.csv,R2.csv --classifica finale.csv \\
                                  --season OP12 --test

NOTA: Questo script sostituisce import_onepiece.py per il nuovo formato.
      Il vecchio formato (singolo CSV) non è più supportato.
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

# Validatore (opzionale, se presente)
try:
    from import_validator import ImportValidator
except ImportError:
    ImportValidator = None


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def parse_round_files(round_files: List[str]) -> Dict[str, List[Dict]]:
    """
    Legge i file round (R1, R2, R3, R4) e costruisce la progressione punti.

    Formato CSV atteso:
    "Rank","Match Point","Status","Player Name - 1","Membership Number - 1"

    Args:
        round_files: Lista path ai file round (ordinati R1, R2, ...)

    Returns:
        Dict[membership] -> List[{round, points, rank}]
    """
    player_progression = defaultdict(list)

    for round_num, filepath in enumerate(round_files, start=1):
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Normalizza nomi colonne (rimuovi spazi)
                    row = {k.strip(): v.strip() if v else '' for k, v in row.items()}

                    membership = row.get('Membership Number - 1', '')
                    if not membership:
                        continue

                    # Pad membership a 10 cifre
                    membership = membership.zfill(10)

                    name = row.get('Player Name - 1', '')
                    points = int(row.get('Match Point', 0))
                    rank = int(row.get('Rank', 999))

                    player_progression[membership].append({
                        'round': round_num,
                        'points': points,
                        'rank': rank,
                        'name': name
                    })

        except Exception as e:
            print(f"❌ Errore lettura {filepath}: {e}")
            raise

    return dict(player_progression)


def parse_classifica_finale(filepath: str) -> Dict[str, Dict]:
    """
    Legge il file ClassificaFinale per ottenere OMW% e ranking ufficiale.

    Formato CSV atteso:
    Ranking, Membership Number, User Name, Win Points, OMW %, OOMW %, Memo, Deck URLs

    Args:
        filepath: Path al file ClassificaFinale

    Returns:
        Dict[membership] -> {rank, name, win_points, omw, oomw}
    """
    final_data = {}

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Normalizza nomi colonne
                row = {k.strip(): v.strip() if v else '' for k, v in row.items()}

                membership = row.get('Membership Number', '')
                if not membership:
                    continue

                membership = membership.zfill(10)

                # Parse OMW% (rimuovi % se presente)
                omw_str = row.get('OMW %', '0').replace('%', '').strip()
                try:
                    omw = float(omw_str)
                except ValueError:
                    omw = 0.0

                final_data[membership] = {
                    'rank': int(row.get('Ranking', 999)),
                    'name': row.get('User Name', ''),
                    'win_points': int(row.get('Win Points', 0)),
                    'omw': omw
                }

    except Exception as e:
        print(f"❌ Errore lettura ClassificaFinale: {e}")
        raise

    return final_data


def calculate_wlt_from_progression(progression: List[Dict]) -> Tuple[int, int, int]:
    """
    Calcola W/T/L dalla progressione punti tra round.

    Logica:
    - Delta +3 = Win (o BYE)
    - Delta +1 = Tie
    - Delta +0 = Loss

    Args:
        progression: Lista ordinata di {round, points, rank}

    Returns:
        Tuple[wins, ties, losses]
    """
    wins = 0
    ties = 0
    losses = 0

    # Ordina per round
    sorted_prog = sorted(progression, key=lambda x: x['round'])

    prev_points = 0
    for entry in sorted_prog:
        delta = entry['points'] - prev_points

        if delta >= 3:
            wins += 1
        elif delta == 1:
            ties += 1
        else:  # delta == 0
            losses += 1

        prev_points = entry['points']

    return wins, ties, losses


def merge_tournament_data(
    progression: Dict[str, List[Dict]],
    final_data: Dict[str, Dict]
) -> List[Dict]:
    """
    Unisce i dati dai round files e dalla ClassificaFinale.

    Args:
        progression: Progressione punti per giocatore
        final_data: Dati finali (rank, OMW%)

    Returns:
        Lista di participant dict standardizzati
    """
    participants = []

    # Usa i dati finali come base
    for membership, final in final_data.items():
        prog = progression.get(membership, [])

        if prog:
            wins, ties, losses = calculate_wlt_from_progression(prog)
            name = prog[-1]['name']  # Nome dall'ultimo round
        else:
            # Fallback: calcola W da win_points
            wins = final['win_points'] // 3
            ties = 0
            losses = 0  # Non possiamo saperlo senza round data
            name = final['name']

        participant = create_participant(
            membership=membership,
            name=name or final['name'],
            rank=final['rank'],
            wins=wins,
            ties=ties,
            losses=losses,
            win_points=final['win_points'],
            omw=final['omw']
        )

        participants.append(participant)

    # Ordina per rank
    participants.sort(key=lambda x: x['rank'])

    return participants


def extract_date_from_filename(filename: str) -> str:
    """
    Estrae la data dal nome file.

    Formati supportati:
    - OP_2025_11_13_R1.csv -> 2025-11-13
    - OP_20251113_R1.csv -> 2025-11-13

    Args:
        filename: Nome file

    Returns:
        Data in formato YYYY-MM-DD
    """
    # Pattern: YYYY_MM_DD o YYYYMMDD
    match = re.search(r'(\d{4})[_-]?(\d{2})[_-]?(\d{2})', filename)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    # Fallback: data odierna
    print(f"⚠️  Data non trovata in filename, uso data odierna")
    return datetime.now().strftime('%Y-%m-%d')


def generate_tournament_id(season_id: str, date: str) -> str:
    """
    Genera tournament_id univoco.

    Formato: {season_id}_{YYYYMMDD}
    Esempio: OP12_20251113
    """
    date_compact = date.replace('-', '')
    return f"{season_id}_{date_compact}"


# =============================================================================
# VOUCHER CALCULATION (One Piece specific)
# =============================================================================

def calculate_vouchers(participants: List[Dict], config: Dict) -> List[Dict]:
    """
    Calcola i voucher (buoni negozio) per One Piece.

    Logica distribuzione:
    1. Fondo totale = partecipanti × entry_fee
    2. Costo buste = floor(partecipanti/3) × pack_cost
    3. Rimanente = Fondo - Buste
    4. Distribuzione per categoria:
       - X-0 (0 sconfitte): ratio maggiore
       - X-1 (1 sconfitta): ratio minore
       - Altri: importo fisso (2€)

    Args:
        participants: Lista partecipanti
        config: Configurazione stagione

    Returns:
        Lista partecipanti con campo 'voucher_amount'
    """
    import math

    n_participants = len(participants)
    entry_fee = config.get('entry_fee', 5.0)
    pack_cost = config.get('pack_cost', 6.0)

    # Calcola fondo
    total_fund = n_participants * entry_fee
    n_packs = math.floor(n_participants / 3)
    packs_cost = n_packs * pack_cost
    remaining = total_fund - packs_cost

    # Identifica categorie
    n_rounds = max(p['wins'] + p['ties'] + p['losses'] for p in participants)

    x0_players = []  # 0 sconfitte
    x1_players = []  # 1 sconfitta
    other_players = []  # Altri (fuori top8 o >1 sconfitta)

    for p in participants:
        if p['rank'] <= 8:
            if p['losses'] == 0:
                x0_players.append(p)
            elif p['losses'] == 1:
                x1_players.append(p)
            else:
                other_players.append(p)
        else:
            other_players.append(p)

    # Calcola distribuzione
    others_amount = 2.0  # Fisso per altri in top8
    others_total = len([p for p in other_players if p['rank'] <= 8]) * others_amount

    pool_for_winners = remaining - others_total
    if pool_for_winners < 0:
        pool_for_winners = 0

    # Ratios (configurabili)
    x0_ratio = 1.9
    x1_ratio = 1.0

    total_weight = len(x0_players) * x0_ratio + len(x1_players) * x1_ratio
    if total_weight > 0:
        unit_value = pool_for_winners / total_weight
    else:
        unit_value = 0

    # Arrotondamento a 0.50€
    rounding = 0.50

    # Assegna voucher
    for p in participants:
        if p['membership'] in [x['membership'] for x in x0_players]:
            amount = round((unit_value * x0_ratio) / rounding) * rounding
        elif p['membership'] in [x['membership'] for x in x1_players]:
            amount = round((unit_value * x1_ratio) / rounding) * rounding
        elif p['rank'] <= 8:
            amount = others_amount
        else:
            amount = 0

        p['voucher_amount'] = amount

    return participants


def write_vouchers_to_sheet(sheet, tournament_data: Dict, test_mode: bool = False) -> int:
    """
    Scrive i voucher nel foglio Vouchers.

    Args:
        sheet: Google Sheet connesso
        tournament_data: Dati torneo con voucher
        test_mode: Se True, non scrive

    Returns:
        int: Numero voucher scritti
    """
    if test_mode:
        total = sum(p.get('voucher_amount', 0) for p in tournament_data['participants'])
        print(f"✅ Vouchers: {total}€ totali (test mode)")
        return 0

    try:
        ws_vouchers = sheet.worksheet("Vouchers")
    except Exception:
        print("⚠️  Foglio Vouchers non trovato, skip")
        return 0

    tournament_id = tournament_data['tournament_id']
    rows = []

    for p in tournament_data['participants']:
        amount = p.get('voucher_amount', 0)
        if amount > 0:
            rows.append([
                f"{tournament_id}_{p['membership']}",
                tournament_id,
                p['membership'],
                p['name'],
                p['rank'],
                amount
            ])

    if rows:
        ws_vouchers.append_rows(rows, value_input_option='RAW')

    total = sum(p.get('voucher_amount', 0) for p in tournament_data['participants'])
    print(f"✅ Vouchers: {len(rows)} assegnati, {total}€ totali")
    return len(rows)


# =============================================================================
# MAIN IMPORT FUNCTION
# =============================================================================

def import_tournament(
    round_files: List[str],
    classifica_file: str,
    season_id: str,
    test_mode: bool = False,
    reimport: bool = False
) -> Optional[Dict]:
    """
    Importa un torneo One Piece dal nuovo formato multi-file.

    Args:
        round_files: Lista path ai file round (R1, R2, ...)
        classifica_file: Path al file ClassificaFinale
        season_id: ID stagione (es. OP12)
        test_mode: Se True, non scrive
        reimport: Se True, permette reimport

    Returns:
        Dict con dati torneo o None se errore
    """
    print("=" * 60)
    print("🚀 IMPORT TORNEO ONE PIECE (v2 - Multi-Round)")
    print("=" * 60)
    print(f"📊 Stagione: {season_id}")
    print(f"📁 Round files: {len(round_files)}")
    print(f"📁 Classifica: {classifica_file}")
    print("")

    # 1. Connessione
    print("📡 Connessione Google Sheets...")
    sheet = connect_sheet()
    print("   ✅ Connesso")

    # 2. Parsing files
    print("\n📂 Parsing files...")

    print(f"   Lettura {len(round_files)} round files...")
    progression = parse_round_files(round_files)
    print(f"   ✅ {len(progression)} giocatori trovati")

    print(f"   Lettura ClassificaFinale...")
    final_data = parse_classifica_finale(classifica_file)
    print(f"   ✅ {len(final_data)} giocatori con OMW%")

    # 3. Merge data
    print("\n🔄 Merge dati...")
    participants = merge_tournament_data(progression, final_data)
    print(f"   ✅ {len(participants)} partecipanti totali")

    # 4. Extract metadata
    tournament_date = extract_date_from_filename(round_files[0])
    tournament_id = generate_tournament_id(season_id, tournament_date)

    print(f"\n📅 Data: {tournament_date}")
    print(f"🆔 Tournament ID: {tournament_id}")

    # 5. Check duplicate
    can_proceed, existing = check_duplicate_tournament(sheet, tournament_id, allow_reimport=reimport)
    if not can_proceed:
        return None

    if existing.get('exists') and reimport:
        print(f"\n🔄 Reimport richiesto, elimino dati esistenti...")
        delete_existing_tournament(sheet, tournament_id)

    # 6. Get season config
    config = get_season_config(sheet, season_id)
    if not config:
        print(f"⚠️  Configurazione stagione {season_id} non trovata, uso default")
        config = {'entry_fee': 5.0, 'pack_cost': 6.0}

    # 7. Calculate vouchers (One Piece specific)
    print("\n💰 Calcolo voucher...")
    participants = calculate_vouchers(participants, config)

    # 8. Create tournament data
    source_files = [f.split('/')[-1] for f in round_files]
    source_files.append(classifica_file.split('/')[-1])

    tournament_data = create_tournament_data(
        tournament_id=tournament_id,
        season_id=season_id,
        date=tournament_date,
        participants=participants,
        tcg='OP',
        source_files=source_files
    )

    # 9. Write to sheets
    print("\n💾 Scrittura dati...")

    write_tournament_to_sheet(sheet, tournament_data, test_mode)
    write_results_to_sheet(sheet, tournament_data, test_mode)
    write_vouchers_to_sheet(sheet, tournament_data, test_mode)

    if not test_mode:
        update_players(sheet, tournament_data, test_mode)

        print("\n📈 Aggiornamento standings...")
        update_seasonal_standings(sheet, season_id, tournament_date)

        increment_season_tournament_count(sheet, season_id)

    # 10. Finalize
    print("\n🎮 Finalizzazione...")
    finalize_import(sheet, tournament_data, test_mode)

    # 11. Summary
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
        description='Import One Piece tournament (v2 - Multi-Round Format)'
    )
    parser.add_argument(
        '--rounds',
        required=True,
        help='Round CSV files comma-separated (es: R1.csv,R2.csv,R3.csv,R4.csv)'
    )
    parser.add_argument(
        '--classifica',
        required=True,
        help='ClassificaFinale CSV file'
    )
    parser.add_argument(
        '--season',
        required=True,
        help='Season ID (es: OP12)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (no write)'
    )
    parser.add_argument(
        '--reimport',
        action='store_true',
        help='Allow reimport of existing tournament'
    )

    args = parser.parse_args()

    # Parse round files
    round_files = [f.strip() for f in args.rounds.split(',')]

    # Run import
    result = import_tournament(
        round_files=round_files,
        classifica_file=args.classifica,
        season_id=args.season,
        test_mode=args.test,
        reimport=args.reimport
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
