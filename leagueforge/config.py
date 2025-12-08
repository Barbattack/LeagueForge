# -*- coding: utf-8 -*-
"""
LeagueForge - Development Configuration
=======================================

Configurazione per ambiente di sviluppo/test.
Generato automaticamente per l'admin del progetto.
"""

import os

# ==============================================================================
# PERSONALIZZAZIONE NEGOZIO
# ==============================================================================
STORE_NAME = os.getenv("STORE_NAME") or "LeagueForge Dev"
STORE_LOGO = os.getenv("STORE_LOGO") or "static/logo.png"
STORE_TAGLINE = os.getenv("STORE_TAGLINE") or "Sistema di gestione classifiche TCG - Dev Environment"

# Colori tema
STORE_PRIMARY_COLOR = os.getenv("STORE_PRIMARY_COLOR") or "#1a73e8"
STORE_SECONDARY_COLOR = os.getenv("STORE_SECONDARY_COLOR") or "#34a853"

# Link social
STORE_INSTAGRAM = os.getenv("STORE_INSTAGRAM") or ""
STORE_WHATSAPP = os.getenv("STORE_WHATSAPP") or ""
STORE_WEBSITE = os.getenv("STORE_WEBSITE") or ""

# ==============================================================================
# GOOGLE SHEETS
# ==============================================================================
# Sheet ID: legge da ENV prima, fallback su valore locale
SHEET_ID = os.getenv("SHEET_ID") or "1as29K5Whi94eWUxR2F2Wgy0tt2LFho_cqQrA68rQK-w"

# Credenziali Google Service Account
# Su Render: usa GOOGLE_CREDENTIALS_JSON (JSON inline come stringa)
# In locale: usa file service_account_credentials.json
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE") or "service_account_credentials.json"
CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")  # Per Render (JSON inline)

# ==============================================================================
# ADMIN LOGIN
# ==============================================================================
# Legge da ENV prima, fallback su valori locali
# Username: admin, Password: dev123 (solo in locale)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") or "admin"
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH") or "pbkdf2:sha256:600000$9N7mVZgfeStgfWzvfaoGWA==$lfwwWBxzcd3W5k+Pl212nOBEke5nJzEUSgjKrhP5h4c="

# Timeout sessione admin (minuti)
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT") or "30")

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================
# Refresh cache (minuti)
CACHE_REFRESH_MINUTES = int(os.getenv("CACHE_REFRESH_MINUTES") or "5")

# Nome file cache locale
CACHE_FILE = os.getenv("CACHE_FILE") or "cache_data.json"

# ==============================================================================
# APP SETTINGS
# ==============================================================================
# Chiave segreta per Flask sessions
SECRET_KEY = os.getenv("SECRET_KEY") or "827ab612922caa33c1ddbf3f038bd0734d2ca3c6d5105269e336012da83e8639"

# Debug mode: False in produzione (Render), True in locale
DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')

# ==============================================================================
# TCG SETTINGS
# ==============================================================================
# TCG abilitati
ENABLE_ONEPIECE = True
ENABLE_POKEMON = True
ENABLE_RIFTBOUND = True
