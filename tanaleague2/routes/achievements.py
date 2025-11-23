# -*- coding: utf-8 -*-
"""
TanaLeague - Achievement Routes
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
        sheet = cache.connect_sheet()

        # Carica achievement definitions
        ws_achievements = sheet.worksheet("Achievement_Definitions")
        achievement_rows = ws_achievements.get_all_values()[4:]

        achievements_by_category = {}
        total_achievements = 0
        total_points = 0

        for row in achievement_rows:
            ach_id = safe_get(row, COL_ACHIEVEMENT_DEF, 'achievement_id')
            if not ach_id:
                continue

            category = safe_get(row, COL_ACHIEVEMENT_DEF, 'category', 'Other')
            if category not in achievements_by_category:
                achievements_by_category[category] = []

            ach = {
                'id': ach_id,
                'name': safe_get(row, COL_ACHIEVEMENT_DEF, 'name'),
                'description': safe_get(row, COL_ACHIEVEMENT_DEF, 'description'),
                'category': category,
                'rarity': safe_get(row, COL_ACHIEVEMENT_DEF, 'rarity', 'Common'),
                'emoji': safe_get(row, COL_ACHIEVEMENT_DEF, 'emoji', ''),
                'points': safe_int(row, COL_ACHIEVEMENT_DEF, 'points', 0)
            }

            achievements_by_category[category].append(ach)
            total_achievements += 1
            total_points += ach['points']

        # Calcola % di unlock per ogni achievement
        ws_player_ach = sheet.worksheet("Player_Achievements")
        player_ach_rows = ws_player_ach.get_all_values()[4:]

        unlock_counts = {}
        for row in player_ach_rows:
            ach_id = safe_get(row, COL_PLAYER_ACH, 'achievement_id')
            if ach_id:
                unlock_counts[ach_id] = unlock_counts.get(ach_id, 0) + 1

        # Conta giocatori totali
        ws_players = sheet.worksheet("Players")
        total_players = len([r for r in ws_players.get_all_values()[3:] if safe_get(r, COL_PLAYERS, 'membership')])

        # Aggiungi % unlock agli achievement
        for category in achievements_by_category:
            for ach in achievements_by_category[category]:
                unlocks = unlock_counts.get(ach['id'], 0)
                ach['unlock_count'] = unlocks
                ach['unlock_percentage'] = (unlocks / total_players * 100) if total_players > 0 else 0

        # Ordina categorie per priorità
        category_order = ['Glory', 'Giant Slayer', 'Consistency', 'Legacy', 'Wildcards', 'Seasonal', 'Heartbreak']
        ordered_categories = []
        for cat in category_order:
            if cat in achievements_by_category:
                ordered_categories.append((cat, achievements_by_category[cat]))
        # Aggiungi eventuali categorie rimanenti
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
        sheet = cache.connect_sheet()

        # 1. Carica info achievement da Achievement_Definitions
        ws_achievements = sheet.worksheet("Achievement_Definitions")
        achievement_rows = ws_achievements.get_all_values()[4:]

        achievement = None
        for row in achievement_rows:
            if safe_get(row, COL_ACHIEVEMENT_DEF, 'achievement_id') == ach_id:
                achievement = {
                    'id': ach_id,
                    'name': safe_get(row, COL_ACHIEVEMENT_DEF, 'name'),
                    'description': safe_get(row, COL_ACHIEVEMENT_DEF, 'description'),
                    'category': safe_get(row, COL_ACHIEVEMENT_DEF, 'category', 'Other'),
                    'rarity': safe_get(row, COL_ACHIEVEMENT_DEF, 'rarity', 'Common'),
                    'emoji': safe_get(row, COL_ACHIEVEMENT_DEF, 'emoji', ''),
                    'points': safe_int(row, COL_ACHIEVEMENT_DEF, 'points', 0)
                }
                break

        if not achievement:
            return render_template('error.html', error='Achievement non trovato'), 404

        # 2. Carica tutti i player che hanno sbloccato questo achievement
        ws_player_ach = sheet.worksheet("Player_Achievements")
        player_ach_rows = ws_player_ach.get_all_values()[4:]

        unlocks_raw = []
        for row in player_ach_rows:
            if safe_get(row, COL_PLAYER_ACH, 'achievement_id') == ach_id:
                unlocks_raw.append({
                    'membership': safe_get(row, COL_PLAYER_ACH, 'membership'),
                    'unlocked_date': safe_get(row, COL_PLAYER_ACH, 'unlocked_date', ''),
                    'tournament_id': safe_get(row, COL_PLAYER_ACH, 'tournament_id', '')
                })

        # 3. Carica nomi giocatori da Players sheet
        ws_players = sheet.worksheet("Players")
        players_data = ws_players.get_all_values()[3:]

        player_names = {}
        for row in players_data:
            membership = safe_get(row, COL_PLAYERS, 'membership')
            if membership:
                player_names[membership] = safe_get(row, COL_PLAYERS, 'name', membership)

        total_players = len([r for r in players_data if safe_get(r, COL_PLAYERS, 'membership')])

        # 4. Arricchisci unlocks con nomi e ordina per data
        unlocks = []
        for u in unlocks_raw:
            unlocks.append({
                'membership': u['membership'],
                'name': player_names.get(u['membership'], u['membership']),
                'unlocked_date': u['unlocked_date'],
                'tournament_id': u['tournament_id']
            })

        # Ordina per data (piu vecchi prima = primi a sbloccare)
        def parse_date(d):
            try:
                from datetime import datetime
                return datetime.strptime(d, '%Y-%m-%d')
            except:
                from datetime import datetime
                return datetime.max

        unlocks.sort(key=lambda x: parse_date(x['unlocked_date']))

        # 5. Calcola statistiche
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
