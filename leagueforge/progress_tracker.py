# -*- coding: utf-8 -*-
"""
=================================================================================
LeagueForge - Progress Tracker
=================================================================================

Sistema per tracciare il progresso degli import in real-time.
Usato per streaming SSE (Server-Sent Events) durante import lunghi.

UTILIZZO:
    tracker = ProgressTracker()

    tracker.log("Inizio import...")
    tracker.update_progress(10, "Validazione file...")
    tracker.update_progress(30, "Parsing dati...")
    tracker.update_progress(100, "Completato!")

    # Recupera tutti i messaggi
    messages = tracker.get_messages()

=================================================================================
"""

import time
from typing import List, Dict
import threading


class ProgressTracker:
    """
    Traccia il progresso di un'operazione con messaggi e percentuale.
    Thread-safe per permettere aggiornamenti da thread diversi.
    """

    def __init__(self):
        self.messages: List[Dict] = []
        self.current_progress = 0
        self.lock = threading.Lock()
        self.completed = False
        self.error = None

    def log(self, message: str, level: str = 'info'):
        """
        Aggiunge un messaggio di log.

        Args:
            message: Testo del messaggio
            level: Livello ('info', 'success', 'warning', 'error')
        """
        with self.lock:
            self.messages.append({
                'type': 'log',
                'level': level,
                'message': message,
                'timestamp': time.time()
            })

    def update_progress(self, percentage: int, message: str = None):
        """
        Aggiorna la percentuale di progresso.

        Args:
            percentage: Percentuale 0-100
            message: Messaggio opzionale da loggare
        """
        with self.lock:
            self.current_progress = min(100, max(0, percentage))
            self.messages.append({
                'type': 'progress',
                'percentage': self.current_progress,
                'message': message,
                'timestamp': time.time()
            })

    def complete(self, success: bool = True, message: str = None):
        """
        Marca l'operazione come completata.

        Args:
            success: True se completata con successo
            message: Messaggio finale
        """
        with self.lock:
            self.completed = True
            if not success:
                self.error = message
            self.messages.append({
                'type': 'complete',
                'success': success,
                'message': message,
                'timestamp': time.time()
            })

    def get_messages(self, since_index: int = 0) -> List[Dict]:
        """
        Recupera messaggi dall'indice specificato.

        Args:
            since_index: Indice da cui partire (0 = tutti)

        Returns:
            Lista di messaggi
        """
        with self.lock:
            return self.messages[since_index:]

    def get_current_progress(self) -> int:
        """Ritorna la percentuale corrente."""
        with self.lock:
            return self.current_progress

    def is_completed(self) -> bool:
        """Ritorna True se completato."""
        with self.lock:
            return self.completed

    def has_error(self) -> bool:
        """Ritorna True se c'è stato un errore."""
        with self.lock:
            return self.error is not None


# =============================================================================
# STORAGE GLOBALE PER TRACKER
# =============================================================================

# Dict per mantenere tracker attivi (chiave: session_id o import_id)
_active_trackers = {}
_trackers_lock = threading.Lock()


def create_tracker(tracker_id: str) -> ProgressTracker:
    """
    Crea un nuovo tracker e lo registra.

    Args:
        tracker_id: ID univoco per questo tracker

    Returns:
        ProgressTracker instance
    """
    with _trackers_lock:
        tracker = ProgressTracker()
        _active_trackers[tracker_id] = tracker
        return tracker


def get_tracker(tracker_id: str) -> ProgressTracker:
    """
    Recupera un tracker esistente.

    Args:
        tracker_id: ID del tracker

    Returns:
        ProgressTracker instance o None se non esiste
    """
    with _trackers_lock:
        return _active_trackers.get(tracker_id)


def remove_tracker(tracker_id: str):
    """
    Rimuove un tracker dalla memoria.

    Args:
        tracker_id: ID del tracker da rimuovere
    """
    with _trackers_lock:
        if tracker_id in _active_trackers:
            del _active_trackers[tracker_id]


def cleanup_old_trackers(max_age_seconds: int = 3600):
    """
    Rimuove tracker vecchi per liberare memoria.

    Args:
        max_age_seconds: Età massima in secondi (default 1 ora)
    """
    now = time.time()
    with _trackers_lock:
        to_remove = []
        for tracker_id, tracker in _active_trackers.items():
            if tracker.is_completed():
                # Check età ultimo messaggio
                if tracker.messages:
                    last_msg_time = tracker.messages[-1]['timestamp']
                    if now - last_msg_time > max_age_seconds:
                        to_remove.append(tracker_id)

        for tracker_id in to_remove:
            del _active_trackers[tracker_id]
