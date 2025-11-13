# -*- coding: utf-8 -*-
"""
TanaLeague - Cache Manager
===========================
Legge Google Sheet ogni N minuti e mantiene cache locale
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime, timedelta
from config import SHEET_ID, CREDENTIALS_FILE, CACHE_REFRESH_MINUTES, CACHE_FILE

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
                if row and row[0]:
                    seasons.append({
                        'id': row[0],
                        'tcg': row[1],
                        'name': row[2],
                        'status': row[4] if len(row) > 4 else 'UNKNOWN',
                        'next_tournament': row[11] if len(row) > 11 and row[11] else None
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
                if not row or not row[0]:
                    continue
                sid = row[0]
                prov_map.setdefault(sid, []).append(row)
            final_map = {}
            for row in final_rows:
                if not row or not row[0]:
                    continue
                sid = row[0]
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
                        'position': row[10] if len(row) > 10 else '',
                        'membership': row[1],
                        'name': row[2],
                        'points': float(row[3]) if row[3] else 0,
                        'tournaments_played': int(row[4]) if row[4] else 0,
                        'tournaments_counted': int(row[5]) if row[5] else 0,
                        'total_wins': int(row[6]) if row[6] else 0,
                        'match_wins': int(row[7]) if row[7] else 0,
                        'best_rank': int(row[8]) if row[8] else 999,
                        'top8_count': int(row[9]) if row[9] else 0
                    })
            # Leggi Tournaments 
            # Leggi Tournaments per metadata
            ws_tournaments = sheet.worksheet("Tournaments")
            tournaments_data = ws_tournaments.get_all_values()[3:]
            
            tournaments_by_season = {}
            for row in tournaments_data:
                if not row or not row[0]:
                    continue
                season_id = row[1]
                if season_id not in tournaments_by_season:
                    tournaments_by_season[season_id] = []
                
                tournaments_by_season[season_id].append({
                    'id': row[0],
                    'date': row[2],
                    'participants': int(row[3]) if row[3] else 0,
                    'winner': row[7] if len(row) > 7 else ''
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
