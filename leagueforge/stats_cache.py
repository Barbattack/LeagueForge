# -*- coding: utf-8 -*-
"""
stats_cache.py
A simple file-based cache for stats objects per scope.
"""

import os, json, time
from pathlib import Path
from typing import Callable, Dict, Any

BASE_DIR = Path(__file__).resolve().parent / "stats_cache"
BASE_DIR.mkdir(parents=True, exist_ok=True)

def _path_for(scope: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in scope)
    return BASE_DIR / f"stats_{safe}.json"

def get_cached(scope: str, max_age_seconds: int) -> Dict[str, Any] | None:
    p = _path_for(scope)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        ts = obj.get("_cached_at", 0)
        if time.time() - ts <= max_age_seconds:
            return obj.get("data")
        return None
    except Exception:
        return None

def set_cached(scope: str, data: Dict[str, Any]) -> None:
    p = _path_for(scope)
    payload = {"_cached_at": time.time(), "data": data}
    p.write_text(json.dumps(payload, ensure_ascii=False, separators=(",",":")), encoding="utf-8")

def clear(scope: str) -> bool:
    p = _path_for(scope)
    if p.exists():
        p.unlink()
        return True
    return False