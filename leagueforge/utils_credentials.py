# -*- coding: utf-8 -*-
"""
Utilities per gestione credenziali Google - funziona in locale E su Render
"""
import os
import json
import tempfile
from google.oauth2.service_account import Credentials


def get_google_credentials(scopes):
    """
    Carica credenziali Google da file o da environment variable.

    Supporta:
    - Locale: file JSON sul disco
    - Render/Cloud: variabile GOOGLE_CREDENTIALS_JSON

    Args:
        scopes: Lista scope Google API

    Returns:
        Credentials object
    """
    # OPZIONE 1: Environment variable (Render/Cloud)
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        # Parse JSON da variabile d'ambiente
        try:
            creds_dict = json.loads(creds_json)
            return Credentials.from_service_account_info(creds_dict, scopes=scopes)
        except json.JSONDecodeError as e:
            raise ValueError(f"GOOGLE_CREDENTIALS_JSON non è un JSON valido: {e}")

    # OPZIONE 2: File path (Locale)
    creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    if creds_file and os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=scopes)

    # OPZIONE 3: Default locale (fallback)
    default_paths = [
        os.path.join(os.path.dirname(__file__), 'service_account_credentials.json'),
        '/etc/secrets/credentials.json',  # Render Secret Files
    ]

    for path in default_paths:
        if os.path.exists(path):
            return Credentials.from_service_account_file(path, scopes=scopes)

    raise FileNotFoundError(
        "Credenziali Google non trovate!\n"
        "Configura una di queste opzioni:\n"
        "1. Variabile d'ambiente GOOGLE_CREDENTIALS_JSON (JSON completo)\n"
        "2. Variabile d'ambiente GOOGLE_CREDENTIALS_FILE (path al file)\n"
        "3. File service_account_credentials.json nella cartella leagueforge/\n"
    )
