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
COL_RESULTS = {
    'tournament_id': 0,
    'season_id': 1,
    'membership': 2,
    'name': 3,
    'rank': 4,
    'points': 5,
    'record': 6,
    'match_w': 7,
    'match_l': 8,
    'match_t': 9,
    'omw': 10,
    'deck': 11
}

# Players sheet
COL_PLAYERS = {
    'membership': 0,
    'name': 1,
    'tcg': 2,
    'tournaments_total': 3,
    'wins_total': 4,
    'points_total': 5
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
