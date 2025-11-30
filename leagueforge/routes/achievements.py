# -*- coding: utf-8 -*-
"""
LeagueForge - Achievement Routes
===============================

Blueprint per le route achievement:
- /achievements - Catalogo completo achievement
- /achievement/<ach_id> - Dettaglio singolo achievement
"""

from flask import Blueprint, render_template

from cache import cache
from sheet_utils import (
    COL_ACHIEVEMENT_DEF, COL_PLAYER_ACH, COL_PLAYERS,
    safe_get, safe_int
)


# =============================================================================
# BLUEPRINT DEFINITION
# =============================================================================

achievements_bp = Blueprint('achievements', __name__, template_folder='../templates')


# =============================================================================
# ROUTES
# =============================================================================

@achievements_bp.route('/achievements')
def achievements_list():
    """
    Pagina catalogo achievement completo.

    Mostra tutti i 40+ achievement disponibili organizzati per categoria:
    - Glory (vittorie e trionfi)
    - Giant Slayer (battere i migliori)
    - Consistency (serie positive)
    - Legacy (milestone lifetime)
    - Wildcards (achievement bizzarri)
    - Seasonal (performance stagionali)
    - Heartbreak (sfortune e quasi vittorie)

    Per ogni achievement visualizza:
    - Emoji + Nome
    - Descrizione unlock condition
    - Rarity badge (Common -> Legendary)
    - Punti assegnati
    - Unlock percentage (quanti giocatori l'hanno sbloccato)
    - Progress bar visuale

    Returns:
        Template: achievements.html con catalogo completo
    """
    try:
        # Get data from cache (refreshes automatically if needed)
        data, err, meta = cache.get_data()
        if not data:
            return render_template('error.html', error=err or 'Cache non disponibile'), 500

        achievement_defs = data.get('achievement_defs', {})
        player_achievements = data.get('player_achievements', [])
        total_players = data.get('total_players', 0)

        # Organize achievements by category
        achievements_by_category = {}
        total_achievements = 0
        total_points = 0

        for ach_id, ach in achievement_defs.items():
            category = ach.get('category', 'Other')
            if category not in achievements_by_category:
                achievements_by_category[category] = []

            achievements_by_category[category].append(ach)
            total_achievements += 1
            total_points += ach.get('points', 0)

        # Calculate unlock percentage for each achievement
        unlock_counts = {}
        for player_ach in player_achievements:
            ach_id = player_ach.get('achievement_id')
            if ach_id:
                unlock_counts[ach_id] = unlock_counts.get(ach_id, 0) + 1

        # Add unlock percentage to achievements
        for category in achievements_by_category:
            for ach in achievements_by_category[category]:
                unlocks = unlock_counts.get(ach['id'], 0)
                ach['unlock_count'] = unlocks
                ach['unlock_percentage'] = (unlocks / total_players * 100) if total_players > 0 else 0

        # Sort categories by priority
        category_order = ['Glory', 'Giant Slayer', 'Consistency', 'Legacy', 'Wildcards', 'Seasonal', 'Heartbreak']
        ordered_categories = []
        for cat in category_order:
            if cat in achievements_by_category:
                ordered_categories.append((cat, achievements_by_category[cat]))
        # Add remaining categories
        for cat, achs in achievements_by_category.items():
            if cat not in category_order:
                ordered_categories.append((cat, achs))

        return render_template('achievements.html',
                               achievements_by_category=ordered_categories,
                               total_achievements=total_achievements,
                               total_points=total_points,
                               total_players=total_players)

    except Exception as e:
        return render_template('error.html', error=f'Errore caricamento achievement: {str(e)}'), 500


@achievements_bp.route('/achievement/<ach_id>')
def achievement_detail(ach_id):
    """
    Pagina dettaglio singolo achievement.

    Mostra:
    - Info achievement (emoji, nome, descrizione, rarity, punti)
    - Lista giocatori che l'hanno sbloccato con:
      - Badge "First!" per il primo a sbloccarlo
      - Data di unlock
      - Link al profilo giocatore
    - Statistiche: X su Y giocatori (Z%)

    Args:
        ach_id: ID achievement (es. "glory_first_blood")

    Returns:
        Template: achievement_detail.html
        404: Se achievement non trovato
    """
    try:
        # Get data from cache (refreshes automatically if needed)
        data, err, meta = cache.get_data()
        if not data:
            return render_template('error.html', error=err or 'Cache non disponibile'), 500

        achievement_defs = data.get('achievement_defs', {})
        player_achievements = data.get('player_achievements', [])
        players = data.get('players', {})
        total_players = data.get('total_players', 0)

        # 1. Get achievement info
        achievement = achievement_defs.get(ach_id)
        if not achievement:
            return render_template('error.html', error='Achievement non trovato'), 404

        # 2. Get all players who unlocked this achievement
        unlocks = []
        for player_ach in player_achievements:
            if player_ach.get('achievement_id') == ach_id:
                membership = player_ach.get('membership', '')
                player_info = players.get(membership, {})
                unlocks.append({
                    'membership': membership,
                    'name': player_info.get('name', membership),
                    'unlocked_date': player_ach.get('unlocked_date', ''),
                    'tournament_id': player_ach.get('tournament_id', '')
                })

        # 3. Sort by date (oldest first = first to unlock)
        def parse_date(d):
            try:
                from datetime import datetime
                return datetime.strptime(d, '%Y-%m-%d')
            except:
                from datetime import datetime
                return datetime.max

        unlocks.sort(key=lambda x: parse_date(x['unlocked_date']))

        # 4. Calculate statistics
        unlock_count = len(unlocks)
        unlock_percentage = (unlock_count / total_players * 100) if total_players > 0 else 0

        return render_template('achievement_detail.html',
                               achievement=achievement,
                               unlocks=unlocks,
                               unlock_count=unlock_count,
                               total_players=total_players,
                               unlock_percentage=unlock_percentage)

    except Exception as e:
        return render_template('error.html', error=f'Errore caricamento achievement: {str(e)}'), 500
