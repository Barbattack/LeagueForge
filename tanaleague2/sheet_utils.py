# -*- coding: utf-8 -*-
"""
Sheet utilities - Mappature colonne e row wrapper.
Elimina fragilità da row[x] hardcoded.
"""

# =============================================================================
# MAPPATURE COLONNE - Aggiorna QUI se cambi struttura fogli
# =============================================================================

# Config sheet (skip 4 righe header)
COL_CONFIG = {
    'season_id': 0,
    'tcg': 1,
    'name': 2,
    'season_num': 3,
    'status': 4,
    'next_tournament': 11
}

# Seasonal_Standings (skip 3 righe header)
COL_STANDINGS = {
    'season_id': 0,
    'membership': 1,
    'name': 2,
    'points': 3,
    'tournaments_played': 4,
    'tournaments_counted': 5,
    'total_wins': 6,
    'match_wins': 7,
    'best_rank': 8,
    'top8_count': 9,
    'position': 10
}

# Tournaments sheet (skip 3 righe header)
COL_TOURNAMENTS = {
    'tournament_id': 0,
    'season_id': 1,
    'date': 2,
    'participants': 3,
    'format': 4,
    'rounds': 5,
    'location': 6,
    'winner': 7
}

# Results sheet (skip 3 righe header)
# NOTA: La struttura varia per TCG, questa è la mappatura base
COL_RESULTS = {
    'season_id': 0,
    'tournament_id': 1,
    'membership': 2,
    'rank': 3,
    'points': 4,
    'name': 5,
    'record': 6,
    'match_w': 7,
    'match_l': 8,
    'match_t': 9,
    'omw': 10,
    'deck': 11
}

# Players sheet (skip 3 righe header)
COL_PLAYERS = {
    'membership': 0,
    'name': 1,
    'tcg': 2,
    'first_seen': 3,
    'last_seen': 4,
    'total_tournaments': 5,
    'tournament_wins': 6,
    'match_w': 7,
    'match_t': 8,
    'match_l': 9,
    'total_points': 10
}

# Achievement_Definitions sheet (skip 4 righe header)
COL_ACHIEVEMENT_DEF = {
    'achievement_id': 0,
    'name': 1,
    'description': 2,
    'category': 3,
    'rarity': 4,
    'emoji': 5,
    'points': 6,
    'requirement_type': 7,
    'requirement_value': 8
}

# Player_Achievements sheet
COL_PLAYER_ACH = {
    'membership': 0,
    'achievement_id': 1,
    'unlocked_date': 2,
    'tournament_id': 3
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_get(row, col_map, key, default=None):
    """Accesso sicuro a colonna by-name."""
    idx = col_map.get(key)
    if idx is None or idx >= len(row):
        return default
    val = row[idx]
    return val if val != '' else default


def safe_int(row, col_map, key, default=0):
    """Accesso sicuro + conversione int."""
    val = safe_get(row, col_map, key)
    try:
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


def safe_float(row, col_map, key, default=0.0):
    """Accesso sicuro + conversione float."""
    val = safe_get(row, col_map, key)
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default


class SheetRow:
    """Wrapper per accedere a righe Google Sheets con nomi colonna."""

    def __init__(self, row: list, col_map: dict):
        self._row = row
        self._map = col_map

    def get(self, key: str, default=None):
        return safe_get(self._row, self._map, key, default)

    def get_int(self, key: str, default=0):
        return safe_int(self._row, self._map, key, default)

    def get_float(self, key: str, default=0.0):
        return safe_float(self._row, self._map, key, default)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key] if key < len(self._row) else None
        return self.get(key)

    def raw(self):
        return self._row
