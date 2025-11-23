"""
TanaLeague - Test Configuration
===============================

Fixtures condivise per tutti i test.

USO:
    pytest                      # Esegui tutti i test
    pytest tests/test_app.py    # Esegui test specifici
    pytest -v                   # Output verboso
    pytest --cov=tanaleague2    # Con coverage report
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Aggiungi tanaleague2 al path
sys.path.insert(0, str(Path(__file__).parent.parent / "tanaleague2"))


# =============================================================================
# FIXTURES - FLASK APP
# =============================================================================

@pytest.fixture
def app():
    """
    Crea istanza Flask app per testing.
    Configura l'app in modalità test (no cache reale).
    """
    # Mock cache prima di importare app
    with patch('cache.cache') as mock_cache:
        # Configura mock cache
        mock_cache.get_data.return_value = (
            get_mock_cache_data(),
            None,  # No error
            {'last_update': '2025-01-01 12:00:00'}
        )
        mock_cache.connect_sheet.return_value = MagicMock()

        from app import app as flask_app
        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False

        yield flask_app


@pytest.fixture
def client(app):
    """Client Flask per fare richieste HTTP di test."""
    return app.test_client()


# =============================================================================
# FIXTURES - MOCK DATA
# =============================================================================

def get_mock_cache_data():
    """Dati mock che simulano la cache."""
    return {
        'schema_version': 2,
        'seasons': [
            {'id': 'OP12', 'tcg': 'OP', 'name': 'One Piece S12', 'status': 'ACTIVE'},
            {'id': 'PKM-FS25', 'tcg': 'PKM', 'name': 'Pokemon Fall 2025', 'status': 'ACTIVE'},
            {'id': 'RFB01', 'tcg': 'RFB', 'name': 'Riftbound S1', 'status': 'ACTIVE'},
        ],
        'standings_by_season': {
            'OP12': [
                {'position': 1, 'membership': '0000012345', 'name': 'Mario Rossi',
                 'points': 45, 'tournaments': 5, 'wins': 2},
                {'position': 2, 'membership': '0000067890', 'name': 'Luigi Verdi',
                 'points': 38, 'tournaments': 4, 'wins': 1},
            ],
            'PKM-FS25': [
                {'position': 1, 'membership': '0000011111', 'name': 'Anna Bianchi',
                 'points': 30, 'tournaments': 3, 'wins': 1},
            ],
            'RFB01': [],
        },
        'tournaments_by_season': {
            'OP12': [
                {'id': 'OP12_2025-01-15', 'date': '2025-01-15', 'participants': 16},
                {'id': 'OP12_2025-01-22', 'date': '2025-01-22', 'participants': 12},
            ],
            'PKM-FS25': [
                {'id': 'PKM-FS25_2025-01-20', 'date': '2025-01-20', 'participants': 8},
            ],
            'RFB01': [],
        },
    }


@pytest.fixture
def mock_cache_data():
    """Fixture che restituisce dati mock."""
    return get_mock_cache_data()


@pytest.fixture
def mock_player_data():
    """Dati mock per un giocatore."""
    return {
        'membership': '0000012345',
        'name': 'Mario Rossi',
        'tcg': 'OP',
        'tournaments_played': 10,
        'tournament_wins': 3,
        'top8_count': 7,
        'total_points': 120,
        'results': [
            {'tournament_id': 'OP12_2025-01-15', 'rank': 1, 'points': 18},
            {'tournament_id': 'OP12_2025-01-22', 'rank': 3, 'points': 14},
        ]
    }


@pytest.fixture
def mock_achievement_definitions():
    """Definizioni achievement mock."""
    return {
        'ACH_GLO_001': {
            'id': 'ACH_GLO_001',
            'name': 'First Blood',
            'description': 'Vinci il tuo primo torneo',
            'category': 'Glory',
            'rarity': 'Uncommon',
            'emoji': '🎬',
            'points': 25,
            'requirement_type': 'tournament_wins',
            'requirement_value': '1'
        },
        'ACH_LEG_001': {
            'id': 'ACH_LEG_001',
            'name': 'Debutto',
            'description': 'Gioca il tuo primo torneo',
            'category': 'Legacy',
            'rarity': 'Common',
            'emoji': '🎮',
            'points': 10,
            'requirement_type': 'tournaments_played',
            'requirement_value': '1'
        },
        'ACH_LEG_003': {
            'id': 'ACH_LEG_003',
            'name': 'Veteran',
            'description': 'Gioca 15 tornei',
            'category': 'Legacy',
            'rarity': 'Uncommon',
            'emoji': '🎖️',
            'points': 25,
            'requirement_type': 'tournaments_played',
            'requirement_value': '15'
        },
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def assert_page_loads(client, url, expected_status=200):
    """Helper: verifica che una pagina carichi correttamente."""
    response = client.get(url)
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code} for {url}"
    return response


def assert_contains(response, text):
    """Helper: verifica che la risposta contenga un testo."""
    assert text.encode() in response.data, \
        f"Expected '{text}' in response"
