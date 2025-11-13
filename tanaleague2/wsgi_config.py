import sys

path = '/home/latanadellepulci/tanaleague'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
