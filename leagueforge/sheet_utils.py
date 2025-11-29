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
    'result_id': 0,
    'tournament_id': 1,
    'membership': 2,
    'rank': 3,
    'win_points': 4,
    'omw': 5,
    'points_victory': 6,
    'points_ranking': 7,
    'points_total': 8,
    'name': 9,
    'match_w': 10,
    'match_t': 11,
    'match_l': 12
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

# Player_Stats sheet (skip 3 righe header) - Aggregati pre-calcolati
COL_PLAYER_STATS = {
    'membership': 0,
    'name': 1,
    'tcg': 2,
    'total_tournaments': 3,
    'total_wins': 4,
    'current_streak': 5,
    'best_streak': 6,
    'top8_count': 7,
    'last_rank': 8,
    'last_date': 9,
    'seasons_count': 10,
    'updated_at': 11,
    'total_points': 12
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


def normalize_name(name: str) -> str:
    """Normalizza nome per confronto: lowercase, spazi singoli, strip."""
    if not name:
        return ''
    return ' '.join(name.lower().split())


def fuzzy_match(name1: str, name2: str, threshold: int = 85) -> bool:
    """
    Confronto fuzzy tra due nomi.
    Ritorna True se la similarità è >= threshold (default 85%).

    Gestisce: doppi spazi, accenti diversi, typo minori.
    """
    if not name1 or not name2:
        return False

    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # Match esatto dopo normalizzazione
    if n1 == n2:
        return True

    # Fuzzy matching con rapidfuzz
    try:
        from rapidfuzz import fuzz
        score = fuzz.ratio(n1, n2)
        return score >= threshold
    except ImportError:
        # Fallback se rapidfuzz non installato
        return n1 == n2


def find_best_match(target: str, candidates: list, threshold: int = 85) -> tuple:
    """
    Trova il miglior match per target in una lista di candidati.

    Returns:
        (best_match, score) o (None, 0) se nessun match sopra threshold
    """
    if not target or not candidates:
        return None, 0

    target_norm = normalize_name(target)

    try:
        from rapidfuzz import fuzz
        best_match = None
        best_score = 0

        for candidate in candidates:
            if not candidate:
                continue
            score = fuzz.ratio(target_norm, normalize_name(candidate))
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold:
            return best_match, best_score
        return None, 0
    except ImportError:
        # Fallback esatto
        for candidate in candidates:
            if normalize_name(candidate) == target_norm:
                return candidate, 100
        return None, 0


def validate_sheet_headers(worksheet, col_map: dict, expected_headers: list,
                          header_row_index: int = 2, strict: bool = False) -> dict:
    """
    Valida che gli header del foglio Google Sheets corrispondano al mapping.

    Args:
        worksheet: Worksheet gspread
        col_map: Dizionario mapping (es. COL_PLAYER_STATS)
        expected_headers: Lista header attesi nell'ordine corretto
        header_row_index: Riga degli header (0-indexed, default 2 = riga 3)
        strict: Se True solleva eccezione, altrimenti ritorna warning dict

    Returns:
        dict: {
            'valid': bool,
            'errors': list,
            'warnings': list
        }

    Example:
        result = validate_sheet_headers(
            ws_player_stats,
            COL_PLAYER_STATS,
            ["Membership", "Name", "TCG", ...],
            header_row_index=2
        )
        if not result['valid']:
            print("ERRORI:", result['errors'])
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    try:
        # Leggi riga header
        all_rows = worksheet.get_all_values()
        if len(all_rows) <= header_row_index:
            result['valid'] = False
            result['errors'].append(f"Sheet ha solo {len(all_rows)} righe, impossibile leggere header alla riga {header_row_index + 1}")
            if strict:
                raise ValueError(result['errors'][0])
            return result

        actual_headers = all_rows[header_row_index]

        # Verifica numero colonne
        expected_count = len(expected_headers)
        actual_count = len([h for h in actual_headers if h.strip()])  # Conta solo non vuote

        if actual_count < expected_count:
            msg = f"Mancano {expected_count - actual_count} colonne (attese: {expected_count}, trovate: {actual_count})"
            result['errors'].append(msg)
            result['valid'] = False

        # Verifica ordine e nomi colonne
        for key, expected_idx in col_map.items():
            if expected_idx >= len(expected_headers):
                continue  # Ignora indici fuori range

            expected_name = expected_headers[expected_idx]

            if expected_idx >= len(actual_headers):
                msg = f"Colonna '{key}' (pos {expected_idx}) mancante - atteso '{expected_name}'"
                result['errors'].append(msg)
                result['valid'] = False
                continue

            actual_name = actual_headers[expected_idx].strip()

            # Confronto case-insensitive e normalizzato
            if normalize_name(actual_name) != normalize_name(expected_name):
                msg = f"Colonna {expected_idx} - atteso '{expected_name}', trovato '{actual_name}'"
                result['errors'].append(msg)
                result['valid'] = False

        if strict and not result['valid']:
            error_msg = "❌ VALIDAZIONE HEADER FALLITA:\n" + "\n".join(result['errors'])
            raise ValueError(error_msg)

    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Errore durante validazione: {str(e)}")
        if strict:
            raise

    return result


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
