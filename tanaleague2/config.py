import os
# -*- coding: utf-8 -*-
"""
TanaLeague - Configuration
===========================
Credenziali e impostazioni app
"""

# Google Sheets
SHEET_ID = "19ZF35DTmgZG8v1GfzKE5JmMUTXLo300vuw_AdrgQPFE"
CREDENTIALS_FILE = os.getenv("PULCI_SA_CREDENTIALS") or (
    "secrets/service_account.json" if os.path.exists("secrets/service_account.json") else "service_account_credentials.json"
)

# Admin Login
ADMIN_USER = "barbattack"
ADMIN_PASS = "tanaleague2025"  # CAMBIA QUESTA PASSWORD!

# Cache Settings
CACHE_REFRESH_MINUTES = 5
CACHE_FILE = "cache_data.json"

# App Settings
SECRET_KEY = "tanaleague-secret-key-change-me"  # Per Flask sessions
DEBUG = True  # Metti False in produzione