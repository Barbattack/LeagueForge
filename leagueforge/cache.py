# -*- coding: utf-8 -*-
"""
LeagueForge - Cache Manager
===========================
Legge Google Sheet ogni N minuti e mantiene cache locale
"""

import gspread
import json
import os
from datetime import datetime, timedelta
from config import SHEET_ID, CACHE_REFRESH_MINUTES, CACHE_FILE
from utils_credentials import get_google_credentials
from sheet_utils import (
    COL_CONFIG, COL_STANDINGS, COL_TOURNAMENTS, COL_ACHIEVEMENT_DEF, COL_PLAYER_ACH, COL_PLAYERS,
    safe_get, safe_int, safe_float
)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetCache:
    def __init__(self):
        self.cache_data = None
        self.last_update = None
        self.load_from_file()
    
    def load_from_file(self):
        """Carica cache da file se esiste"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache_data = data.get('data')
                    self.last_update = datetime.fromisoformat(data.get('timestamp'))
            except:
                pass
    
    def save_to_file(self):
        """Salva cache su file"""
        data = {
            'timestamp': self.last_update.isoformat(),
            'data': self.cache_data
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def needs_refresh(self):
        """Controlla se cache deve essere refreshata"""
        if not self.cache_data or not self.last_update:
            return True
        age = datetime.now() - self.last_update
        return age > timedelta(minutes=CACHE_REFRESH_MINUTES)
    
    def connect_sheet(self):
        """Connette a Google Sheet"""
        creds = get_google_credentials(scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID)
    
    def fetch_data(self):
        """Legge dati da Google Sheet"""
        try:
            sheet = self.connect_sheet()
            
            # Leggi Config per lista stagioni
            ws_config = sheet.worksheet("Config")
            config_data = ws_config.get_all_values()[4:]  # Skip header
            seasons = []
            for row in config_data:
                if row and safe_get(row, COL_CONFIG, 'season_id'):
                    seasons.append({
                        'id': safe_get(row, COL_CONFIG, 'season_id'),
                        'tcg': safe_get(row, COL_CONFIG, 'tcg'),
                        'name': safe_get(row, COL_CONFIG, 'name'),
                        'status': safe_get(row, COL_CONFIG, 'status', 'UNKNOWN'),
                        'next_tournament': safe_get(row, COL_CONFIG, 'next_tournament')
                    })
            
            # Leggi Seasonal_Standings per ogni stagione

            # Leggi Standings (usato per tutte le stagioni: ACTIVE, CLOSED, ARCHIVED)
            standings_by_season = {}
            standings_rows = []
            try:
                ws_standings = sheet.worksheet("Seasonal_Standings_PROV")
                standings_rows = ws_standings.get_all_values()[3:]  # Skip header
            except Exception:
                standings_rows = []

            # Crea mappa per season_id
            standings_map = {}
            for row in standings_rows:
                sid = safe_get(row, COL_STANDINGS, 'season_id')
                if not sid:
                    continue
                standings_map.setdefault(sid, []).append(row)

            # Popola standings_by_season
            standings_by_season = {}
            for s in seasons:
                sid = s.get('id')
                rows = standings_map.get(sid, [])
                standings_by_season[sid] = []
                for row in rows:
                    # Forza membership a 10 cifre con padding zeri (fix per Google Sheets che rimuove zeri iniziali)
                    membership_raw = safe_get(row, COL_STANDINGS, 'membership', '')
                    membership_padded = str(membership_raw).zfill(10) if membership_raw else ''

                    standings_by_season[sid].append({
                        'position': safe_get(row, COL_STANDINGS, 'position', ''),
                        'membership': membership_padded,
                        'name': safe_get(row, COL_STANDINGS, 'name'),
                        'points': safe_float(row, COL_STANDINGS, 'points', 0),
                        'tournaments_played': safe_int(row, COL_STANDINGS, 'tournaments_played', 0),
                        'tournaments_counted': safe_int(row, COL_STANDINGS, 'tournaments_counted', 0),
                        'total_wins': safe_int(row, COL_STANDINGS, 'total_wins', 0),
                        'match_wins': safe_int(row, COL_STANDINGS, 'match_wins', 0),
                        'best_rank': safe_int(row, COL_STANDINGS, 'best_rank', 999),
                        'top8_count': safe_int(row, COL_STANDINGS, 'top8_count', 0)
                    })
            # Leggi Tournaments 
            # Leggi Tournaments per metadata
            ws_tournaments = sheet.worksheet("Tournaments")
            tournaments_data = ws_tournaments.get_all_values()[3:]
            
            tournaments_by_season = {}
            for row in tournaments_data:
                t_id = safe_get(row, COL_TOURNAMENTS, 'tournament_id')
                if not t_id:
                    continue
                season_id = safe_get(row, COL_TOURNAMENTS, 'season_id')
                if season_id not in tournaments_by_season:
                    tournaments_by_season[season_id] = []

                tournaments_by_season[season_id].append({
                    'id': t_id,
                    'tournament_id': t_id,
                    'date': safe_get(row, COL_TOURNAMENTS, 'date'),
                    'participants': safe_int(row, COL_TOURNAMENTS, 'participants', 0),
                    'winner': safe_get(row, COL_TOURNAMENTS, 'winner', '')
                })

            # Leggi Achievement_Definitions
            achievement_defs = {}
            try:
                ws_achievements = sheet.worksheet("Achievement_Definitions")
                achievement_rows = ws_achievements.get_all_values()[4:]
                for row in achievement_rows:
                    ach_id = safe_get(row, COL_ACHIEVEMENT_DEF, 'achievement_id')
                    if ach_id:
                        achievement_defs[ach_id] = {
                            'id': ach_id,
                            'name': safe_get(row, COL_ACHIEVEMENT_DEF, 'name'),
                            'description': safe_get(row, COL_ACHIEVEMENT_DEF, 'description'),
                            'category': safe_get(row, COL_ACHIEVEMENT_DEF, 'category', 'Other'),
                            'rarity': safe_get(row, COL_ACHIEVEMENT_DEF, 'rarity', 'Common'),
                            'emoji': safe_get(row, COL_ACHIEVEMENT_DEF, 'emoji', ''),
                            'points': safe_int(row, COL_ACHIEVEMENT_DEF, 'points', 0)
                        }
            except Exception as e:
                print(f"Warning: Could not load Achievement_Definitions: {e}")

            # Leggi Player_Achievements
            player_achievements = []
            try:
                ws_player_ach = sheet.worksheet("Player_Achievements")
                player_ach_rows = ws_player_ach.get_all_values()[4:]
                for row in player_ach_rows:
                    membership = safe_get(row, COL_PLAYER_ACH, 'membership')
                    ach_id = safe_get(row, COL_PLAYER_ACH, 'achievement_id')
                    if membership and ach_id:
                        # Padding membership number to 10 digits
                        membership_padded = str(membership).zfill(10) if membership else ''
                        player_achievements.append({
                            'membership': membership_padded,
                            'achievement_id': ach_id,
                            'unlocked_date': safe_get(row, COL_PLAYER_ACH, 'unlocked_date', ''),
                            'tournament_id': safe_get(row, COL_PLAYER_ACH, 'tournament_id', '')
                        })
            except Exception as e:
                print(f"Warning: Could not load Player_Achievements: {e}")

            # Leggi Players (per nomi e conteggio totale)
            players = {}
            total_players = 0
            try:
                ws_players = sheet.worksheet("Players")
                players_data = ws_players.get_all_values()[3:]
                for row in players_data:
                    membership = safe_get(row, COL_PLAYERS, 'membership')
                    if membership:
                        # Padding membership number to 10 digits
                        membership_padded = str(membership).zfill(10) if membership else ''
                        players[membership_padded] = {
                            'membership': membership_padded,
                            'name': safe_get(row, COL_PLAYERS, 'name', membership_padded),
                            'tcg': safe_get(row, COL_PLAYERS, 'tcg', '')
                        }
                        total_players += 1
            except Exception as e:
                print(f"Warning: Could not load Players: {e}")

            self.cache_data = {
            'schema_version': 2,
            'seasons': seasons,
            'standings_by_season': standings_by_season,
            'tournaments_by_season': tournaments_by_season,
            'achievement_defs': achievement_defs,
            'player_achievements': player_achievements,
            'players': players,
            'total_players': total_players,
            # legacy aliases (back-compat)
            'standings': standings_by_season,
            'tournaments': tournaments_by_season
        }
            self.last_update = datetime.now()
            self.save_to_file()
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_data(self):
        """Ottieni dati (con refresh automatico se necessario)"""
        if self.needs_refresh():
            success, error = self.fetch_data()
            if not success and not self.cache_data:
                # Primo caricamento fallito e no cache
                return None, error, None
        
        age_minutes = int((datetime.now() - self.last_update).total_seconds() / 60) if self.last_update else 999
        is_stale = age_minutes > CACHE_REFRESH_MINUTES
        
        return self.cache_data, None, (is_stale, age_minutes)

# Istanza globale
cache = SheetCache()
