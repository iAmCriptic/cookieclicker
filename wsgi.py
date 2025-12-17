"""
WSGI Konfiguration für PythonAnywhere
======================================

Kopiere diesen Inhalt in deine PythonAnywhere WSGI-Datei:
/var/www/techportal_eu_pythonanywhere_com_wsgi.py

WICHTIG: Passe den Pfad an!
"""

import sys, os

# ============================================
# PFAD ANPASSEN! 
# ============================================
path = '/home/techportal/Primsateams_web_V0'

if path not in sys.path:
    sys.path.append(path)

# Arbeitsverzeichnis setzen (wichtig für Templates/Static)
os.chdir(path)

# Umgebungsvariablen
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONANYWHERE_SITE'] = 'true'

# Flask-App importieren
from app import app as application
