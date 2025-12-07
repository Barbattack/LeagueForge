# -*- coding: utf-8 -*-
"""
LeagueForge - Admin Routes
=========================

Blueprint per tutte le route admin:
- Login/Logout
- Dashboard
- Import tornei (One Piece, Pokemon, Riftbound)

Tutte le route sono protette da @admin_required (eccetto login).
"""

import os
import subprocess
import tempfile

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename

from auth import admin_required, login_user, logout_user, is_admin_logged_in, get_session_info
from cache import cache
from import_controller import import_tournament as controller_import_tournament
from season_manager import create_season, close_season, get_seasons, suggest_next_season_id


# =============================================================================
# BLUEPRINT DEFINITION
# =============================================================================

admin_bp = Blueprint('admin', __name__, template_folder='../templates')


# =============================================================================
# ROUTES - AUTH
# =============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Pagina login admin.

    GET: Mostra form login
    POST: Verifica credenziali e crea sessione
    """
    if is_admin_logged_in():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if login_user(username, password):
            flash('Login effettuato con successo!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Credenziali non valide. Riprova.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Logout admin e redirect a login page."""
    logout_user()
    flash('Logout effettuato.', 'info')
    return redirect(url_for('admin.login'))


# =============================================================================
# ROUTES - DASHBOARD
# =============================================================================

@admin_bp.route('/')
@admin_required
def dashboard():
    """
    Dashboard admin principale.

    Mostra:
    - Form upload per 3 TCG (One Piece, Pokemon, Riftbound)
    - Dropdown stagioni disponibili
    - Checkbox test mode
    - Session info (tempo rimanente)
    """
    data, err, meta = cache.get_data()
    if not data:
        seasons_by_tcg = {'OP': [], 'PKM': [], 'RFB': []}
    else:
        seasons = data.get('seasons', [])

        # Filtra solo stagioni ACTIVE e CLOSED (no ARCHIVED)
        active_seasons = [s for s in seasons if s.get('status', '').upper() in ['ACTIVE', 'CLOSED']]

        # Raggruppa per TCG
        seasons_by_tcg = {
            'OP': [s for s in active_seasons if s.get('id', '').startswith('OP')],
            'PKM': [s for s in active_seasons if s.get('id', '').startswith('PKM')],
            'RFB': [s for s in active_seasons if s.get('id', '').startswith('RFB')]
        }

        # Sort per numero stagione DESC
        for tcg in seasons_by_tcg:
            seasons_by_tcg[tcg].sort(
                key=lambda s: int(''.join(c for c in s.get('id', '') if c.isdigit()) or '0'),
                reverse=True
            )

    session_info = get_session_info()

    return render_template('admin/dashboard.html',
                          seasons_by_tcg=seasons_by_tcg,
                          session_info=session_info)


# =============================================================================
# ROUTES - IMPORT
# =============================================================================

@admin_bp.route('/import/onepiece', methods=['POST'])
@admin_required
def import_onepiece():
    """
    Gestisce import One Piece da CSV.

    NOTE: Usa subprocess temporaneamente. Sarà migrato a import_controller
    in FASE 3 con nuova UI multi-file (round_files + classifica).

    Form data:
    - file: CSV file
    - season: Season ID (es. OP12)
    - test_mode: checkbox (optional)
    """
    try:
        if 'file' not in request.files:
            flash('Nessun file caricato', 'danger')
            return redirect(url_for('admin.dashboard'))

        file = request.files['file']
        season_id = request.form.get('season', '').strip()
        test_mode = request.form.get('test_mode') == 'on'

        if not file or file.filename == '':
            flash('Nessun file selezionato', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not season_id:
            flash('Seleziona una stagione', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not file.filename.endswith('.csv'):
            flash('File deve essere CSV', 'danger')
            return redirect(url_for('admin.dashboard'))

        # Salva file temporaneo
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Esegui import script
        cmd = ['python3', 'import_onepiece.py', '--csv', tmp_path, '--season', season_id]
        if test_mode:
            cmd.append('--test')

        result = subprocess.run(cmd, cwd='/home/user/LeagueForge/leagueforge',
                               capture_output=True, text=True, timeout=120)

        os.unlink(tmp_path)

        output = result.stdout + result.stderr

        if result.returncode == 0:
            flash(f'Import One Piece completato{"(TEST MODE)" if test_mode else ""}!', 'success')
        else:
            flash('Errore durante import', 'danger')

        return render_template('admin/import_result.html',
                             tcg='One Piece',
                             season=season_id,
                             test_mode=test_mode,
                             success=(result.returncode == 0),
                             output=output)

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/import/pokemon', methods=['POST'])
@admin_required
def import_pokemon():
    """Gestisce import Pokemon da TDF/XML."""
    try:
        if 'file' not in request.files:
            flash('Nessun file caricato', 'danger')
            return redirect(url_for('admin.dashboard'))

        file = request.files['file']
        season_id = request.form.get('season', '').strip()
        test_mode = request.form.get('test_mode') == 'on'

        if not file or file.filename == '':
            flash('Nessun file selezionato', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not season_id:
            flash('Seleziona una stagione', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not (file.filename.endswith('.tdf') or file.filename.endswith('.xml')):
            flash('File deve essere TDF o XML', 'danger')
            return redirect(url_for('admin.dashboard'))

        # Salva file temporaneo
        suffix = '.tdf' if file.filename.endswith('.tdf') else '.xml'
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Import tramite controller (no subprocess)
        result = controller_import_tournament(
            tcg='pokemon',
            season_id=season_id,
            files={'tdf': tmp_path},
            test_mode=test_mode,
            allow_reimport=False
        )

        # Cleanup file temp
        os.unlink(tmp_path)

        # Gestione risultato
        if result['success']:
            flash(f'Import Pokemon completato{" (TEST MODE)" if test_mode else ""}!', 'success')
        else:
            flash(f'Errore durante import: {result.get("error", "Errore sconosciuto")}', 'danger')

        return render_template('admin/import_result.html',
                             tcg='Pokemon',
                             season=season_id,
                             test_mode=test_mode,
                             success=result['success'],
                             output=result.get('output', result.get('error', '')))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/import/riftbound', methods=['POST'])
@admin_required
def import_riftbound():
    """
    Gestisce import Riftbound da CSV Multi-Round.

    NOTE: Usa subprocess temporaneamente. Sarà migrato a import_controller
    in FASE 3 con nuova UI multi-file (round_files).
    """
    try:
        if 'file' not in request.files:
            flash('Nessun file caricato', 'danger')
            return redirect(url_for('admin.dashboard'))

        file = request.files['file']
        season_id = request.form.get('season', '').strip()
        test_mode = request.form.get('test_mode') == 'on'

        if not file or file.filename == '':
            flash('Nessun file selezionato', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not season_id:
            flash('Seleziona una stagione', 'danger')
            return redirect(url_for('admin.dashboard'))

        if not file.filename.endswith('.csv'):
            flash('File deve essere CSV', 'danger')
            return redirect(url_for('admin.dashboard'))

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        cmd = ['python3', 'import_riftbound.py', '--csv', tmp_path, '--season', season_id]
        if test_mode:
            cmd.append('--test')

        result = subprocess.run(cmd, cwd='/home/user/LeagueForge/leagueforge',
                               capture_output=True, text=True, timeout=120)

        os.unlink(tmp_path)

        output = result.stdout + result.stderr

        if result.returncode == 0:
            flash(f'Import Riftbound completato{"(TEST MODE)" if test_mode else ""}!', 'success')
        else:
            flash('Errore durante import', 'danger')

        return render_template('admin/import_result.html',
                             tcg='Riftbound',
                             season=season_id,
                             test_mode=test_mode,
                             success=(result.returncode == 0),
                             output=output)

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


# =============================================================================
# ROUTES - IMPORT WIZARD (FASE 3)
# =============================================================================

@admin_bp.route('/import/wizard')
@admin_required
def import_wizard():
    """
    STEP 1: Selezione TCG + Season.
    Mostra wizard multi-step per import guidato.
    """
    # Get seasons from cache
    data, err, meta = cache.get_data()

    if not data or not data.get('seasons'):
        flash('Errore caricamento stagioni dal cache', 'danger')
        return redirect(url_for('admin.dashboard'))

    seasons = data.get('seasons', [])

    # Prepara JSON per JavaScript
    import json
    seasons_json = json.dumps([
        {
            'id': s.get('id'),
            'name': s.get('name'),
            'status': s.get('status', 'ACTIVE')
        }
        for s in seasons
    ])

    session_info = get_session_info()

    return render_template('admin/import_wizard.html',
                          seasons_json=seasons_json,
                          session_info=session_info)


@admin_bp.route('/import/wizard/upload', methods=['POST'])
@admin_required
def import_wizard_upload():
    """
    STEP 2: Upload file + validazione.
    Salva file temporanei, valida, genera preview.
    """
    from flask import session as flask_session, jsonify
    import json
    from datetime import datetime

    try:
        tcg = request.form.get('tcg', '').strip()
        season_id = request.form.get('season_id', '').strip()
        test_mode = request.form.get('test_mode') == 'on'

        if not tcg or not season_id:
            return jsonify({'success': False, 'error': 'TCG o Season mancanti'})

        # Salva file temporanei basato su TCG
        temp_files = {}

        if tcg == 'pokemon':
            # Single file TDF
            if 'file_pokemon' not in request.files:
                return jsonify({'success': False, 'error': 'File TDF mancante'})

            file = request.files['file_pokemon']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Nessun file selezionato'})

            suffix = '.tdf' if file.filename.endswith('.tdf') else '.xml'
            with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
                file.save(tmp.name)
                temp_files['tdf'] = tmp.name

        elif tcg == 'onepiece':
            # Multi-round + ClassificaFinale
            round_files = []

            # Cerca tutti i file round (file_op_r1, file_op_r2, ...)
            for key in request.files:
                if key.startswith('file_op_r'):
                    file = request.files[key]
                    if file and file.filename:
                        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
                            file.save(tmp.name)
                            round_files.append(tmp.name)

            # ClassificaFinale
            if 'file_classifica' not in request.files:
                return jsonify({'success': False, 'error': 'File ClassificaFinale mancante'})

            classifica_file = request.files['file_classifica']
            if classifica_file.filename == '':
                return jsonify({'success': False, 'error': 'File ClassificaFinale non selezionato'})

            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
                classifica_file.save(tmp.name)
                temp_files['classifica'] = tmp.name

            temp_files['rounds'] = round_files

        elif tcg == 'riftbound':
            # Multi-round
            round_files = []

            # Cerca tutti i file round (file_rfb_r1, file_rfb_r2, ...)
            for key in request.files:
                if key.startswith('file_rfb_r'):
                    file = request.files[key]
                    if file and file.filename:
                        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
                            file.save(tmp.name)
                            round_files.append(tmp.name)

            temp_files['rounds'] = round_files

        # Salva in session Flask
        flask_session['wizard_tcg'] = tcg
        flask_session['wizard_season_id'] = season_id
        flask_session['wizard_test_mode'] = test_mode
        flask_session['wizard_temp_files'] = json.dumps(temp_files)
        flask_session['wizard_upload_time'] = datetime.now().isoformat()

        return jsonify({'success': True, 'message': 'File caricati con successo'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/import/wizard/preview')
@admin_required
def import_wizard_preview():
    """
    STEP 3: Preview dati.
    Parse file, valida, mostra preview per conferma utente.
    """
    from flask import session as flask_session
    import json
    from import_controller import parse, preview as controller_preview, check_duplicate_participants
    from import_base import connect_sheet

    try:
        # Recupera dati da session
        tcg = flask_session.get('wizard_tcg')
        season_id = flask_session.get('wizard_season_id')
        test_mode = flask_session.get('wizard_test_mode', False)
        temp_files_json = flask_session.get('wizard_temp_files')

        if not all([tcg, season_id, temp_files_json]):
            flash('Session scaduta. Riprova import.', 'warning')
            return redirect(url_for('admin.import_wizard'))

        temp_files = json.loads(temp_files_json)

        # Parse file
        parsed_result = parse(tcg, season_id, temp_files)

        if not parsed_result['success']:
            flash(f'Errore parsing: {parsed_result.get("error")}', 'danger')
            return redirect(url_for('admin.import_wizard'))

        # Genera preview
        preview_data = controller_preview(parsed_result)

        # Salva parsed_data in session per step conferma
        flask_session['wizard_parsed_data'] = json.dumps(parsed_result)

        # Check duplicati
        sheet = connect_sheet()
        tournament_id = preview_data['stats'].get('tournament_id', '')
        participants = preview_data.get('participants', [])

        duplicate_check = check_duplicate_participants(sheet, tournament_id, participants)

        duplicate_warning = None
        if duplicate_check['is_duplicate']:
            duplicate_warning = duplicate_check['message']

        return render_template('admin/import_preview.html',
                              tcg=tcg,
                              season_id=season_id,
                              test_mode=test_mode,
                              stats=preview_data['stats'],
                              participants=preview_data['participants'],
                              duplicate_warning=duplicate_warning)

    except Exception as e:
        flash(f'Errore generazione preview: {str(e)}', 'danger')
        return redirect(url_for('admin.import_wizard'))


@admin_bp.route('/import/wizard/confirm', methods=['POST'])
@admin_required
def import_wizard_confirm():
    """
    STEP 4: Conferma e scrittura.
    Esegue import effettivo su Google Sheets.
    """
    from flask import session as flask_session
    import json
    from import_controller import write
    from import_base import connect_sheet

    try:
        # Recupera dati da session
        tcg = flask_session.get('wizard_tcg')
        season_id = flask_session.get('wizard_season_id')
        test_mode = flask_session.get('wizard_test_mode', False)
        parsed_data_json = flask_session.get('wizard_parsed_data')
        temp_files_json = flask_session.get('wizard_temp_files')

        overwrite = request.form.get('overwrite') == 'true'

        if not all([tcg, season_id, parsed_data_json]):
            flash('Session scaduta. Riprova import.', 'warning')
            return redirect(url_for('admin.import_wizard'))

        parsed_data = json.loads(parsed_data_json)

        # Connetti sheet
        sheet = connect_sheet()

        # Se overwrite, cancella dati esistenti prima
        if overwrite:
            from import_base import delete_existing_tournament
            tournament_id = parsed_data['data']['tournament'][0]
            flash('Eliminazione dati esistenti...', 'info')
            delete_existing_tournament(sheet, tournament_id)

        # Scrittura
        write_result = write(sheet, parsed_data, test_mode=test_mode)

        # Cleanup temp files
        if temp_files_json:
            temp_files = json.loads(temp_files_json)
            for key, value in temp_files.items():
                if isinstance(value, list):
                    for f in value:
                        try:
                            os.unlink(f)
                        except:
                            pass
                elif isinstance(value, str):
                    try:
                        os.unlink(value)
                    except:
                        pass

        # Clear session wizard data
        for key in ['wizard_tcg', 'wizard_season_id', 'wizard_test_mode',
                    'wizard_temp_files', 'wizard_parsed_data', 'wizard_upload_time']:
            flask_session.pop(key, None)

        if write_result['success']:
            flash(write_result['message'], 'success')
            return render_template('admin/import_result.html',
                                  tcg=tcg.upper(),
                                  season=season_id,
                                  test_mode=test_mode,
                                  success=True,
                                  output=write_result.get('message', ''))
        else:
            flash(f'Errore import: {write_result.get("error")}', 'danger')
            return redirect(url_for('admin.import_wizard'))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.import_wizard'))


@admin_bp.route('/import/wizard/cancel')
@admin_required
def import_wizard_cancel():
    """
    Annulla wizard e pulisce session.
    """
    from flask import session as flask_session
    import json

    # Cleanup temp files
    temp_files_json = flask_session.get('wizard_temp_files')
    if temp_files_json:
        try:
            temp_files = json.loads(temp_files_json)
            for key, value in temp_files.items():
                if isinstance(value, list):
                    for f in value:
                        try:
                            os.unlink(f)
                        except:
                            pass
                elif isinstance(value, str):
                    try:
                        os.unlink(value)
                    except:
                        pass
        except:
            pass

    # Clear session
    for key in ['wizard_tcg', 'wizard_season_id', 'wizard_test_mode',
                'wizard_temp_files', 'wizard_parsed_data', 'wizard_upload_time']:
        flask_session.pop(key, None)

    flash('Import annullato', 'info')
    return redirect(url_for('admin.dashboard'))


# =============================================================================
# ROUTES - SEASON MANAGEMENT (FASE 4)
# =============================================================================

@admin_bp.route('/seasons')
@admin_required
def seasons():
    """
    Gestione stagioni: lista, creazione, chiusura.

    Mostra:
    - Form creazione nuova stagione (TCG, ID, nome custom, fees)
    - Lista stagioni per TCG (One Piece, Pokemon, Riftbound)
    - Bottoni chiusura per stagioni ACTIVE
    """
    from import_base import connect_sheet

    try:
        sheet = connect_sheet()

        # Recupera tutte le stagioni (escluse ARCHIVED)
        all_seasons = get_seasons(sheet, tcg=None, include_archived=False)

        # Raggruppa per TCG
        seasons_by_tcg = {
            'OP': [s for s in all_seasons if s['id'].startswith('OP')],
            'PKM': [s for s in all_seasons if s['id'].startswith('PKM')],
            'RFB': [s for s in all_seasons if s['id'].startswith('RFB')]
        }

        # Suggerimenti next season ID per ogni TCG
        suggestions = {
            'onepiece': suggest_next_season_id(sheet, 'onepiece'),
            'pokemon': '',  # Pokemon non ha suggestion automatico
            'riftbound': suggest_next_season_id(sheet, 'riftbound')
        }

        # Converti in JSON per JavaScript
        import json
        suggestions_json = json.dumps(suggestions)

        session_info = get_session_info()

        return render_template('admin/seasons.html',
                              seasons_by_tcg=seasons_by_tcg,
                              suggestions=suggestions_json,
                              session_info=session_info)

    except Exception as e:
        flash(f'Errore caricamento stagioni: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/create', methods=['POST'])
@admin_required
def season_create():
    """
    Crea nuova stagione.

    Form data:
    - tcg: TCG type ('onepiece', 'pokemon', 'riftbound')
    - season_id: Season ID (es. OP13, PKM-FS25, RFB02)
    - custom_name: Nome custom (opzionale)
    - entry_fee: Quota iscrizione (default 5.0)
    - pack_cost: Costo busta premio (default 6.0)
    """
    from import_base import connect_sheet

    try:
        tcg = request.form.get('tcg', '').strip()
        season_id = request.form.get('season_id', '').strip().upper()
        custom_name = request.form.get('custom_name', '').strip()
        entry_fee = float(request.form.get('entry_fee', 5.0))
        pack_cost = float(request.form.get('pack_cost', 6.0))

        if not tcg or not season_id:
            flash('TCG e Season ID sono obbligatori', 'danger')
            return redirect(url_for('admin.seasons'))

        # Connetti sheet
        sheet = connect_sheet()

        # Crea stagione
        result = create_season(
            sheet=sheet,
            tcg=tcg,
            season_id=season_id,
            custom_name=custom_name if custom_name else None,
            entry_fee=entry_fee,
            pack_cost=pack_cost
        )

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result.get('error', 'Errore creazione stagione'), 'danger')

        return redirect(url_for('admin.seasons'))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.seasons'))


@admin_bp.route('/season/<season_id>/close', methods=['POST'])
@admin_required
def season_close(season_id):
    """
    Chiude stagione ACTIVE → CLOSED.
    Ricalcola classifica con scarto 2 peggiori se ≥8 tornei.

    Args:
        season_id: ID stagione da chiudere (es. OP12, PKM-FS25)
    """
    from import_base import connect_sheet

    try:
        sheet = connect_sheet()

        # Chiudi stagione
        result = close_season(sheet, season_id)

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result.get('error', 'Errore chiusura stagione'), 'danger')

        return redirect(url_for('admin.seasons'))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.seasons'))
