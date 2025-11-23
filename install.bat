@echo off
chcp 65001 >nul
echo ========================================
echo    TanaLeague - Installazione Windows
echo ========================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato!
    echo.
    echo Scarica Python da: https://www.python.org/downloads/
    echo Assicurati di selezionare "Add Python to PATH" durante l'installazione!
    echo.
    pause
    exit /b 1
)

echo [OK] Python trovato
python --version
echo.

REM Crea virtual environment (opzionale ma consigliato)
echo Creazione ambiente virtuale...
python -m venv venv
if errorlevel 1 (
    echo [WARN] Impossibile creare venv, continuo senza...
) else (
    echo [OK] Virtual environment creato
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment attivato
)
echo.

REM Installa dipendenze
echo Installazione dipendenze...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRORE] Installazione dipendenze fallita!
    pause
    exit /b 1
)
echo [OK] Dipendenze installate
echo.

REM Verifica config.py
if not exist "tanaleague2\config.py" (
    echo [INFO] config.py non trovato
    echo.
    echo Prossimi passi:
    echo   1. cd tanaleague2
    echo   2. python setup_wizard.py
    echo   3. python init_database.py
    echo   4. python check_setup.py
    echo   5. python app.py
) else (
    echo [OK] config.py trovato
    echo.
    echo Per avviare l'applicazione:
    echo   cd tanaleague2
    echo   python app.py
    echo.
    echo Poi apri: http://localhost:5000
)

echo.
echo ========================================
echo    Installazione completata!
echo ========================================
echo.
pause
