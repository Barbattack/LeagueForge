#!/usr/bin/env python3
"""
Calcola la classifica ESATTA del torneo One Piece 2025-11-13
con la correzione: Blund ha battuto Lorbag99 nel Round 4
"""

import csv
from collections import defaultdict
from typing import Dict, List, Tuple

def read_pairings(filepath: str) -> List[Dict]:
    """Legge i pairings dal CSV"""
    pairings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairings.append({
                'round': int(row['Round']),
                'p1_id': row['ID Player 1'].strip(),
                'p1_nick': row['Nick Player 1'].strip(),
                'p2_id': row['ID Player 2'].strip(),
                'p2_nick': row['Nick Player 2'].strip(),
                'winner': int(row['Winner'])
            })
    return pairings

def apply_correction(pairings: List[Dict]) -> List[Dict]:
    """Corregge il match R4: Blund vs Lorbag99"""
    corrected = []
    for match in pairings:
        if (match['round'] == 4 and
            match['p1_id'] == '203688' and  # Lorbag99
            match['p2_id'] == '110798'):     # Blund
            # Corregge: Blund vince (winner = 2)
            match['winner'] = 2
            print(f"✓ Corretto R4: Lorbag99 vs Blund → Blund WIN")
        corrected.append(match)
    return corrected

def calculate_records(pairings: List[Dict]) -> Dict[str, Dict]:
    """Calcola record W-L per ogni giocatore"""
    records = defaultdict(lambda: {'nick': '', 'wins': 0, 'losses': 0, 'opponents': []})

    for match in pairings:
        p1_id = match['p1_id']
        p2_id = match['p2_id']

        # Salva nick
        records[p1_id]['nick'] = match['p1_nick']
        records[p2_id]['nick'] = match['p2_nick']

        # Salva avversari
        records[p1_id]['opponents'].append(p2_id)
        records[p2_id]['opponents'].append(p1_id)

        # Registra risultato
        if match['winner'] == 1:
            records[p1_id]['wins'] += 1
            records[p2_id]['losses'] += 1
        else:
            records[p2_id]['wins'] += 1
            records[p1_id]['losses'] += 1

    return dict(records)

def calculate_win_rate(record: Dict) -> float:
    """Calcola win rate, minimo 33.33% per regole TCG"""
    total = record['wins'] + record['losses']
    if total == 0:
        return 0.333333
    wr = record['wins'] / total
    return max(0.333333, wr)

def calculate_omw(player_id: str, records: Dict[str, Dict]) -> float:
    """Calcola OMW% = media del win rate degli avversari"""
    opponents = records[player_id]['opponents']
    if not opponents:
        return 0.0

    total_wr = sum(calculate_win_rate(records[opp_id]) for opp_id in opponents)
    return total_wr / len(opponents)

def calculate_oomw(player_id: str, records: Dict[str, Dict]) -> float:
    """Calcola OOMW% = media degli OMW% degli avversari"""
    opponents = records[player_id]['opponents']
    if not opponents:
        return 0.0

    total_omw = sum(calculate_omw(opp_id, records) for opp_id in opponents)
    return total_omw / len(opponents)

def format_percentage(value: float) -> str:
    """Formatta percentuale come nel CSV originale (es. '52%' o '68.8%')"""
    pct = value * 100
    if pct == int(pct):
        return f"{int(pct)}%"
    else:
        return f"{pct:.1f}%"

def main():
    print("=" * 70)
    print("CALCOLO CLASSIFICA ESATTA - One Piece 2025-11-13")
    print("=" * 70)
    print()

    # 1. Leggi pairings
    pairings = read_pairings('PairingsTorneoOP - Foglio1.csv')
    print(f"✓ Letti {len(pairings)} match da 4 round")
    print()

    # 2. Applica correzione R4
    pairings = apply_correction(pairings)
    print()

    # 3. Calcola record W-L
    records = calculate_records(pairings)
    print(f"✓ Calcolati record per {len(records)} giocatori")
    print()

    # 4. Calcola OMW% e OOMW%
    standings = []
    for player_id, record in records.items():
        win_points = record['wins'] * 3
        omw = calculate_omw(player_id, records)
        oomw = calculate_oomw(player_id, records)

        standings.append({
            'id': player_id,
            'nick': record['nick'],
            'wins': record['wins'],
            'losses': record['losses'],
            'win_points': win_points,
            'omw': omw,
            'oomw': oomw
        })

    # 5. Ordina per: Win Points DESC, OMW% DESC, OOMW% DESC
    standings.sort(key=lambda x: (x['win_points'], x['omw'], x['oomw']), reverse=True)

    # 6. Mostra classifica
    print("CLASSIFICA FINALE:")
    print("-" * 70)
    print(f"{'Pos':<4} {'Player':<15} {'ID':<12} {'W-L':<6} {'Pts':<5} {'OMW%':<8} {'OOMW%':<8}")
    print("-" * 70)

    for i, player in enumerate(standings, 1):
        print(f"{i:<4} {player['nick']:<15} {player['id']:<12} "
              f"{player['wins']}-{player['losses']:<4} {player['win_points']:<5} "
              f"{format_percentage(player['omw']):<8} {format_percentage(player['oomw']):<8}")

    print()
    print("=" * 70)

    # 7. Scrivi CSV corretta
    output_file = 'OP_2025_11_13_ClassificaFinale_EXACT.csv'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # Header identico al file originale
        writer.writerow([
            'Ranking',
            'Membership Number',
            'User Name',
            'Win Points',
            'OMW %',
            'OOMW %',
            'Memo',
            'Deck URLs'
        ])

        # Scrivi dati
        for i, player in enumerate(standings, 1):
            writer.writerow([
                i,
                f"0000{player['id']}",  # Formato con zeri iniziali
                player['nick'],
                player['win_points'],
                format_percentage(player['omw']),
                format_percentage(player['oomw']),
                'undefined',
                ''
            ])

    print(f"✓ File creato: {output_file}")
    print()

    # 8. Confronto chiave
    print("CONFRONTO CHIAVE (con file errato):")
    print("-" * 70)
    print("PRIMA (errato):           DOPO (corretto):")
    print(f"2. Lorbag99    9pt  →    {standings[4]['nick']:<12} {standings[4]['win_points']}pt")
    print(f"5. Blund       6pt  →    {standings[3]['nick']:<12} {standings[3]['win_points']}pt")
    print()

if __name__ == "__main__":
    main()
