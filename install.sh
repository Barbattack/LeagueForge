#!/bin/bash
# LeagueForge - Installation Script for Mac/Linux

echo "========================================"
echo "   LeagueForge - Installazione Mac/Linux"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRORE] Python3 non trovato!"
    echo
    echo "Installa Python:"
    echo "  Mac:   brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[OK] Python trovato"
python3 --version
echo

# Create virtual environment
echo "Creazione ambiente virtuale..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "[WARN] Impossibile creare venv, continuo senza..."
else
    echo "[OK] Virtual environment creato"
    source venv/bin/activate
    echo "[OK] Virtual environment attivato"
fi
echo

# Install dependencies
echo "Installazione dipendenze..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERRORE] Installazione dipendenze fallita!"
    exit 1
fi
echo "[OK] Dipendenze installate"
echo

# Check config.py
if [ ! -f "leagueforge2/config.py" ]; then
    echo "[INFO] config.py non trovato"
    echo
    echo "Prossimi passi:"
    echo "  1. cd leagueforge2"
    echo "  2. python3 setup_wizard.py"
    echo "  3. python3 init_database.py"
    echo "  4. python3 check_setup.py"
    echo "  5. python3 app.py"
else
    echo "[OK] config.py trovato"
    echo
    echo "Per avviare l'applicazione:"
    echo "  cd leagueforge2"
    echo "  python3 app.py"
    echo
    echo "Poi apri: http://localhost:5000"
fi

echo
echo "========================================"
echo "   Installazione completata!"
echo "========================================"
echo
