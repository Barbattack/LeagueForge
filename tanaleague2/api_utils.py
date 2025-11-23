#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TanaLeague - API Utilities
===========================

Utility per gestire le chiamate API Google Sheets con retry automatico.

FUNZIONALITÀ:
- Retry automatico su errori rate limit (RESOURCE_EXHAUSTED)
- Exponential backoff (attesa crescente tra i tentativi)
- Messaggi user-friendly durante l'attesa
"""

import time
import functools
from typing import Callable, Any

# Errori che triggherano il retry
RETRYABLE_ERRORS = [
    "RESOURCE_EXHAUSTED",
    "Quota exceeded",
    "Rate Limit Exceeded",
    "Too Many Requests",
    "503",
    "429",
]


def is_rate_limit_error(error: Exception) -> bool:
    """Verifica se l'errore è un rate limit."""
    error_str = str(error).lower()
    return any(err.lower() in error_str for err in RETRYABLE_ERRORS)


def with_retry(max_retries: int = 3, base_delay: int = 60):
    """
    Decorator per aggiungere retry automatico alle funzioni.

    Args:
        max_retries: Numero massimo di tentativi
        base_delay: Secondi di attesa base (raddoppia ad ogni retry)

    Usage:
        @with_retry(max_retries=3, base_delay=60)
        def my_api_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not is_rate_limit_error(e):
                        # Non è un rate limit, rilancia subito
                        raise

                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"\n⏳ API occupate (limite raggiunto)")
                        print(f"   Attendo {delay} secondi prima di riprovare...")
                        print(f"   Tentativo {attempt + 1}/{max_retries + 1}")

                        # Countdown visuale
                        for remaining in range(delay, 0, -10):
                            print(f"   ⏱️  {remaining} secondi rimanenti...", end='\r')
                            time.sleep(min(10, remaining))
                        print(" " * 50, end='\r')  # Pulisce la riga

                        print(f"   🔄 Riprovo...")
                    else:
                        print(f"\n❌ API ancora occupate dopo {max_retries + 1} tentativi")
                        print(f"   Riprova tra qualche minuto.")
                        raise

            raise last_error

        return wrapper
    return decorator


def retry_on_rate_limit(func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
    """
    Esegue una funzione con retry automatico su rate limit.

    Args:
        func: Funzione da eseguire
        *args: Argomenti posizionali
        max_retries: Numero massimo di tentativi
        **kwargs: Argomenti keyword

    Returns:
        Risultato della funzione

    Usage:
        result = retry_on_rate_limit(sheet.append_row, data, max_retries=3)
    """
    last_error = None
    base_delay = 60

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e

            if not is_rate_limit_error(e):
                raise

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"\n⏳ API occupate, attendo {delay}s... (tentativo {attempt + 1}/{max_retries + 1})")
                time.sleep(delay)
            else:
                raise

    raise last_error


class APIRateLimiter:
    """
    Classe per gestire rate limiting delle API.

    Usage:
        limiter = APIRateLimiter()

        with limiter.protect():
            sheet.append_row(data)
    """

    def __init__(self, max_retries: int = 3, base_delay: int = 60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.total_retries = 0

    def protect(self):
        """Context manager per proteggere chiamate API."""
        return _RateLimitContext(self)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Esegue una funzione con protezione rate limit."""
        return retry_on_rate_limit(
            func, *args,
            max_retries=self.max_retries,
            **kwargs
        )


class _RateLimitContext:
    """Context manager interno per APIRateLimiter."""

    def __init__(self, limiter: APIRateLimiter):
        self.limiter = limiter

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and is_rate_limit_error(exc_val):
            # Potremmo implementare retry qui se necessario
            pass
        return False  # Non sopprime l'eccezione


# Istanza globale per uso semplice
default_limiter = APIRateLimiter()


def safe_api_call(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper semplice per chiamate API sicure.

    Usage:
        from api_utils import safe_api_call

        safe_api_call(sheet.append_row, [data])
        safe_api_call(worksheet.update, values=data, range_name="A1")
    """
    return default_limiter.execute(func, *args, **kwargs)
