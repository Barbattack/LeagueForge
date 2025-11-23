"""
TanaLeague - Achievement Tests
==============================

Test della logica achievement.

ESEGUI:
    pytest tests/test_achievements.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# TEST: SIMPLE ACHIEVEMENTS (Contatori)
# =============================================================================

class TestSimpleAchievements:
    """Test achievement basati su contatori semplici."""

    def test_check_tournaments_played_unlocks(self, mock_achievement_definitions):
        """Achievement per tornei giocati deve sbloccarsi."""
        from achievements import check_simple_achievements

        stats = {
            'tournaments_played': 15,
            'tournament_wins': 0,
            'top8_count': 0,
        }
        unlocked = set()  # Nessun achievement già sbloccato

        to_unlock = check_simple_achievements(
            stats, mock_achievement_definitions, unlocked
        )

        # Deve sbloccare Debutto (1 torneo) e Veteran (15 tornei)
        unlock_ids = [u[0] for u in to_unlock]
        assert 'ACH_LEG_001' in unlock_ids  # Debutto
        assert 'ACH_LEG_003' in unlock_ids  # Veteran

    def test_check_tournament_wins_unlocks(self, mock_achievement_definitions):
        """Achievement per vittorie deve sbloccarsi."""
        from achievements import check_simple_achievements

        stats = {
            'tournaments_played': 5,
            'tournament_wins': 1,
            'top8_count': 3,
        }
        unlocked = set()

        to_unlock = check_simple_achievements(
            stats, mock_achievement_definitions, unlocked
        )

        # Deve sbloccare First Blood (1 vittoria)
        unlock_ids = [u[0] for u in to_unlock]
        assert 'ACH_GLO_001' in unlock_ids  # First Blood

    def test_already_unlocked_not_duplicated(self, mock_achievement_definitions):
        """Achievement già sbloccati non devono essere duplicati."""
        from achievements import check_simple_achievements

        stats = {
            'tournaments_played': 20,
            'tournament_wins': 5,
            'top8_count': 10,
        }
        # Già sbloccati
        unlocked = {'ACH_LEG_001', 'ACH_LEG_003', 'ACH_GLO_001'}

        to_unlock = check_simple_achievements(
            stats, mock_achievement_definitions, unlocked
        )

        # Non deve sbloccare nulla (tutti già unlocked)
        assert len(to_unlock) == 0

    def test_not_enough_stats_no_unlock(self, mock_achievement_definitions):
        """Stats insufficienti non devono sbloccare achievement."""
        from achievements import check_simple_achievements

        stats = {
            'tournaments_played': 0,
            'tournament_wins': 0,
            'top8_count': 0,
        }
        unlocked = set()

        to_unlock = check_simple_achievements(
            stats, mock_achievement_definitions, unlocked
        )

        # Non deve sbloccare nulla
        assert len(to_unlock) == 0


# =============================================================================
# TEST: PLAYER STATS CALCULATION
# =============================================================================

class TestPlayerStatsCalculation:
    """Test calcolo statistiche giocatore."""

    def test_calculate_basic_stats(self):
        """Calcolo stats base deve funzionare."""
        # Mock sheet e dati
        mock_sheet = MagicMock()

        # Mock Config (per ARCHIVED seasons)
        mock_config = MagicMock()
        mock_config.get_all_values.return_value = [
            [], [], [], [],  # Header
            ['OP12', 'OP', 'One Piece S12', '12', 'ACTIVE'],
            ['OP11', 'OP', 'One Piece S11', '11', 'ARCHIVED'],
        ]

        # Mock Results
        mock_results = MagicMock()
        mock_results.get_all_values.return_value = [
            [], [], [],  # Header
            # season_id, tournament_id, membership, rank, ...
            ['OP12', 'OP12_2025-01-15', '0000012345', '1', '9', '65', '3', '15', '18', 'Mario', '3', '0', '0'],
            ['OP12', 'OP12_2025-01-22', '0000012345', '3', '6', '55', '2', '13', '15', 'Mario', '2', '0', '1'],
            ['OP11', 'OP11_2024-01-01', '0000012345', '1', '9', '60', '3', '15', '18', 'Mario', '3', '0', '0'],  # ARCHIVED
        ]

        mock_sheet.worksheet.side_effect = lambda name: {
            'Config': mock_config,
            'Results': mock_results,
        }.get(name, MagicMock())

        with patch('achievements.sheet', mock_sheet):
            from achievements import calculate_player_stats

            stats = calculate_player_stats(mock_sheet, '0000012345', tcg='OP')

            # ARCHIVED season (OP11) non deve essere contata
            assert stats['tournaments_played'] == 2  # Solo OP12
            assert stats['tournament_wins'] == 1  # Solo rank 1 in OP12


# =============================================================================
# TEST: ARCHIVED SEASONS EXCLUSION
# =============================================================================

class TestArchivedSeasonsExclusion:
    """Test che stagioni ARCHIVED siano escluse."""

    def test_archived_seasons_not_counted(self):
        """Risultati da stagioni ARCHIVED non devono contare."""
        mock_sheet = MagicMock()

        # Config con una stagione ARCHIVED
        mock_config = MagicMock()
        mock_config.get_all_values.return_value = [
            [], [], [], [],
            ['OP12', 'OP', 'S12', '12', 'ACTIVE'],
            ['OLD01', 'OP', 'Old', '1', 'ARCHIVED'],
        ]

        # Results con dati da entrambe le stagioni
        mock_results = MagicMock()
        mock_results.get_all_values.return_value = [
            [], [], [],
            ['OP12', 'T1', '0000012345', '1', '9', '65', '3', '15', '18', 'Test', '3', '0', '0'],
            ['OLD01', 'T2', '0000012345', '1', '9', '65', '3', '15', '18', 'Test', '3', '0', '0'],  # ARCHIVED
            ['OLD01', 'T3', '0000012345', '1', '9', '65', '3', '15', '18', 'Test', '3', '0', '0'],  # ARCHIVED
        ]

        mock_sheet.worksheet.side_effect = lambda name: {
            'Config': mock_config,
            'Results': mock_results,
        }.get(name, MagicMock())

        with patch('achievements.sheet', mock_sheet):
            from achievements import calculate_player_stats

            stats = calculate_player_stats(mock_sheet, '0000012345')

            # Solo 1 torneo (OP12), non 3 (che includerebbero OLD01 ARCHIVED)
            assert stats['tournaments_played'] == 1
            assert stats['tournament_wins'] == 1


# =============================================================================
# TEST: ACHIEVEMENT DETAIL PAGE
# =============================================================================

class TestAchievementDetailPage:
    """Test della pagina dettaglio achievement."""

    def test_achievement_detail_loads(self, client):
        """Pagina dettaglio achievement deve caricare."""
        with patch('app.cache') as mock_cache:
            mock_sheet = MagicMock()
            mock_cache.connect_sheet.return_value = mock_sheet

            # Mock Achievement_Definitions
            mock_ws_ach = MagicMock()
            mock_ws_ach.get_all_values.return_value = [
                [], [], [], [],
                ['ACH_GLO_001', 'First Blood', 'Vinci torneo', 'Glory', 'Uncommon', '🎬', '25'],
            ]

            # Mock Player_Achievements
            mock_ws_player_ach = MagicMock()
            mock_ws_player_ach.get_all_values.return_value = [
                [], [], [], [],
                ['0000012345', 'ACH_GLO_001', '2025-01-15', 'OP12_2025-01-15', ''],
            ]

            # Mock Players
            mock_ws_players = MagicMock()
            mock_ws_players.get_all_values.return_value = [
                [], [], [],
                ['0000012345', 'Mario Rossi', 'OP'],
            ]

            mock_sheet.worksheet.side_effect = lambda name: {
                'Achievement_Definitions': mock_ws_ach,
                'Player_Achievements': mock_ws_player_ach,
                'Players': mock_ws_players,
            }.get(name, MagicMock())

            response = client.get('/achievement/ACH_GLO_001')
            assert response.status_code == 200
            assert b'First Blood' in response.data

    def test_achievement_detail_not_found(self, client):
        """Achievement non esistente deve dare 404."""
        with patch('app.cache') as mock_cache:
            mock_sheet = MagicMock()
            mock_cache.connect_sheet.return_value = mock_sheet

            # Mock vuoto
            mock_ws = MagicMock()
            mock_ws.get_all_values.return_value = [[], [], [], []]
            mock_sheet.worksheet.return_value = mock_ws

            response = client.get('/achievement/NONEXISTENT')
            assert response.status_code in [404, 500]
