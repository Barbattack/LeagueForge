# -*- coding: utf-8 -*-
"""
TanaLeague - Admin Routes
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

        result = subprocess.run(cmd, cwd='/home/user/TanaLeague/tanaleague2',
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

        suffix = '.tdf' if file.filename.endswith('.tdf') else '.xml'
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        cmd = ['python3', 'import_pokemon.py', '--tdf', tmp_path, '--season', season_id]
        if test_mode:
            cmd.append('--test')

        result = subprocess.run(cmd, cwd='/home/user/TanaLeague/tanaleague2',
                               capture_output=True, text=True, timeout=120)

        os.unlink(tmp_path)

        output = result.stdout + result.stderr

        if result.returncode == 0:
            flash(f'Import Pokemon completato{"(TEST MODE)" if test_mode else ""}!', 'success')
        else:
            flash('Errore durante import', 'danger')

        return render_template('admin/import_result.html',
                             tcg='Pokemon',
                             season=season_id,
                             test_mode=test_mode,
                             success=(result.returncode == 0),
                             output=output)

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/import/riftbound', methods=['POST'])
@admin_required
def import_riftbound():
    """Gestisce import Riftbound da CSV Multi-Round."""
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

        result = subprocess.run(cmd, cwd='/home/user/TanaLeague/tanaleague2',
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
