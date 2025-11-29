# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge v2.0 - Flask Web Application
=================================================================================

Webapp per gestione league TCG multi-gioco (One Piece, Pokemon, Riftbound).

Funzionalità principali:
- Homepage con link ai 3 TCG
- Classifiche stagionali con dropdown selector
- Profili giocatori con storico risultati e achievement sbloccati
- Pagina achievement con catalogo completo e unlock percentages
- Statistiche avanzate (Spotlights, Pulse, Tales, Hall of Fame)
- Sistema cache 5-min per performance Google Sheets API

Architettura:
- Flask routes servono templates Jinja2
- cache.py gestisce connessione Google Sheets + file-based cache
- stats_builder.py calcola statistiche avanzate
- achievements.py gestisce unlock automatico durante import tornei

Note:
- Support BOTH /classifica/<season_id> and /classifica?season=OP12
  per retrocompatibilità con vecchi template
=================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================
from flask import Flask, render_template, redirect, url_for, jsonify, request, flash, session
from cache import cache
from config import SECRET_KEY, DEBUG, SESSION_TIMEOUT
from stats_builder import build_stats
from datetime import timedelta
from sheet_utils import (
    COL_PLAYERS, COL_PLAYER_STATS, COL_ACHIEVEMENT_DEF, COL_PLAYER_ACH,
    validate_sheet_headers
)
# Note: safe_int, safe_float sono definiti localmente in questo file (signature diversa da sheet_utils)


# ============================================================================
# FLASK APP CONFIGURATION
# ============================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_TIMEOUT)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload

# Register Blueprints (modular routes)
from routes import register_blueprints
register_blueprints(app)

@app.context_processor
def inject_defaults():
    """
    Inietta variabili default nel contesto di tutti i template Jinja2.
    Previene crash se un template usa variabile non definita (es. default_stats_scope).
    """
    return {"default_stats_scope": "OP12"}


# ============================================================================
# HELPER FUNCTIONS - Utility generiche
# ============================================================================

# --- Conversione sicura valori da Google Sheets ---
def safe_int(value, default=0):
    """
    Converte valore in int gestendo errori.

    Previene crash quando Google Sheets restituisce valori non numerici
    (es. stringhe, date, celle vuote).

    Args:
        value: Valore da convertire
        default: Valore di ritorno se conversione fallisce (default: 0)

    Returns:
        int: Valore convertito o default

    Esempio:
        safe_int("123") → 123
        safe_int("abc") → 0
        safe_int("2025-11-13") → 0
        safe_int(None) → 0
    """
    try:
        return int(value) if value and str(value).strip() else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """
    Converte valore in float gestendo errori.
    Analogo a safe_int() ma per numeri decimali.

    Args:
        value: Valore da convertire
        default: Valore di ritorno se conversione fallisce (default: 0.0)

    Returns:
        float: Valore convertito o default
    """
    try:
        return float(value) if value and str(value).strip() else default
    except (ValueError, TypeError):
        return default


# --- Jinja2 Filters Custom ---
@app.template_filter('format_player_name')
def format_player_name(name, tcg, membership=''):
    """
    Filtro Jinja2 per formattare nomi giocatori in base al TCG.

    Ogni TCG ha una convenzione di visualizzazione diversa:
    - **One Piece (OP)**: Nome completo "Mario Rossi"
    - **Pokemon (PKM)**: Nome + iniziale cognome "Mario R."
    - **Riftbound (RFB)**: Membership number (nickname)

    Questo filtro viene applicato automaticamente in tutti i template quando
    si usa: {{ player.name | format_player_name(player.tcg, player.membership) }}

    Args:
        name (str): Nome completo giocatore dal Google Sheet
        tcg (str): Codice TCG (OP, PKM, RFB)
        membership (str): Membership number / nickname (per RFB)

    Returns:
        str: Nome formattato secondo convenzione TCG

    Esempi:
        format_player_name("Rossi, Mario", "PKM", "") → "Mario R."
        format_player_name("Rossi Mario", "RFB", "HotelMotel") → "HotelMotel"
        format_player_name("Rossi Mario", "OP", "") → "Rossi Mario"
    """
    if not name:
        return membership or 'N/A'

    tcg_upper = (tcg or '').upper()

    if tcg_upper == 'PKM':
        # Pokemon: "Nome I." - first name + last initial
        parts = name.split()
        if len(parts) >= 2:
            # Assume format "Cognome, Nome" or "Nome Cognome"
            if ',' in name:
                # Format: "Cognome, Nome" -> "Nome C."
                surname, firstname = name.split(',', 1)
                firstname = firstname.strip()
                surname = surname.strip()
                if surname:
                    return f"{firstname} {surname[0]}."
                return firstname
            else:
                # Format: "Nome Cognome" -> "Nome C."
                firstname = parts[0]
                lastname = parts[-1]
                if lastname:
                    return f"{firstname} {lastname[0]}."
                return firstname
        return name

    elif tcg_upper == 'RFB':
        # Riftbound: Mostra il membership number (nickname)
        return membership if membership else name

    else:
        # One Piece e altri: nome completo
        return name

# ---- Safety net + endpoint di test -----------------------------------------
@app.context_processor
def inject_defaults():
    # già presente sopra: lo lascio qui identico per evitare il crash del menu
    return {"default_stats_scope": "OP12"}

@app.get("/ping")
def ping():
    return "pong", 200
# ---------------------------------------------------------------------------


# ---------------------- REFRESH ROBUSTO CACHE/STATS ------------------------
def _normalize_builder_result(res, scope):
    """
    Normalizza l'output del build_stats:
    - se res è un dict con dentro {scope: {...}} ritorna res[scope]
    - se è già "flat" lo lascia così
    - riempie i pezzi mancanti con default sicuri (così Jinja non esplode)
    """
    # estrazione del payload della stagione
    if isinstance(res, dict) and scope in res:
        payload = res[scope]
    else:
        payload = res

    if not isinstance(payload, dict):
        payload = {}

    def ensure(path_keys, default_value):
        d = payload
        for k in path_keys[:-1]:
            if k not in d or not isinstance(d.get(k), dict):
                d[k] = {}
            d = d[k]
        d.setdefault(path_keys[-1], default_value)

    # default per spotlights
    ensure(["spotlights"], {})
    for k in ["mvp", "sharpshooter", "metronome", "phoenix", "big_stage", "closer"]:
        payload["spotlights"].setdefault(k, [])

    # narrative cards
    ensure(["spot_narrative"], [])

    # pulse.kpi
    ensure(["pulse"], {})
    ensure(["pulse", "kpi"], {})
    kpi = payload["pulse"]["kpi"]
    kpi.setdefault("events_total", 0)
    kpi.setdefault("unique_players", 0)         # o "participants_unique" se preferisci
    kpi.setdefault("entries_total", 0)
    kpi.setdefault("avg_participants", 0.0)
    kpi.setdefault("top8_rate", 0.0)
    kpi.setdefault("avg_omw", 0.0)

    # pulse.series
    ensure(["pulse", "series"], {})
    payload["pulse"]["series"].setdefault("entries_per_event", [])
    payload["pulse"]["series"].setdefault("avg_points_per_event", [])

    # tales
    ensure(["tales"], {})
    for k in ["companions", "podium_rivals", "top8_mixture"]:
        payload["tales"].setdefault(k, [])

    # hall of fame
    ensure(["hof"], {})
    for k in ["highest_single_score", "biggest_crowd", "most_balanced", "most_dominated", "fastest_riser"]:
        payload["hof"].setdefault(k, None)

    return payload


def _do_refresh(scope):
    try:
        # il tuo import in alto: from stats_builder import build_stats
        # Provo prima con lista (alcune versioni vogliono ['OP12']), poi con stringa.
        try:
            raw = build_stats([scope])
        except Exception:
            raw = build_stats(scope)

        payload = _normalize_builder_result(raw, scope)

        # Se la V2 è presente, salvo in cache; se non c'è, pazienza.
        try:
            from leagueforge_v2.services.stats_service import write_stats
            write_stats(scope, payload)
        except Exception:
            pass

        return jsonify({"status": "ok", "scope": scope, "keys": list(payload.keys())})
    except Exception as e:
        # NON facciamo più saltare la WSGI: rispondiamo con JSON d'errore
        return jsonify({"status": "error", "message": str(e)}), 500


@app.get("/api/refresh")
def api_refresh_default():
    # refresh di cortesia sulla stagione standard
    return _do_refresh("OP12")


@app.get("/api/stats/refresh/<scope>")
def api_refresh_scope(scope):
    return _do_refresh(scope.strip().upper())
# ---------------------------------------------------------------------------



# ---------- Helpers (used only inside /stats for the dropdown) ----------
def _tcg_code(sid: str) -> str:
    prefix = ''.join(ch for ch in str(sid) if ch.isalpha())
    return prefix.upper()

def _is_valid_season_id(sid: str) -> bool:
    """
    Allow valid season IDs:
    - Base format: OP12, PKM25, RFB1 (letters + digits)
    - Extended format: PKM-FS25, RFB-S1 (letters + hyphen + letters + digits)
    - Aggregate format: ALL-OP, ALL-PKM (ALL- prefix)
    """
    import re
    if not isinstance(sid, str):
        return False
    sid = sid.strip().upper()
    # Base: OP12, PKM25, RFB1
    # Extended: PKM-FS25, RFB-S1
    # Aggregate: ALL-OP, ALL-PKM
    return bool(
        re.match(r'^[A-Z]{2,}\d{1,3}$', sid) or           # OP12, PKM25
        re.match(r'^[A-Z]{2,}-[A-Z]+\d{1,3}$', sid) or    # PKM-FS25, RFB-S1
        re.match(r'^ALL-[A-Z]+$', sid)                     # ALL-OP
    )

def _season_key_desc(sid: str):
    """Sort by TCG prefix then by numeric part DESC (OP12 > OP11 > OP2)."""
    if not isinstance(sid, str):
        return ('', 0)
    prefix = ''.join(ch for ch in sid if ch.isalpha()).upper()
    num_str = ''.join(ch for ch in sid if ch.isdigit())
    try:
        num = int(num_str) if num_str else 0
    except Exception:
        num = 0
    # negative for DESC
    return (prefix, -num)

# ---------- Globals for templates (KEEP original behavior for classifica) ----------
@app.context_processor
def inject_globals():
    data, err, meta = cache.get_data()
    seasons = data.get('seasons', []) if data else []
    # original logic: pick ACTIVE else first
    active = [s for s in seasons if s.get('status','').upper() == 'ACTIVE']
    default_season = (active[0]['id'] if active else (seasons[0]['id'] if seasons else 'OP12'))

    # Provide also default_all_scope to avoid template expectations
    tcg = _tcg_code(default_season) if default_season else 'OP'
    default_all_scope = f"ALL-{tcg}"

    # default stats scope = current season by default
    return dict(
        default_season=default_season,
        default_stats_scope=default_season,
        default_all_scope=default_all_scope
    )

# ============================================================================
# ROUTES - HOMEPAGE
# ============================================================================

@app.route('/')
def index():
    """
    Homepage principale con cards per i 3 TCG.

    Mostra 3 card cliccabili:
    - One Piece: Link alla stagione attiva o fallback alla prima disponibile
    - Pokemon: Link alla stagione attiva o fallback
    - Riftbound: Link alla stagione attiva o fallback

    Ogni card punta a /classifica/<season_id> della rispettiva stagione attiva.
    Le stagioni con status=ARCHIVED vengono nascoste.

    Returns:
        Template: landing.html con liste stagioni filtrate per TCG
    """
    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error=err or 'Cache non disponibile'), 500

    seasons = data.get('seasons', [])
    standings_by_season = data.get('standings_by_season', {})

    # Filter OP, PKM, RFB seasons (exclude ARCHIVED)
    op_seasons = [s for s in seasons if s.get('id','').startswith('OP') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']
    pkm_seasons = [s for s in seasons if s.get('id','').startswith('PKM') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']
    rfb_seasons = [s for s in seasons if s.get('id','').startswith('RFB') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']

    # Sort by season number DESC (OP12 > OP11)
    def season_num(s):
        sid = s.get('id', '')
        num = ''.join(ch for ch in sid if ch.isdigit())
        return int(num) if num else 0

    op_seasons_sorted = sorted(op_seasons, key=season_num, reverse=True)
    pkm_seasons_sorted = sorted(pkm_seasons, key=season_num, reverse=True)
    rfb_seasons_sorted = sorted(rfb_seasons, key=season_num, reverse=True)

    # Podio: ultima CLOSED
    closed_seasons = [s for s in op_seasons_sorted if s.get('status','').upper() == 'CLOSED']
    podio_season_id = closed_seasons[0]['id'] if closed_seasons else (op_seasons_sorted[0]['id'] if op_seasons_sorted else 'OP12')

    # Stats/Highlights: ultima ACTIVE, oppure ultima CLOSED
    active_seasons = [s for s in op_seasons_sorted if s.get('status','').upper() == 'ACTIVE']
    stats_season_id = active_seasons[0]['id'] if active_seasons else podio_season_id

    # Active seasons for each TCG (for homepage buttons)
    pkm_active_season_id = None
    if pkm_seasons_sorted:
        pkm_active = [s for s in pkm_seasons_sorted if s.get('status','').upper() == 'ACTIVE']
        pkm_active_season_id = pkm_active[0]['id'] if pkm_active else pkm_seasons_sorted[0]['id']

    rfb_active_season_id = None
    if rfb_seasons_sorted:
        rfb_active = [s for s in rfb_seasons_sorted if s.get('status','').upper() == 'ACTIVE']
        rfb_active_season_id = rfb_active[0]['id'] if rfb_active else rfb_seasons_sorted[0]['id']

    # === GLOBAL STATS per ticker (tutte le stagioni non-ARCHIVED) ===
    all_active_seasons = op_seasons + pkm_seasons + rfb_seasons  # Già filtrate senza ARCHIVED
    global_players = set()
    global_tournaments = 0

    for season in all_active_seasons:
        sid = season.get('id', '')
        season_standings = standings_by_season.get(sid, [])
        # Conta giocatori unici
        for player in season_standings:
            if player.get('membership'):
                global_players.add(player.get('membership'))

    # Conta tornei da tournaments_by_season (è un dizionario, non una lista!)
    tournaments_by_season = data.get('tournaments_by_season', {})
    for season in all_active_seasons:
        sid = season.get('id', '')
        season_tournaments = tournaments_by_season.get(sid, [])
        global_tournaments += len(season_tournaments)

    # Top 3 standings (from podio season)
    standings = standings_by_season.get(podio_season_id, [])[:3]

    # Stats highlights (from stats season)
    from stats_cache import get_cached
    stats_obj = get_cached(stats_season_id, 900)
    if not stats_obj:
        try:
            stats_map = build_stats([stats_season_id])
            stats_obj = stats_map.get(stats_season_id, {})
        except:
            stats_obj = {}

    # Next tournament (from stats season)
    next_tournament = None
    stats_season_meta = next((s for s in seasons if s.get('id') == stats_season_id), None)
    if stats_season_meta:
        next_tournament = stats_season_meta.get('next_tournament')

    # Season names for display
    podio_season_name = next((s.get('name','') for s in seasons if s.get('id') == podio_season_id), podio_season_id)
    stats_season_name = next((s.get('name','') for s in seasons if s.get('id') == stats_season_id), stats_season_id)
    
    return render_template(
        'landing.html',
        standings=standings,
        stats=stats_obj,
        next_tournament=next_tournament,
        podio_season_id=podio_season_id,
        stats_season_id=stats_season_id,
        podio_season_name=podio_season_name,
        stats_season_name=stats_season_name,
        pkm_active_season_id=pkm_active_season_id,
        rfb_active_season_id=rfb_active_season_id,
        global_players_count=len(global_players),
        global_tournaments_count=global_tournaments
    )


# ============================================================================
# ROUTES - PAGINA CLASSIFICHE (Lista Stagioni)
# ============================================================================

@app.route('/classifiche')
def classifiche_page():
    """
    Pagina dedicata alle classifiche - lista tutte le stagioni disponibili per TCG.

    Mostra 3 sezioni (One Piece, Pokemon, Riftbound), ognuna con cards
    per tutte le stagioni non-ARCHIVED ordinate per numero DESC.

    Ogni card linka a /classifica/<season_id> per vedere la classifica
    dettagliata della stagione.

    Le stagioni ARCHIVED sono nascoste (doppio filtro: route + template).

    Returns:
        Template: classifiche_page.html con liste stagioni per TCG
    """
    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error=err or 'Cache non disponibile'), 500

    seasons = data.get('seasons', [])

    # Filtra stagioni per TCG (escludi ARCHIVED)
    op_seasons = [s for s in seasons if s.get('id','').startswith('OP') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']
    pkm_seasons = [s for s in seasons if s.get('id','').startswith('PKM') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']
    rfb_seasons = [s for s in seasons if s.get('id','').startswith('RFB') and _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']

    # Sort by season number DESC
    def season_num(s):
        sid = s.get('id', '')
        num = ''.join(ch for ch in sid if ch.isdigit())
        return int(num) if num else 0

    op_seasons_sorted = sorted(op_seasons, key=season_num, reverse=True)
    pkm_seasons_sorted = sorted(pkm_seasons, key=season_num, reverse=True)
    rfb_seasons_sorted = sorted(rfb_seasons, key=season_num, reverse=True)

    return render_template(
        'classifiche_page.html',
        op_seasons=op_seasons_sorted,
        pkm_seasons=pkm_seasons_sorted,
        rfb_seasons=rfb_seasons_sorted
    )


# ============================================================================
# ROUTES - CLASSIFICA STAGIONE (Standings)
# ============================================================================

# Support BOTH /classifica and /classifica/<season_id>
@app.route('/classifica')
@app.route('/classifica/<season_id>')
def classifica(season_id=None):
    """
    Classifica dettagliata di una singola stagione.

    Mostra:
    - Info card stagione (nome, status, date tornei, vincitore ultimo torneo)
    - Tabella standings con rank, giocatore, tornei giocati, punti totali
    - Dettaglio tornei della stagione (espandibile)

    Supporta sia /classifica/<season_id> che /classifica?season=<season_id>
    per retrocompatibilità con vecchi template.

    Le stagioni ARCHIVED sono accessibili direttamente tramite URL ma non
    compaiono in dropdown/liste.

    Args:
        season_id (str, optional): ID stagione (es. OP12).
                                   Se None, usa query param ?season=

    Returns:
        Template: classifica.html con standings e info stagione
    """
    # Accept legacy query param ?season=OP12 (from old templates)
    q_season = request.args.get('season')
    if season_id is None and q_season:
        season_id = q_season

    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error=err or 'Cache non disponibile'), 500

    seasons = data.get('seasons', [])
    standings_by_season = data.get('standings_by_season', {})
    tournaments_by_season = data.get('tournaments_by_season', {})

    # Compute last_tournament (date + winner) for info card
    last_tournament_ctx = None
    _tlist = tournaments_by_season.get(season_id, []) if season_id else []
    def _parse_dt(s):
        from datetime import datetime
        for fmt in ('%Y-%m-%d','%d/%m/%Y','%Y/%m/%d'):
            try:
                return datetime.strptime(str(s), fmt)
            except Exception:
                pass
        return None
    _best = None; _best_dt = None
    for _t in _tlist:
        _dt = _parse_dt(_t.get('date'))
        if _dt is None:
            continue
        if _best_dt is None or _dt > _best_dt:
            _best, _best_dt = _t, _dt
    if _best is None and _tlist:
        _best = _tlist[-1]
    if _best:
        last_tournament_ctx = {
            'date': _best.get('date') or '',
            'winner': _best.get('winner') or ''
        }


    # If still None, select default and redirect to canonical URL
    if season_id is None:
        active = [s for s in seasons if s.get('status','').upper() == 'ACTIVE']
        season_id = (active[0]['id'] if active else (seasons[0]['id'] if seasons else None))
        if season_id is None:
            return render_template('error.html', error='Nessuna stagione disponibile'), 500
        return redirect(url_for('classifica', season_id=season_id))

    standings = standings_by_season.get(season_id, []) or []

    # Self-healing: if standings empty, try one fetch_data() and retry once
    if len(standings) == 0:
        success, error = cache.fetch_data()
        if success:
            data, err, meta = cache.get_data()
            standings_by_season = data.get('standings_by_season', {})
            tournaments_by_season = data.get('tournaments_by_season', {})
            standings = standings_by_season.get(season_id, []) or []

    season_meta = next((s for s in seasons if s.get('id') == season_id), None)
    if not season_meta:
        return render_template('error.html', error='Stagione non trovata'), 404

    # Provide alias 'all_seasons' for template backward-compatibility
    all_seasons = seasons

    return render_template(
        'classifica.html',
        season=season_meta,
        standings=standings,
        tournaments=tournaments_by_season.get(season_id, []),
        seasons=seasons,
        all_seasons=all_seasons,
        is_stale=(meta[0] if meta else False),
        cache_age=(meta[1] if meta else None),
        last_tournament=last_tournament_ctx  # optional for template
    )


# ============================================================================
# ROUTES - SAGA NARRATIVA
# ============================================================================

@app.route('/saga/<season_id>')
def saga(season_id):
    """
    Timeline narrativa epica della stagione - stile pergamena fantasy.
    Genera automaticamente una storia basata sui risultati dei tornei.
    """
    import random

    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error=err or 'Cache non disponibile'), 500

    seasons = data.get('seasons', [])
    season_meta = next((s for s in seasons if s.get('id') == season_id), None)
    if not season_meta:
        return render_template('error.html', error=f'Stagione {season_id} non trovata'), 404

    tournaments = data.get('tournaments_by_season', {}).get(season_id, [])
    standings = data.get('standings_by_season', {}).get(season_id, [])
    results = data.get('results', [])

    # Sort tournaments by date
    def parse_date(d):
        from datetime import datetime
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try: return datetime.strptime(str(d), fmt)
            except: pass
        return None

    tournaments = sorted(tournaments, key=lambda t: parse_date(t.get('date')) or t.get('date', ''))

    # Generate narrative chapters
    chapters = []
    saga_titles = [
        "La Saga", "Le Cronache", "L'Epopea", "La Leggenda", "Il Racconto"
    ]
    saga_subtitles = [
        "Gloria e Sconfitte nell'Arena", "Dove i Campioni Forgiano il Destino",
        "L'Ascesa dei Valorosi", "Sangue, Sudore e Carte", "La Battaglia per la Corona"
    ]

    # Track state for narrative
    prev_winner = None
    streak_count = 0
    streak_holder = None

    for i, t in enumerate(tournaments):
        winner = t.get('winner', 'Sconosciuto')
        participants = safe_int(t.get('participants', 0))
        date = t.get('date', '')
        t_id = t.get('tournament_id', '')

        # Get tournament results for more context
        t_results = [r for r in results if r.get('tournament_id') == t_id]
        t_results_sorted = sorted(t_results, key=lambda x: safe_int(x.get('rank', 99)))
        second = t_results_sorted[1].get('name', '') if len(t_results_sorted) > 1 else None

        # Track streaks
        if winner == prev_winner:
            streak_count += 1
        else:
            streak_count = 1
            streak_holder = winner

        chapter = {'num': _roman(i+1), 'epic': False, 'badge': None}

        # Generate varied narrative based on context
        if i == 0:
            # First tournament
            openers = [
                f"La stagione ebbe inizio con un torneo memorabile. <span class='highlight-name'>{winner}</span> si impose fin da subito, "
                f"dominando {participants} avversari e dichiarando le proprie ambizioni.",
                f"L'alba della stagione vide emergere <span class='highlight-name'>{winner}</span>. Con determinazione implacabile, "
                f"si fece strada tra {participants} sfidanti, conquistando il primo trofeo.",
                f"Tutto cominciò quando <span class='highlight-name'>{winner}</span> alzò il primo trofeo della stagione. "
                f"Nessuno dei {participants} partecipanti poté fermarlo."
            ]
            chapter['title'] = random.choice(["L'Alba", "Il Principio", "La Genesi", "L'Inizio"])
            chapter['text'] = random.choice(openers)

        elif winner == prev_winner:
            # Streak continues
            chapter['epic'] = True
            streak_texts = [
                f"<span class='highlight-name'>{winner}</span> non si accontentò. Per la {_ordinal(streak_count)} volta consecutiva, "
                f"il suo dominio fu assoluto. Gli avversari iniziarono a tremare.",
                f"La leggenda di <span class='highlight-name'>{winner}</span> crebbe ancora. <span class='highlight-event'>Striscia di {streak_count} vittorie!</span> "
                f"Chi avrebbe potuto fermarlo?",
                f"Inarrestabile. <span class='highlight-name'>{winner}</span> conquistò un'altra vittoria, la {_ordinal(streak_count)} di fila. "
                f"Il suo regno sembrava eterno."
            ]
            chapter['title'] = random.choice(["Il Dominio", "L'Inarrestabile", "La Striscia", "Il Regno"])
            chapter['text'] = random.choice(streak_texts)
            chapter['badge'] = f"🔥 {streak_count} vittorie consecutive"

        elif streak_count > 1 and winner != streak_holder:
            # Streak broken - UPSET!
            chapter['epic'] = True
            upset_texts = [
                f"Ma ecco il colpo di scena! <span class='highlight-name'>{winner}</span> spezzò la striscia di {prev_winner}. "
                f"<span class='highlight-event'>L'imbattibile era caduto.</span> L'arena esplose.",
                f"La caduta dei giganti. <span class='highlight-name'>{winner}</span> compì l'impresa, detronizzando {prev_winner} "
                f"dopo {streak_count-1} vittorie consecutive. Un nuovo eroe era nato.",
                f"Nessuno se lo aspettava. <span class='highlight-name'>{winner}</span> emerse dall'ombra e abbatté "
                f"il regno di {prev_winner}. <span class='highlight-event'>UPSET!</span>"
            ]
            chapter['title'] = random.choice(["La Caduta", "L'Upset", "Il Ribaltone", "Il Nuovo Ordine"])
            chapter['text'] = random.choice(upset_texts)
            chapter['badge'] = f"⚡ Striscia di {prev_winner} interrotta!"

        else:
            # Normal tournament, new winner
            normal_texts = [
                f"Fu il turno di <span class='highlight-name'>{winner}</span> di scrivere il proprio nome nella storia. "
                f"Con {participants} anime in lizza, prevalse con maestria.",
                f"<span class='highlight-name'>{winner}</span> si fece avanti. In un torneo combattuto, "
                f"emerse vittorioso tra {participants} partecipanti.",
                f"Le carte favorirono <span class='highlight-name'>{winner}</span> questa volta. "
                f"Una vittoria meritata che riaccese la corsa al titolo."
            ]
            if second:
                normal_texts.append(
                    f"<span class='highlight-name'>{winner}</span> e {second} si diedero battaglia fino all'ultimo. "
                    f"Solo uno poteva prevalere, e fu {winner.split()[0]} a trionfare."
                )
            chapter['title'] = random.choice(["Un Nuovo Eroe", "La Svolta", "Cambio di Guardia", "Il Torneo"])
            chapter['text'] = random.choice(normal_texts)

        chapter['badge'] = chapter.get('badge') or f"🏆 Torneo #{i+1} • {participants} partecipanti"
        chapters.append(chapter)
        prev_winner = winner

    # Get current leader
    leader = standings[0].get('name') if standings else None
    is_closed = season_meta.get('status', '').upper() == 'CLOSED'

    return render_template(
        'saga.html',
        season=season_meta,
        chapters=chapters,
        saga_title=f"{random.choice(saga_titles)} di {season_meta.get('name', season_id)}",
        saga_subtitle=random.choice(saga_subtitles),
        leader=leader,
        is_closed=is_closed
    )


def _roman(n):
    """Convert int to roman numeral."""
    vals = [(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for v, r in vals:
        while n >= v:
            result += r
            n -= v
    return result


def _ordinal(n):
    """Italian ordinal."""
    ords = {1:'prima',2:'seconda',3:'terza',4:'quarta',5:'quinta',6:'sesta',7:'settima',8:'ottava',9:'nona',10:'decima'}
    return ords.get(n, f'{n}ª')


# ============================================================================
# ROUTES - STATISTICHE AVANZATE (Stats)
# ============================================================================

@app.route('/stats/<scope>')
def stats(scope):
    """
    Statistiche avanzate per stagione o all-time TCG.

    Mostra 4 categorie di statistiche:
    - **Spotlights**: Record individuali (max wins, max points, streak, etc.)
    - **Pulse**: Medie, mediane, varianza (analisi statistica)
    - **Tales**: Pattern interessanti (comeback, consistency, volatility)
    - **Hall of Fame**: Top 10 lifetime per vari indicatori

    Scope può essere:
    - Singola stagione (es. OP12) → stats solo per quella stagione
    - All-time TCG (es. ALL-OP) → stats aggregate per tutti i tornei One Piece

    Usa cache file-based (stats_cache.py) per performance.
    Cache TTL: 900s (15 min).

    Args:
        scope (str): Season ID (es. OP12) o ALL-<TCG> (es. ALL-OP)

    Returns:
        Template: stats.html con 4 categorie di statistiche
    """
    from stats_cache import get_cached, set_cached

    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error=err or 'Cache non disponibile'), 500

    seasons = data.get('seasons', [])

    # only "real seasons" for the dropdown (exclude ARCHIVED)
    real_seasons = [s for s in seasons if _is_valid_season_id(s.get('id')) and s.get('status','').upper() != 'ARCHIVED']

    # default season for the "Classifica" button - dynamic based on current scope TCG
    current_tcg = _tcg_code(scope) if not scope.startswith('ALL-') else scope.split('-')[1]
    active_same_tcg = [s for s in real_seasons if s.get('status','').upper() == 'ACTIVE' and s.get('id','').startswith(current_tcg)]
    default_season = (active_same_tcg[0]['id'] if active_same_tcg else
                     (real_seasons[0]['id'] if real_seasons else 'OP12'))

    # Build ordered dropdown:
    season_ids = [s['id'] for s in real_seasons]
    all_active = [s for s in real_seasons if s.get('status','').upper() == 'ACTIVE']
    active_id = all_active[0]['id'] if all_active else None
    others = [sid for sid in season_ids if sid != active_id]
    others_sorted = sorted(others, key=_season_key_desc)  # already DESC by numeric

    tcgs = sorted({_tcg_code(sid) for sid in season_ids})
    all_time = [f'ALL-{t}' for t in tcgs]

    if active_id:
        available_scopes = [active_id] + others_sorted + all_time
    else:
        available_scopes = others_sorted + all_time

    # File-based cache (15 min TTL)
    MAX_AGE = 900
    stats_obj = get_cached(scope, MAX_AGE)
    if stats_obj is None:
        stats_map = build_stats([scope])
        stats_obj = stats_map.get(scope)
        if not stats_obj:
            return render_template('error.html', error='Scope non valido o nessun dato'), 404
        set_cached(scope, stats_obj)

    return render_template(
        'stats.html',
        scope=scope,
        stats=stats_obj,
        default_season=default_season,
        available_scopes=available_scopes
    )

# ---------- APIs ----------
@app.route('/api/refresh')
def api_refresh():
    """Refresh della cache classifica (quella originale)."""
    success, error = cache.fetch_data()
    if success:
        return jsonify({'status': 'ok', 'message': 'Cache refreshed'})
    else:
        return jsonify({'status': 'error', 'message': error}), 500

@app.route('/api/stats/refresh/<scope>')
def api_stats_refresh(scope):
    """Invalidates and rebuilds stats cache for a scope."""
    from stats_cache import clear, set_cached
    try:
        cleared = clear(scope)
        stats_map = build_stats([scope])
        stats_obj = stats_map.get(scope)
        if not stats_obj:
            return jsonify({'status':'error','message':'Scope non valido o nessun dato'}), 404
        set_cached(scope, stats_obj)
        return jsonify({'status':'ok','cleared': cleared, 'scope': scope})
    except Exception as e:
        return jsonify({'status':'error','message': str(e)}), 500


# ============================================================================
# ROUTES - GIOCATORI (Profili e Lista)
# ============================================================================

@app.route('/players')
def players_list():
    """
    Lista tutti i giocatori registrati (senza duplicati).

    Legge da Player_Stats per mostrare una sola card per membership,
    con stats aggregate di tutte le stagioni.

    Mostra card per ogni giocatore ordinata per punti medi con:
    - Membership number
    - Nome (formattato per TCG con filtro format_player_name)
    - TCG principale
    - Numero tornei giocati
    - Numero vittorie tornei
    - Punti medi per torneo

    Ogni card linka al profilo dettagliato /player/<membership>.

    Returns:
        Template: players.html con lista giocatori ordinata per punti medi DESC
    """
    from cache import cache
    try:
        sheet = cache.connect_sheet()
        ws_stats = sheet.worksheet("Player_Stats")

        # Valida struttura Player_Stats
        expected_headers = [
            "Membership", "Name", "TCG", "Total Tournaments", "Total Wins",
            "Current Streak", "Best Streak", "Top8 Count", "Last Rank",
            "Last Date", "Seasons Count", "Updated At", "Total Points"
        ]
        validation = validate_sheet_headers(ws_stats, COL_PLAYER_STATS, expected_headers, header_row_index=2)
        if not validation['valid']:
            error_msg = "⚠️ ATTENZIONE: La struttura del foglio Player_Stats non è corretta!\n"
            error_msg += "\n".join(validation['errors'])
            error_msg += "\n\nContatta l'amministratore per correggere il problema."
            return render_template('error.html', error=error_msg), 500

        all_stats = ws_stats.get_all_values()[3:]  # Skip header

        players = []
        for row in all_stats:
            if not row or len(row) <= COL_PLAYER_STATS['membership']:
                continue

            membership = row[COL_PLAYER_STATS['membership']].strip() if len(row) > COL_PLAYER_STATS['membership'] else ''
            if membership:
                # Estrai valori usando indici del mapping
                total_tournaments = safe_int(
                    row[COL_PLAYER_STATS['total_tournaments']] if len(row) > COL_PLAYER_STATS['total_tournaments'] else None,
                    0
                )
                total_points = safe_float(
                    row[COL_PLAYER_STATS['total_points']] if len(row) > COL_PLAYER_STATS['total_points'] else None,
                    0.0
                )
                avg_points = round(total_points / total_tournaments, 1) if total_tournaments > 0 else 0.0

                players.append({
                    'membership': membership,
                    'name': row[COL_PLAYER_STATS['name']] if len(row) > COL_PLAYER_STATS['name'] else '',
                    'tcg': row[COL_PLAYER_STATS['tcg']] if len(row) > COL_PLAYER_STATS['tcg'] else 'OP',
                    'tournaments': total_tournaments,
                    'wins': safe_int(
                        row[COL_PLAYER_STATS['total_wins']] if len(row) > COL_PLAYER_STATS['total_wins'] else None,
                        0
                    ),
                    'points': avg_points
                })

        # Ordina per punti medi DESC
        players.sort(key=lambda x: x['points'], reverse=True)

        return render_template('players.html', players=players)
    except Exception as e:
        return render_template('error.html', error=f'Errore: {str(e)}'), 500

@app.route('/player/<membership>')
def player(membership):
    """
    Profilo dettagliato singolo giocatore.

    Mostra:
    - Card anagrafica (nome, TCG, membership, tornei/vittorie/punti lifetime)
    - Achievement sbloccati con emoji, rarity badges, punti totali
    - Storico risultati tornei (tabella con tutte le partecipazioni)
    - Grafici performance (se disponibili)

    Gli achievement vengono caricati da:
    - Achievement_Definitions (per info emoji, rarity, descrizione)
    - Player_Achievements (per achievement sbloccati da questo giocatore)

    Args:
        membership (str): Membership number giocatore (es. 0000012345)

    Returns:
        Template: player.html con profilo completo giocatore
        404: Se giocatore non trovato (no results in Results sheet)
    """
    from cache import cache
    data, err, meta = cache.get_data()
    if not data:
        return render_template('error.html', error='Cache non disponibile'), 500

    # Carica sheet per player data
    try:
        sheet = cache.connect_sheet()
        ws_results = sheet.worksheet("Results")
        all_results = ws_results.get_all_values()[3:]

        # Filtra per membership
        player_results = [r for r in all_results if r and len(r) >= 10 and r[2] == membership]

        if not player_results:
            return render_template('error.html', error='Giocatore non trovato'), 404

        # Leggi TCG dal foglio Players
        ws_players = sheet.worksheet("Players")
        players_data = ws_players.get_all_values()[3:]
        player_row = next((p for p in players_data if safe_get(p, COL_PLAYERS, 'membership') == membership), None)
        player_tcg = safe_get(player_row, COL_PLAYERS, 'tcg', 'OP') if player_row else 'OP'

        # Dati base
        player_name = player_results[0][9] if player_results[0][9] else membership
        
        # Calcoli
        tournaments_played = len(player_results)
        tournament_wins = sum(1 for r in player_results if r[3] and int(r[3]) == 1)
        top8_count = sum(1 for r in player_results if r[3] and int(r[3]) <= 8)
        
        points = [float(r[8]) for r in player_results if r[8]]
        avg_points = sum(points) / len(points) if points else 0
        best_rank = min([int(r[3]) for r in player_results if r[3]], default=999)
        
        # Win Rate (assumendo 4 round medi)
        total_wins = sum([float(r[4])/3 for r in player_results if r[4]])
        win_rate = (total_wins / (tournaments_played * 4) * 100) if tournaments_played > 0 else 0
        
        # Top8 Rate
        top8_rate = (top8_count / tournaments_played * 100) if tournaments_played > 0 else 0
        
        # Trend (ultimi 2 vs precedenti)
        if len(points) >= 3:
            recent = sum(points[-2:]) / 2
            older = sum(points[:-2]) / len(points[:-2])
            trend = ((recent - older) / older * 100) if older > 0 else 0
        else:
            trend = 0
        
        # First seen
        dates = [r[1].split('_')[1] if '_' in r[1] else '' for r in player_results if r[1]]
        first_seen = min(dates) if dates else 'N/A'
        
        # Storico tornei (ultimi 10)
        # Carica seasons per ottenere status (ARCHIVED check)
        seasons = data.get('seasons', [])
        season_status_map = {s.get('id'): s.get('status', '') for s in seasons}

        history = []
        for r in player_results[-10:]:
            season_id = r[1].split('_')[0] if '_' in r[1] else ''
            season_status = season_status_map.get(season_id, '')

            # Costruisci record W-T-L o W-L in base al TCG
            # Colonne Results: 10=Match_W, 11=Match_T, 12=Match_L
            if len(r) >= 13 and r[10] and r[11] and r[12]:
                match_w = int(r[10])
                match_t = int(r[11])
                match_l = int(r[12])

                # Pokemon e Riftbound hanno ties, One Piece no
                if match_t > 0:
                    record = f"{match_w}-{match_t}-{match_l}"  # W-T-L
                else:
                    record = f"{match_w}-{match_l}"  # W-L
            else:
                # Fallback per dati vecchi senza Match_W/T/L
                # Approssima da Win_Points (W*3 + T*1)
                wins = int(float(r[4])/3) if r[4] else 0
                record = f"{wins}-?"

            history.append({
                'date': r[1].split('_')[1] if '_' in r[1] else '',
                'season': season_id,
                'season_status': season_status,
                'rank': int(r[3]) if r[3] else 999,
                'points': float(r[8]) if r[8] else 0,
                'record': record
            })
        history.reverse()
        
        # Chart data (ultimi 10)
        chart_labels = [h['date'] for h in history[::-1]]
        chart_data = [h['points'] for h in history[::-1]]

        # ====================================================================
        # NUOVI CALCOLI PER GRAFICI STATISTICHE AVANZATE
        # ====================================================================

        # 1. Match Record (W-T-L totali lifetime)
        total_match_w = 0
        total_match_t = 0
        total_match_l = 0
        has_match_data = False

        for r in player_results:
            if len(r) >= 13 and r[10] and r[11] and r[12]:
                total_match_w += int(r[10])
                total_match_t += int(r[11])
                total_match_l += int(r[12])
                has_match_data = True

        match_record = {
            'wins': total_match_w,
            'ties': total_match_t,
            'losses': total_match_l,
            'has_data': has_match_data
        }

        # 2. Ranking Distribution (quante volte in ogni fascia)
        rank_1st = sum(1 for r in player_results if r[3] and int(r[3]) == 1)
        rank_2nd = sum(1 for r in player_results if r[3] and int(r[3]) == 2)
        rank_3rd = sum(1 for r in player_results if r[3] and int(r[3]) == 3)
        rank_top8 = sum(1 for r in player_results if r[3] and 4 <= int(r[3]) <= 8)
        rank_other = sum(1 for r in player_results if r[3] and int(r[3]) > 8)

        ranking_dist = {
            'first': rank_1st,
            'second': rank_2nd,
            'third': rank_3rd,
            'top8': rank_top8,
            'other': rank_other
        }

        # 3. Radar Data (5 metriche normalizzate 0-100)
        # Victory Rate: % tornei vinti
        victory_rate = (tournament_wins / tournaments_played * 100) if tournaments_played > 0 else 0

        # Avg Performance: punti medi normalizzati (max 25 = 100%)
        avg_performance = min(100, (avg_points / 25 * 100)) if avg_points > 0 else 0

        # Consistency: stabilità basata su deviazione standard (max dev 10 = 0%)
        if len(points) > 1:
            import statistics
            std_dev = statistics.stdev(points)
            consistency = max(0, (1 - std_dev / 10) * 100)
        else:
            consistency = 100  # Se ha giocato 1 solo torneo, è "perfettamente consistente"

        radar_data = {
            'win_rate': round(win_rate, 1),
            'top8_rate': round(top8_rate, 1),
            'victory_rate': round(victory_rate, 1),
            'avg_performance': round(avg_performance, 1),
            'consistency': round(consistency, 1)
        }

        # Achievement data
        achievements_unlocked = []
        achievement_points = 0
        try:
            ws_achievements = sheet.worksheet("Achievement_Definitions")
            achievement_defs = {}
            for row in ws_achievements.get_all_values()[4:]:
                ach_id = safe_get(row, COL_ACHIEVEMENT_DEF, 'achievement_id')
                if ach_id:
                    achievement_defs[ach_id] = {
                        'name': safe_get(row, COL_ACHIEVEMENT_DEF, 'name'),
                        'description': safe_get(row, COL_ACHIEVEMENT_DEF, 'description'),
                        'category': safe_get(row, COL_ACHIEVEMENT_DEF, 'category'),
                        'rarity': safe_get(row, COL_ACHIEVEMENT_DEF, 'rarity'),
                        'emoji': safe_get(row, COL_ACHIEVEMENT_DEF, 'emoji'),
                        'points': safe_int(row, COL_ACHIEVEMENT_DEF, 'points', 0)
                    }

            ws_player_ach = sheet.worksheet("Player_Achievements")
            for row in ws_player_ach.get_all_values()[4:]:
                if safe_get(row, COL_PLAYER_ACH, 'membership') == membership:
                    ach_id = safe_get(row, COL_PLAYER_ACH, 'achievement_id')
                    if ach_id in achievement_defs:
                        ach_info = achievement_defs[ach_id]
                        achievements_unlocked.append({
                            'id': ach_id,
                            'name': ach_info['name'],
                            'description': ach_info['description'],
                            'category': ach_info['category'],
                            'rarity': ach_info['rarity'],
                            'emoji': ach_info['emoji'],
                            'points': ach_info['points'],
                            'unlocked_date': safe_get(row, COL_PLAYER_ACH, 'unlocked_date', '')
                        })
                        achievement_points += ach_info['points']
        except Exception as e:
            print(f"Achievement load error: {e}")
            # Se achievement non esistono ancora, continua senza

        player_data = {
            'membership': membership,
            'name': player_name,
            'tcg': player_tcg,
            'first_seen': first_seen,
            'tournaments_played': tournaments_played,
            'tournament_wins': tournament_wins,
            'top8_count': top8_count,
            'avg_points': round(avg_points, 1),
            'best_rank': best_rank,
            'win_rate': round(win_rate, 1),
            'top8_rate': round(top8_rate, 1),
            'trend': round(trend, 1),
            'history': history,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'achievements': achievements_unlocked,
            'achievement_points': achievement_points,
            # Nuovi dati per grafici statistiche avanzate
            'match_record': match_record,
            'ranking_dist': ranking_dist,
            'radar_data': radar_data
        }
        
        return render_template('player.html', player=player_data)
        
    except Exception as e:
        return render_template('error.html', error=f'Errore caricamento dati: {str(e)}'), 500


# =============================================================================
# NOTE: Achievement and Admin routes are now in Blueprint modules:
# - routes/achievements.py - /achievements, /achievement/<id>
# - routes/admin.py - /admin/*, /admin/login, /admin/logout
# =============================================================================


# ---------- Errors ----------
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Pagina non trovata'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Errore del server'), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)