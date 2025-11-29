#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeagueForge - Database Initialization
=====================================

Crea automaticamente tutti i fogli necessari nel Google Sheet.

PREREQUISITI:
1. Google Sheet già creato (anche vuoto)
2. Service Account con accesso al Google Sheet
3. config.py configurato con SHEET_ID e CREDENTIALS_FILE

UTILIZZO:
    python init_database.py

COSA FA:
- Crea tutti i fogli necessari con headers corretti
- Popola Achievement_Definitions con 40+ achievement
- Crea Config con stagioni esempio
- NON sovrascrive fogli esistenti (chiede conferma)
"""

import sys
from datetime import datetime

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
    print("   Copia config.example.py in config.py e configura i valori.")
    print("   Oppure esegui: python setup_wizard.py")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


# ==============================================================================
# DEFINIZIONE FOGLI
# ==============================================================================

SHEETS_STRUCTURE = {
    "Config": {
        "headers": ["Season_ID", "TCG", "Name", "Status", "Start_Date", "End_Date", "Entry_Fee", "Pack_Cost"],
        "description": "Configurazione stagioni",
        "sample_data": [
            ["OP01", "onepiece", "Stagione 1 - One Piece", "ACTIVE", "2025-01-01", "2025-06-30", "5", "4"],
            ["PKM01", "pokemon", "Stagione 1 - Pokemon", "ACTIVE", "2025-01-01", "2025-06-30", "5", "4"],
            ["RFB01", "riftbound", "Stagione 1 - Riftbound", "ACTIVE", "2025-01-01", "2025-06-30", "5", "4"],
        ]
    },
    "Tournaments": {
        "headers": ["Tournament_ID", "Season_ID", "Date", "Participants", "Rounds", "Winner", "Winner_Membership", "TCG", "Import_Date"],
        "description": "Lista tornei importati"
    },
    "Results": {
        "headers": ["Tournament_ID", "Membership_Number", "Player_Name", "Ranking", "Record", "Win_Points", "OMW", "Points_Victory", "Points_Ranking", "Points_Total", "Match_W", "Match_T", "Match_L"],
        "description": "Risultati individuali giocatori"
    },
    "Players": {
        "headers": ["Membership_Number", "Player_Name", "TCG", "First_Seen", "Last_Seen", "Total_Tournaments", "Tournament_Wins", "Match_W", "Match_T", "Match_L", "Total_Points"],
        "description": "Anagrafica giocatori"
    },
    "Player_Stats": {
        "headers": ["Membership", "Name", "TCG", "Total_Tournaments", "Total_Wins", "Current_Streak", "Best_Streak", "Top8_Count", "Last_Rank", "Last_Date", "Seasons_Count", "Updated_At", "Total_Points"],
        "description": "Statistiche lifetime aggregate (CQRS read model)"
    },
    "Seasonal_Standings_PROV": {
        "headers": ["Season_ID", "Rank", "Membership_Number", "Player_Name", "Tournaments_Played", "Best_Results", "Total_Points", "Avg_Points"],
        "description": "Classifiche provvisorie stagioni attive"
    },
    "Seasonal_Standings_FINAL": {
        "headers": ["Season_ID", "Rank", "Membership_Number", "Player_Name", "Tournaments_Played", "Best_Results", "Total_Points", "Avg_Points"],
        "description": "Classifiche finali stagioni chiuse"
    },
    "Achievement_Definitions": {
        "headers": ["achievement_id", "name", "description", "category", "rarity", "emoji", "points", "requirement_type", "requirement_value"],
        "description": "Definizioni achievement",
        "special": "achievements"  # Flag per popolare con achievement
    },
    "Player_Achievements": {
        "headers": ["membership", "achievement_id", "unlocked_date", "tournament_id", "progress"],
        "description": "Achievement sbloccati dai giocatori"
    },
    "Vouchers": {
        "headers": ["Tournament_ID", "Membership_Number", "Player_Name", "Ranking", "Category", "Voucher_Amount"],
        "description": "Buoni negozio (One Piece)"
    },
    "Pokemon_Matches": {
        "headers": ["Tournament_ID", "Round", "Table", "Player1_Membership", "Player1_Name", "Player2_Membership", "Player2_Name", "Winner", "Outcome"],
        "description": "Match H2H Pokemon"
    },
    "Riftbound_Matches": {
        "headers": ["Tournament_ID", "Round", "Table", "Player1_Membership", "Player1_Name", "Player2_Membership", "Player2_Name", "Winner", "Result"],
        "description": "Match H2H Riftbound"
    }
}


def get_achievement_data():
    """Restituisce lista completa degli achievement."""
    return [
        # GLORY
        ["ACH_GLO_001", "First Blood", "Vinci il tuo primo torneo", "Glory", "Uncommon", "🎬", 25, "tournament_wins", 1],
        ["ACH_GLO_002", "Podium Climber", "Raggiungi 3 top8", "Glory", "Uncommon", "🎯", 25, "top8_count", 3],
        ["ACH_GLO_003", "King of the Hill", "Vinci un torneo mentre sei rank #1", "Glory", "Rare", "👑", 50, "special", "win_as_rank1"],
        ["ACH_GLO_004", "Phoenix Rising", "Vinci dopo essere stato ultimo", "Glory", "Rare", "🔥", 50, "special", "comeback_win"],
        ["ACH_GLO_005", "Perfect Storm", "Vinci senza sconfitte (4-0 o 5-0)", "Glory", "Rare", "⚡", 50, "special", "perfect_win"],
        ["ACH_GLO_006", "Dynasty Builder", "Vinci 5 tornei totali", "Glory", "Legendary", "💎", 250, "tournament_wins", 5],
        # GIANT SLAYER
        ["ACH_GIA_001", "Lucky Shot", "Batti un giocatore 5+ posizioni sopra", "Giant Slayer", "Common", "🎲", 10, "special", "upset_5plus"],
        ["ACH_GIA_002", "Dragonslayer", "Batti il rank #1 della stagione", "Giant Slayer", "Rare", "🐉", 50, "special", "beat_rank1"],
        ["ACH_GIA_003", "Giant Killer", "Batti il vincitore della stagione precedente", "Giant Slayer", "Rare", "👹", 50, "special", "beat_prev_champ"],
        # CONSISTENCY
        ["ACH_CON_001", "Back to Back", "2 top8 consecutivi", "Consistency", "Uncommon", "🔄", 25, "special", "streak_top8_2"],
        ["ACH_CON_002", "Regular", "Partecipa a 5 tornei in una stagione", "Consistency", "Common", "📅", 10, "special", "season_5tournaments"],
        ["ACH_CON_003", "Hot Streak", "4 top8 consecutivi", "Consistency", "Rare", "⚡", 50, "special", "streak_top8_4"],
        ["ACH_CON_004", "Iron Wall", "5 tornei consecutivi in top50%", "Consistency", "Rare", "🛡️", 50, "special", "streak_top50_5"],
        ["ACH_CON_005", "Season Warrior", "100% partecipazione stagione (8+ tornei)", "Consistency", "Rare", "🏛️", 50, "special", "season_full_attendance"],
        # HEARTBREAK
        ["ACH_HEA_001", "Participation Trophy", "Finisci ultimo (8+ giocatori)", "Heartbreak", "Common", "😅", 10, "special", "last_place"],
        ["ACH_HEA_002", "So Close", "9° posto per 3 volte", "Heartbreak", "Uncommon", "😢", 25, "special", "rank9_3x"],
        ["ACH_HEA_003", "Forever Second", "2° posto 3 volte senza vittorie", "Heartbreak", "Rare", "🥈", 50, "special", "second_3x_no_wins"],
        # WILDCARDS
        ["ACH_WIL_001", "The Answer", "Esattamente 42 punti in un torneo", "Wildcards", "Epic", "🎯", 100, "special", "points_42"],
        ["ACH_WIL_002", "Perfectly Balanced", "Record 2-2 in torneo 4+ round", "Wildcards", "Common", "⚖️", 10, "special", "record_2-2"],
        ["ACH_WIL_003", "Lucky Seven", "Piazza esattamente 7°", "Wildcards", "Uncommon", "🎰", 25, "special", "rank_7"],
        ["ACH_WIL_004", "Triple Threat", "3° posto per 3 volte", "Wildcards", "Rare", "🔢", 50, "special", "rank3_3x"],
        # LEGACY
        ["ACH_LEG_001", "Debutto", "Primo torneo", "Legacy", "Common", "🎬", 10, "tournaments_played", 1],
        ["ACH_LEG_002", "Veteran", "10 tornei completati", "Legacy", "Uncommon", "🗓️", 25, "tournaments_played", 10],
        ["ACH_LEG_003", "Multi-Format", "3+ tornei in 2 TCG diversi", "Legacy", "Rare", "🌈", 50, "special", "multi_tcg_3+"],
        ["ACH_LEG_004", "Gladiator", "25 tornei completati", "Legacy", "Rare", "⚔️", 50, "tournaments_played", 25],
        ["ACH_LEG_005", "Hat Trick", "3 vittorie totali", "Legacy", "Rare", "🏆", 50, "tournament_wins", 3],
        ["ACH_LEG_006", "Hall of Famer", "50 tornei completati", "Legacy", "Legendary", "🏛️", 250, "tournaments_played", 50],
        # SEASONAL
        ["ACH_SEA_001", "Opening Act", "Vinci il primo torneo di una stagione", "Seasonal", "Rare", "🎉", 50, "special", "win_season_first"],
        ["ACH_SEA_002", "Grand Finale", "Vinci l'ultimo torneo di una stagione", "Seasonal", "Rare", "🎭", 50, "special", "win_season_last"],
        ["ACH_SEA_003", "Season Sweep", "3+ vittorie in una stagione", "Seasonal", "Legendary", "👑", 250, "special", "season_3wins"],
    ]


def connect_sheet():
    """Connette al Google Sheet."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def create_worksheet(sheet, name, config, force=False):
    """Crea un singolo worksheet con headers."""
    try:
        ws = sheet.worksheet(name)
        if not force:
            print(f"  ⚠️  {name} già esiste (skip)")
            return None
        else:
            ws.clear()
            print(f"  🗑️  {name} svuotato")
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=len(config["headers"]) + 2)
        print(f"  ✅ {name} creato")

    # Scrivi headers
    ws.update(values=[config["headers"]], range_name="A1")
    ws.format("A1:Z1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # Popola dati speciali
    if config.get("special") == "achievements":
        achievements = get_achievement_data()
        if achievements:
            ws.update(values=achievements, range_name="A2")
            print(f"      → {len(achievements)} achievement inseriti")
    elif config.get("sample_data"):
        ws.update(values=config["sample_data"], range_name="A2")
        print(f"      → {len(config['sample_data'])} righe esempio inserite")

    return ws


def main():
    print("=" * 60)
    print("🗄️  LEAGUEFORGE - DATABASE INITIALIZATION")
    print("=" * 60)
    print()
    print(f"📊 Google Sheet ID: {SHEET_ID[:20]}...")
    print(f"🔑 Credentials: {CREDENTIALS_FILE}")
    print()
    print("Questo script creerà i seguenti fogli:")
    for name, config in SHEETS_STRUCTURE.items():
        print(f"  • {name} - {config['description']}")
    print()

    resp = input("Procedere? (y/n): ").strip().lower()
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
        print()
        print("Verifica che:")
        print("  1. SHEET_ID in config.py sia corretto")
        print("  2. Il file credenziali esista")
        print("  3. Il Service Account abbia accesso al Google Sheet")
        return

    print()
    print("📋 Creazione fogli...")

    created = 0
    skipped = 0

    for name, config in SHEETS_STRUCTURE.items():
        result = create_worksheet(sheet, name, config)
        if result is not None:
            created += 1
        else:
            skipped += 1

    print()
    print("=" * 60)
    print("🎉 INIZIALIZZAZIONE COMPLETATA!")
    print("=" * 60)
    print(f"  ✅ Fogli creati: {created}")
    print(f"  ⏭️  Fogli esistenti (skip): {skipped}")
    print()
    print("📝 Prossimi passi:")
    print("  1. Verifica i fogli su Google Sheets")
    print("  2. Modifica Config con le tue stagioni")
    print("  3. Esegui 'python check_setup.py' per verificare")
    print("  4. Importa il primo torneo!")
    print()


if __name__ == "__main__":
    main()
