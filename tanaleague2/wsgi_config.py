"""
WSGI Configuration for TanaLeague
==================================

Questo file viene usato da server WSGI (es. gunicorn, PythonAnywhere).

NOTA: Modifica 'path' con il percorso della TUA installazione!
Esempio PythonAnywhere: '/home/TUOUSERNAME/TanaLeague/tanaleague2'
"""
import sys
from pathlib import Path

# Path dinamico basato sulla posizione di questo file
# Funziona automaticamente ovunque sia installato
path = str(Path(__file__).parent)

# In alternativa, specifica manualmente il path:
# path = '/home/TUOUSERNAME/TanaLeague/tanaleague2'

if path not in sys.path:
    sys.path.append(path)

from app import app as application
