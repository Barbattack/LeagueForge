#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeagueForge - Demo Data Loader
==============================

Carica dati di esempio per testare l'applicazione.

UTILIZZO:
    python load_demo_data.py

COSA FA:
- Crea 2 tornei demo (One Piece e Pokemon)
- Aggiunge 8 giocatori fittizi
- Aggiunge risultati con ranking e punti
- Sblocca alcuni achievement demo

NOTA: I dati demo sono chiaramente identificabili e possono essere
rimossi manualmente dal Google Sheet quando non servono più.
"""

import sys
from datetime import datetime, timedelta
import random

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Errore: installa dipendenze con 'pip install gspread google-auth'")
    sys.exit(1)

# Importa configurazione
try:
    from config import SHEET_ID, CREDENTIALS_FILE
except ImportError:
    print("❌ Errore: config.py non trovato!")
    print("   Esegui prima: python setup_wizard.py")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


# ==============================================================================
# DATI DEMO
# ==============================================================================

DEMO_PLAYERS = [
    {"id": "DEMO001", "name": "Mario Rossi"},
    {"id": "DEMO002", "name": "Luigi Verdi"},
    {"id": "DEMO003", "name": "Anna Bianchi"},
    {"id": "DEMO004", "name": "Paolo Neri"},
    {"id": "DEMO005", "name": "Giulia Ferrari"},
    {"id": "DEMO006", "name": "Marco Colombo"},
    {"id": "DEMO007", "name": "Sara Romano"},
    {"id": "DEMO008", "name": "Luca Ricci"},
]


def connect_sheet():
    """Connette al Google Sheet."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def generate_demo_tournament(tcg, season_id, days_ago=7):
    """Genera dati per un torneo demo."""
    tournament_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    tournament_id = f"{season_id}_{tournament_date}_DEMO"

    # Mescola giocatori e assegna risultati
    players = DEMO_PLAYERS.copy()
    random.shuffle(players)

    n_players = len(players)
    results = []

    for rank, player in enumerate(players, 1):
        # Genera record realistico basato sul ranking
        if rank == 1:
            wins = 4
            losses = 0
        elif rank <= 3:
            wins = 3
            losses = 1
        elif rank <= 5:
            wins = 2
            losses = 2
        else:
            wins = random.randint(0, 2)
            losses = 4 - wins

        record = f"{wins}-{losses}"
        win_points = wins * 3
        omw = round(50 + random.random() * 20, 1)
        points_victory = wins
        points_ranking = n_players - rank + 1
        points_total = points_victory + points_ranking

        results.append({
            "tournament_id": tournament_id,
            "membership": player["id"],
            "name": player["name"],
            "rank": rank,
            "record": record,
            "win_points": win_points,
            "omw": omw,
            "points_victory": points_victory,
            "points_ranking": points_ranking,
            "points_total": points_total,
            "match_w": wins,
            "match_t": 0,
            "match_l": losses,
        })

    tournament = {
        "id": tournament_id,
        "season_id": season_id,
        "date": tournament_date,
        "participants": n_players,
        "rounds": 4,
        "winner": results[0]["name"],
        "winner_membership": results[0]["membership"],
        "tcg": tcg,
        "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (DEMO)",
    }

    return tournament, results


def load_demo_tournaments(sheet):
    """Carica tornei demo nel Google Sheet."""

    # Genera 2 tornei demo
    tournament1, results1 = generate_demo_tournament("onepiece", "OP01", days_ago=14)
    tournament2, results2 = generate_demo_tournament("pokemon", "PKM01", days_ago=7)

    tournaments = [tournament1, tournament2]
    all_results = results1 + results2

    # Carica tornei
    try:
        ws_tournaments = sheet.worksheet("Tournaments")
        existing = ws_tournaments.get_all_values()

        # Verifica se demo già caricati
        for row in existing:
            if "DEMO" in str(row):
                print("  ⚠️  Dati demo già presenti in Tournaments")
                return False

        # Aggiungi tornei
        for t in tournaments:
            row = [t["id"], t["season_id"], t["date"], t["participants"], t["rounds"],
                   t["winner"], t["winner_membership"], t["tcg"], t["import_date"]]
            ws_tournaments.append_row(row)
            print(f"  ✅ Torneo: {t['id']}")

    except gspread.exceptions.WorksheetNotFound:
        print("  ❌ Foglio Tournaments non trovato!")
        return False

    # Carica risultati
    try:
        ws_results = sheet.worksheet("Results")

        for r in all_results:
            row = [r["tournament_id"], r["membership"], r["name"], r["rank"],
                   r["record"], r["win_points"], r["omw"], r["points_victory"],
                   r["points_ranking"], r["points_total"], r["match_w"], r["match_t"], r["match_l"]]
            ws_results.append_row(row)

        print(f"  ✅ {len(all_results)} risultati aggiunti")

    except gspread.exceptions.WorksheetNotFound:
        print("  ❌ Foglio Results non trovato!")
        return False

    # Carica/aggiorna Players
    try:
        ws_players = sheet.worksheet("Players")
        existing_players = ws_players.get_all_values()
        existing_ids = [row[0] for row in existing_players[1:]] if len(existing_players) > 1 else []

        for player in DEMO_PLAYERS:
            if player["id"] not in existing_ids:
                # Nuovo giocatore
                row = [player["id"], player["name"], "onepiece",
                       datetime.now().strftime("%Y-%m-%d"),
                       datetime.now().strftime("%Y-%m-%d"),
                       2, 0, 4, 0, 4, 20]  # Stats iniziali
                ws_players.append_row(row)

        print(f"  ✅ {len(DEMO_PLAYERS)} giocatori aggiunti/aggiornati")

    except gspread.exceptions.WorksheetNotFound:
        print("  ❌ Foglio Players non trovato!")
        return False

    return True


def load_demo_achievements(sheet):
    """Sblocca alcuni achievement demo."""
    try:
        ws = sheet.worksheet("Player_Achievements")

        # Sblocca "Debutto" per tutti i giocatori demo
        for player in DEMO_PLAYERS[:4]:  # Solo primi 4
            row = [player["id"], "ACH_LEG_001", datetime.now().strftime("%Y-%m-%d"), "DEMO", "1"]
            ws.append_row(row)

        # Sblocca "First Blood" per il vincitore
        row = [DEMO_PLAYERS[0]["id"], "ACH_GLO_001", datetime.now().strftime("%Y-%m-%d"), "DEMO", "1"]
        ws.append_row(row)

        print("  ✅ 5 achievement demo sbloccati")
        return True

    except gspread.exceptions.WorksheetNotFound:
        print("  ⚠️  Foglio Player_Achievements non trovato (skip)")
        return True


def main():
    print("=" * 60)
    print("🎮 TANALEAGUE - DEMO DATA LOADER")
    print("=" * 60)
    print()
    print("Questo script caricherà dati di esempio per testare l'app:")
    print("  • 2 tornei demo (One Piece + Pokemon)")
    print("  • 8 giocatori fittizi con risultati")
    print("  • Alcuni achievement sbloccati")
    print()
    print("⚠️  I dati demo sono identificabili (contengono 'DEMO')")
    print("    e possono essere rimossi manualmente.")
    print()

    resp = input("Caricare dati demo? (y/n): ").strip().lower()
    if resp != 'y':
        print("❌ Operazione annullata.")
        return

    print()
    print("🔗 Connessione a Google Sheets...")

    try:
        sheet = connect_sheet()
        print(f"✅ Connesso a: {sheet.title}")
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return

    print()
    print("📋 Caricamento tornei demo...")
    if not load_demo_tournaments(sheet):
        print("❌ Errore caricamento tornei")
        return

    print()
    print("🏆 Caricamento achievement demo...")
    load_demo_achievements(sheet)

    print()
    print("=" * 60)
    print("🎉 DATI DEMO CARICATI!")
    print("=" * 60)
    print()
    print("Ora puoi:")
    print("  1. Avviare l'app: python app.py")
    print("  2. Aprire http://localhost:5000")
    print("  3. Esplorare classifiche e profili giocatori")
    print()
    print("Per rimuovere i dati demo:")
    print("  - Apri Google Sheets")
    print("  - Cerca righe contenenti 'DEMO'")
    print("  - Eliminale manualmente")
    print()


if __name__ == "__main__":
    main()
