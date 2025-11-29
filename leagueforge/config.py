# -*- coding: utf-8 -*-
"""
LeagueForge - Configuration (Cloud-ready)
==========================================

Questo file carica configurazione da environment variables (Render/Cloud)
oppure da valori di default (sviluppo locale).

NON committare questo file se contiene credenziali reali!
"""

import os
import secrets

# ==============================================================================
# PERSONALIZZAZIONE NEGOZIO
# ==============================================================================
STORE_NAME = os.getenv('STORE_NAME', 'LeagueForge')
STORE_LOGO = os.getenv('STORE_LOGO', 'static/logo.png')
STORE_TAGLINE = os.getenv('STORE_TAGLINE', 'Sistema di gestione classifiche TCG')

STORE_PRIMARY_COLOR = os.getenv('STORE_PRIMARY_COLOR', '#1a73e8')
STORE_SECONDARY_COLOR = os.getenv('STORE_SECONDARY_COLOR', '#34a853')

STORE_INSTAGRAM = os.getenv('STORE_INSTAGRAM', '')
STORE_WHATSAPP = os.getenv('STORE_WHATSAPP', '')
STORE_WEBSITE = os.getenv('STORE_WEBSITE', '')

# ==============================================================================
# GOOGLE SHEETS
# ==============================================================================
SHEET_ID = os.getenv('SHEET_ID')
if not SHEET_ID:
    raise ValueError(
        "SHEET_ID non configurato!\n"
        "Locale: Crea config.py da config.example.py\n"
        "Cloud: Configura environment variable SHEET_ID"
    )

# Credenziali: Gestite da utils_credentials.py
# Supporta: GOOGLE_CREDENTIALS_JSON (cloud) o GOOGLE_CREDENTIALS_FILE (locale)
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'service_account_credentials.json')

# ==============================================================================
# ADMIN LOGIN
# ==============================================================================
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', 'pbkdf2:sha256:600000$CHANGE_ME')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '30'))

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================
CACHE_REFRESH_MINUTES = int(os.getenv('CACHE_REFRESH_MINUTES', '5'))
CACHE_FILE = os.getenv('CACHE_FILE', 'cache_data.json')

# ==============================================================================
# APP SETTINGS
# ==============================================================================
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# ==============================================================================
# TCG SETTINGS
# ==============================================================================
ENABLE_ONEPIECE = os.getenv('ENABLE_ONEPIECE', 'True').lower() in ('true', '1', 'yes')
ENABLE_POKEMON = os.getenv('ENABLE_POKEMON', 'True').lower() in ('true', '1', 'yes')
ENABLE_RIFTBOUND = os.getenv('ENABLE_RIFTBOUND', 'True').lower() in ('true', '1', 'yes')
