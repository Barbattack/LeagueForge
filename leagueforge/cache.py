# -*- coding: utf-8 -*-
"""
LeagueForge - Cache Manager
===========================
Legge Google Sheet ogni N minuti e mantiene cache locale
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime, timedelta
from config import SHEET_ID, CREDENTIALS_FILE, CREDENTIALS_JSON, CACHE_REFRESH_MINUTES, CACHE_FILE
from sheet_utils import (
    COL_CONFIG, COL_STANDINGS, COL_TOURNAMENTS,
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
        """
        Connette a Google Sheet.

        Supporta due modalità:
        1. CREDENTIALS_JSON (env var su Render): JSON inline come stringa
        2. CREDENTIALS_FILE (locale): File service account JSON
        """
        # Priorità a CREDENTIALS_JSON (env var per Render)
        if CREDENTIALS_JSON:
            try:
                creds_dict = json.loads(CREDENTIALS_JSON)
                creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            except json.JSONDecodeError as e:
                raise ValueError(f"CREDENTIALS_JSON non è un JSON valido: {e}")
        else:
            # Fallback: usa file locale
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Credentials non trovate! Configura GOOGLE_CREDENTIALS_JSON env var "
                    f"oppure crea file {CREDENTIALS_FILE}"
                )
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)

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
            
            # Leggi Standings PROV e FINAL (se esistono)
            standings_by_season = { }
            prov_rows = []
            final_rows = []
            try:
                ws_prov = sheet.worksheet("Seasonal_Standings_PROV")
                prov_rows = ws_prov.get_all_values()[3:]  # Skip header
            except Exception:
                prov_rows = []
            try:
                ws_final = sheet.worksheet("Seasonal_Standings_FINAL")
                final_rows = ws_final.get_all_values()[3:]
            except Exception:
                final_rows = []

            # Crea mappe per season_id
            prov_map = {}
            for row in prov_rows:
                sid = safe_get(row, COL_STANDINGS, 'season_id')
                if not sid:
                    continue
                prov_map.setdefault(sid, []).append(row)
            final_map = {}
            for row in final_rows:
                sid = safe_get(row, COL_STANDINGS, 'season_id')
                if not sid:
                    continue
                final_map.setdefault(sid, []).append(row)

            # Scegli sheet giusto in base allo status stagione
            standings_by_season = {}
            for s in seasons:
                sid = s.get('id')
                status = (s.get('status') or '').upper()
                rows = prov_map.get(sid, []) if status == 'ACTIVE' else final_map.get(sid, [])
                # Fallback: se FINAL vuota, usa PROV; se PROV vuota, usa FINAL
                if status == 'CLOSED' and not rows:
                    rows = final_map.get(sid, []) or prov_map.get(sid, [])
                if status != 'CLOSED' and not rows:
                    rows = prov_map.get(sid, []) or final_map.get(sid, [])
                standings_by_season[sid] = []
                for row in rows:
                    standings_by_season[sid].append({
                        'position': safe_get(row, COL_STANDINGS, 'position', ''),
                        'membership': safe_get(row, COL_STANDINGS, 'membership'),
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
            
            self.cache_data = {
            'schema_version': 2,
            'seasons': seasons,
            'standings_by_season': standings_by_season,
            'tournaments_by_season': tournaments_by_season,
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
