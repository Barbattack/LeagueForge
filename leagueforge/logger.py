"""
LeagueForge - Logging Configuration
==================================

Configurazione centralizzata del logging per tutta l'applicazione.

USO:
    from logger import get_logger
    logger = get_logger(__name__)

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.exception("Error with traceback")  # Usa dentro except block

LIVELLI:
    DEBUG    - Dettagli per debugging (non in produzione)
    INFO     - Operazioni normali (import completato, cache refresh)
    WARNING  - Situazioni anomale ma gestite (cache miss, retry)
    ERROR    - Errori che impediscono operazioni
    CRITICAL - Errori gravi che richiedono intervento

FILE LOG:
    - logs/leagueforge.log      - Log principale (INFO+)
    - logs/leagueforge_debug.log - Log dettagliato (DEBUG+, solo se DEBUG=True)
    - Console                   - Output colorato (INFO+)
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

# Directory logs (relativa a leagueforge2/)
LOG_DIR = Path(__file__).parent / "logs"

# Dimensione massima file log (5 MB)
MAX_LOG_SIZE = 5 * 1024 * 1024

# Numero di file di backup da mantenere
BACKUP_COUNT = 3

# Formato log
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Debug mode (legge da environment o config)
DEBUG_MODE = os.environ.get("TANALEAGUE_DEBUG", "false").lower() == "true"


# =============================================================================
# SETUP LOGGING
# =============================================================================

def setup_logging():
    """
    Configura il sistema di logging.
    Chiamato automaticamente al primo import di get_logger().
    """
    # Crea directory logs se non esiste
    LOG_DIR.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger("leagueforge")
    root_logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    # Evita handler duplicati
    if root_logger.handlers:
        return root_logger

    # ---------------------------------------------------------------------
    # Handler 1: File principale (INFO+)
    # ---------------------------------------------------------------------
    file_handler = RotatingFileHandler(
        LOG_DIR / "leagueforge.log",
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # ---------------------------------------------------------------------
    # Handler 2: Console (INFO+, con colori se supportato)
    # ---------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato console più compatto
    console_format = "%(levelname)-8s | %(message)s"
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)

    # ---------------------------------------------------------------------
    # Handler 3: Debug file (solo in DEBUG mode)
    # ---------------------------------------------------------------------
    if DEBUG_MODE:
        debug_handler = RotatingFileHandler(
            LOG_DIR / "leagueforge_debug.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=1,
            encoding="utf-8"
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(debug_handler)

    return root_logger


# =============================================================================
# PUBLIC API
# =============================================================================

_logging_initialized = False

def get_logger(name: str = None) -> logging.Logger:
    """
    Ottiene un logger configurato.

    Args:
        name: Nome del modulo (usa __name__ per auto-naming)
              Es: "leagueforge.app", "leagueforge.achievements"

    Returns:
        Logger configurato

    Esempio:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Operazione completata")
    """
    global _logging_initialized

    if not _logging_initialized:
        setup_logging()
        _logging_initialized = True

    # Prefissa con "leagueforge." se non presente
    if name:
        if not name.startswith("leagueforge"):
            name = f"leagueforge.{name}"
    else:
        name = "leagueforge"

    return logging.getLogger(name)


def log_import_start(logger: logging.Logger, tcg: str, file_path: str, season: str):
    """Helper per loggare inizio import torneo."""
    logger.info("=" * 60)
    logger.info(f"IMPORT {tcg.upper()} - Season: {season}")
    logger.info(f"File: {file_path}")
    logger.info("=" * 60)


def log_import_complete(logger: logging.Logger, tcg: str, tournament_id: str,
                        participants: int, achievements: int = 0):
    """Helper per loggare completamento import."""
    logger.info(f"Import completato: {tournament_id}")
    logger.info(f"  Partecipanti: {participants}")
    if achievements > 0:
        logger.info(f"  Achievement sbloccati: {achievements}")
    logger.info("-" * 60)


def log_error_with_context(logger: logging.Logger, error: Exception,
                           context: dict = None):
    """Helper per loggare errori con contesto."""
    logger.error(f"Errore: {type(error).__name__}: {error}")
    if context:
        for key, value in context.items():
            logger.error(f"  {key}: {value}")
    logger.exception("Traceback:")


# =============================================================================
# INIT
# =============================================================================

if __name__ == "__main__":
    # Test logging
    logger = get_logger("test")
    logger.debug("Debug message (visibile solo in DEBUG mode)")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    print(f"\nLog files in: {LOG_DIR}")
