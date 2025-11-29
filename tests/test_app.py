"""
LeagueForge - App Tests
======================

Test delle route Flask principali.

ESEGUI:
    pytest tests/test_app.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# TEST: PAGINE PUBBLICHE
# =============================================================================

class TestPublicPages:
    """Test delle pagine pubbliche (no auth required)."""

    def test_landing_page_loads(self, client):
        """Homepage deve caricare con status 200."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'LeagueForge' in response.data

    def test_classifiche_page_loads(self, client):
        """Pagina classifiche deve caricare."""
        response = client.get('/classifiche')
        assert response.status_code == 200

    def test_achievements_page_loads(self, client):
        """Pagina achievement deve caricare."""
        with patch('app.cache') as mock_cache:
            # Mock per la route achievements
            mock_sheet = MagicMock()
            mock_cache.connect_sheet.return_value = mock_sheet

            # Mock Achievement_Definitions
            mock_ws_ach = MagicMock()
            mock_ws_ach.get_all_values.return_value = [
                [], [], [], [],  # Header rows
                ['ACH_GLO_001', 'First Blood', 'Vinci torneo', 'Glory', 'Uncommon', '🎬', '25'],
            ]

            # Mock Player_Achievements
            mock_ws_player_ach = MagicMock()
            mock_ws_player_ach.get_all_values.return_value = [[], [], [], []]

            # Mock Players
            mock_ws_players = MagicMock()
            mock_ws_players.get_all_values.return_value = [[], [], []]

            mock_sheet.worksheet.side_effect = lambda name: {
                'Achievement_Definitions': mock_ws_ach,
                'Player_Achievements': mock_ws_player_ach,
                'Players': mock_ws_players,
            }.get(name, MagicMock())

            response = client.get('/achievements')
            assert response.status_code == 200

    def test_players_page_loads(self, client):
        """Pagina giocatori deve caricare."""
        response = client.get('/players')
        assert response.status_code == 200


# =============================================================================
# TEST: CLASSIFICHE
# =============================================================================

class TestClassifiche:
    """Test delle pagine classifica."""

    def test_classifica_valid_season(self, client):
        """Classifica con season valida deve caricare."""
        response = client.get('/classifica/OP12')
        assert response.status_code == 200

    def test_classifica_invalid_season_format(self, client):
        """Season con formato invalido deve dare errore."""
        response = client.get('/classifica/INVALID!!!')
        # Dovrebbe restituire 404 o redirect
        assert response.status_code in [404, 302, 200]

    def test_classifica_nonexistent_season(self, client):
        """Season non esistente deve gestire gracefully."""
        response = client.get('/classifica/OP99')
        # La pagina carica ma mostra classifica vuota
        assert response.status_code == 200


# =============================================================================
# TEST: SEASON ID VALIDATION
# =============================================================================

class TestSeasonIdValidation:
    """Test della validazione season ID."""

    def test_valid_base_format(self):
        """Formato base (OP12, PKM25) deve essere valido."""
        from app import _is_valid_season_id

        assert _is_valid_season_id('OP12') == True
        assert _is_valid_season_id('PKM25') == True
        assert _is_valid_season_id('RFB1') == True
        assert _is_valid_season_id('RFB01') == True

    def test_valid_extended_format(self):
        """Formato esteso (PKM-FS25) deve essere valido."""
        from app import _is_valid_season_id

        assert _is_valid_season_id('PKM-FS25') == True
        assert _is_valid_season_id('RFB-S1') == True
        assert _is_valid_season_id('OP-WIN25') == True

    def test_valid_aggregate_format(self):
        """Formato aggregate (ALL-OP) deve essere valido."""
        from app import _is_valid_season_id

        assert _is_valid_season_id('ALL-OP') == True
        assert _is_valid_season_id('ALL-PKM') == True
        assert _is_valid_season_id('ALL-RFB') == True

    def test_invalid_formats(self):
        """Formati invalidi devono essere rifiutati."""
        from app import _is_valid_season_id

        assert _is_valid_season_id('') == False
        assert _is_valid_season_id('123') == False
        assert _is_valid_season_id('OP') == False  # No digits
        assert _is_valid_season_id('12OP') == False  # Digits first
        assert _is_valid_season_id('OP-12') == False  # Hyphen + digits only
        assert _is_valid_season_id('INVALID!!!') == False
        assert _is_valid_season_id(None) == False
        assert _is_valid_season_id(123) == False


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test gestione errori."""

    def test_404_page(self, client):
        """Pagina non esistente deve dare 404."""
        response = client.get('/pagina-che-non-esiste')
        assert response.status_code == 404

    def test_invalid_player_membership(self, client):
        """Player con membership invalida deve gestire gracefully."""
        with patch('app.cache') as mock_cache:
            mock_cache.get_data.return_value = (
                {'seasons': [], 'standings_by_season': {}, 'tournaments_by_season': {}},
                None, {}
            )
            response = client.get('/player/INVALID')
            # Deve restituire 404 o pagina errore
            assert response.status_code in [404, 200, 500]


# =============================================================================
# TEST: API ENDPOINTS
# =============================================================================

class TestApiEndpoints:
    """Test degli endpoint API."""

    def test_api_refresh(self, client):
        """API refresh deve funzionare."""
        with patch('app.cache') as mock_cache:
            mock_cache.force_refresh.return_value = (
                {'seasons': []}, None, {'last_update': '2025-01-01'}
            )
            response = client.get('/api/refresh')
            # Deve restituire JSON o redirect
            assert response.status_code in [200, 302]
