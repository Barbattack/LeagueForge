# -*- coding: utf-8 -*-
"""
LeagueForge - Configuration Template
====================================

ISTRUZIONI RAPIDE:
1. Copia questo file come "config.py"
2. Modifica i valori con le tue credenziali
3. NON caricare mai config.py su GitHub!

OPPURE: Esegui "python setup_wizard.py" per configurazione guidata!
"""

import os

# ==============================================================================
# PERSONALIZZAZIONE NEGOZIO
# ==============================================================================
# Cambia questi valori per personalizzare l'app con il nome del tuo negozio

STORE_NAME = "LeagueForge"          # Nome visualizzato nell'app (es. "MioNegozio League")
STORE_LOGO = "static/logo.png"     # Path al logo (sostituisci il file)
STORE_TAGLINE = "Sistema di gestione classifiche TCG"  # Sottotitolo homepage

# Colori tema (opzionale - valori CSS)
STORE_PRIMARY_COLOR = "#1a73e8"    # Colore principale (bottoni, link)
STORE_SECONDARY_COLOR = "#34a853"  # Colore secondario (accenti)

# Link social (lascia vuoto "" se non li usi)
STORE_INSTAGRAM = ""               # es. "https://instagram.com/tuonegozio"
STORE_WHATSAPP = ""                # es. "https://wa.me/391234567890"
STORE_WEBSITE = ""                 # es. "https://tuonegozio.it"

# ==============================================================================
# GOOGLE SHEETS
# ==============================================================================
# ID del tuo Google Sheet (lo trovi nell'URL)
# Esempio URL: https://docs.google.com/spreadsheets/d/ABC123.../edit
# L'ID è la parte ABC123...
SHEET_ID = "IL_TUO_GOOGLE_SHEET_ID_QUI"

# Percorso al file JSON delle credenziali del service account
# Su PythonAnywhere: usa path assoluto "/home/username/LeagueForge/leagueforge2/credentials.json"
# In locale: "service_account_credentials.json" nella stessa cartella
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE") or "service_account_credentials.json"

# ==============================================================================
# ADMIN LOGIN
# ==============================================================================
# Username per accesso admin panel
ADMIN_USERNAME = "admin"

# Password HASH (NON la password in chiaro!)
# Per generare l'hash, esegui:
#   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('TUA_PASSWORD'))"
# Poi copia l'output qui sotto
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:600000$SOSTITUISCI_CON_HASH_GENERATO"

# Timeout sessione admin in minuti
SESSION_TIMEOUT = 30

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================
# Ogni quanti minuti refreshare la cache dal Google Sheet
CACHE_REFRESH_MINUTES = 5

# Nome del file di cache locale
CACHE_FILE = "cache_data.json"

# ==============================================================================
# APP SETTINGS
# ==============================================================================
# Chiave segreta per Flask sessions
# IMPORTANTE: Genera una chiave casuale!
# Esegui: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = "genera-una-chiave-casuale-qui"

# Debug mode (metti False in produzione!)
DEBUG = False

# ==============================================================================
# TCG SETTINGS (opzionale)
# ==============================================================================
# TCG abilitati (True = attivo, False = nascosto)
ENABLE_ONEPIECE = True
ENABLE_POKEMON = True
ENABLE_RIFTBOUND = True
