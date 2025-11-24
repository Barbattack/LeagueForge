# 🏆 TanaLeague

**Sistema di gestione classifiche e statistiche per leghe competitive di Trading Card Games (TCG)**

Web app Flask completa per tracciare tornei, classifiche, statistiche avanzate, profili giocatori e achievement per **One Piece TCG**, **Pokémon TCG** e **Riftbound TCG**.

🌐 **Live:** [latanadellepulci.pythonanywhere.com](https://latanadellepulci.pythonanywhere.com)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

---

## 📋 Indice

- [Caratteristiche](#-caratteristiche)
- [TCG Supportati](#-tcg-supportati)
- [Novità v2.0](#-novità-v20)
- [Quick Start](#-quick-start)
- [Architettura](#-architettura)
- [Import Tornei](#-import-tornei)
- [Achievement System](#-achievement-system-new)
- [Deploy](#-deploy-su-pythonanywhere)
- [Documentazione](#-documentazione)
- [Franchise Model](#-franchise-model)
- [Struttura Progetto](#-struttura-progetto)

---

## ✨ Caratteristiche

### Funzionalità Principali
- **📊 Classifiche Stagionali** - Rankings con scarto dinamico (migliori N-2 tornei)
- **🏅 Achievement System** - 40+ achievement sbloccabili automaticamente
- **📈 Statistiche Avanzate** - MVP, Sharpshooter, Metronome, Phoenix, Big Stage, Closer
- **👤 Profili Giocatori** - Storico completo, win rate, trend, 3 grafici avanzati (doughnut, bar, radar), achievement
- **📉 Analytics** - Pulse (KPI), Tales (narrative), Hall of Fame
- **🔄 Import Automatico** - Da CSV (One Piece), TDF/XML (Pokémon), CSV Multi-Round (Riftbound)
- **⚡ Cache Intelligente** - Aggiornamento automatico ogni 5 minuti
- **🎮 Multi-TCG** - Gestione separata per 3 giochi diversi

---

## 🎮 TCG Supportati

### 🏴‍☠️ One Piece TCG
- **Status**: ✅ Completo
- **Import**: CSV da Limitlesstcg
- **Sistema Punti**: W=3, L=0 (no pareggi)
- **Display Nomi**: Nome completo (default)
- **Features**: Classifiche, stats, achievement, profili

### ⚡ Pokémon TCG
- **Status**: ✅ Completo
- **Import**: TDF/XML da Play! Pokémon Tournament
- **Sistema Punti**: W=3, D=1, L=0 (con pareggi)
- **Display Nomi**: "Nome I." (es. "Pietro C.")
- **Features**: Classifiche, stats, achievement, match tracking H2H

### 🌌 Riftbound TCG
- **Status**: ✅ Completo (UPDATED!)
- **Import**: CSV Multi-Round (uno per round, aggregati automaticamente)
- **Sistema Punti**: W=3, D=1, L=0 (con pareggi)
- **Display Nomi**: First Name + Last Name
- **Features**: Classifiche, stats avanzate (W-L-D tracking), achievement, multi-round support

---

## 🆕 Novità v2.0

### Achievement System 🏅
- **40+ achievement** organizzati in 7 categorie
- **Auto-unlock** durante import tornei
- **Profili giocatore** con achievement sbloccati
- **Pagina dedicata** `/achievements` con progress tracking
- **Achievement Detail Page** `/achievement/<id>` con lista chi l'ha sbloccato e badge "Pioneer"
- **Card cliccabili** con hover effects e invito a esplorare
- Categorie: Glory, Giant Slayer, Consistency, Legacy, Wildcards, Seasonal, Heartbreak
- **ARCHIVED seasons** escluse dal calcolo achievement (solo stagioni attive)

### Riftbound Support 🌌
- **Import CSV Multi-Round** con aggregazione automatica (R1.csv,R2.csv,R3.csv)
- **Stats avanzate** con W-L-D tracking dettagliato (come Pokémon!)
- **Seasonal standings** automatici
- **Achievement unlock** integrato
- User ID come Membership Number

### Pokémon Enhancements ⚡
- **Seasonal standings** automatici (come Riftbound/OP)
- **Achievement unlock** integrato
- Display personalizzato "Nome I."

### UI/UX Improvements 🎨
- **Grafici Avanzati Profilo Giocatore** 📊
  - Match Record (doughnut): W-T-L lifetime con percentuali
  - Ranking Distribution (bar): Frequenza in ogni fascia (1°, 2°, 3°, Top8, oltre)
  - Performance Radar (pentagon): 5 metriche normalizzate (Win Rate, Top8 Rate, Victory Rate, Avg Perf, Consistency)
  - 9 tooltip informativi per user-friendly UX
- **Nuova pagina Classifiche** (`/classifiche`) con lista tutte le stagioni
- **Menu rinnovato** con Home, Classifiche, Achievement, Stats
- **Pulsanti PKM/RFB attivi** sulla homepage
- **Stagioni ARCHIVED nascoste** da dropdown e liste
- **Custom name display** per TCG (OP: full, PKM: Nome I., RFB: nickname)
- **Lista giocatori corretta** con punti medi e stats accurate

---

## 🆕 Recent Updates (Nov 2025)

### 🏪 v2.3 - Franchise Model + Plug-and-Play (Latest)

- **Franchise Tools**: Strumenti per distribuire TanaLeague ad altri negozi
  - `create_store_package.py` - Crea pacchetti ZIP pre-configurati
  - `api_utils.py` - Retry automatico su rate limit API
  - `install.bat` / `install.sh` - Script installazione
- **Modello Plug-and-Play**:
  - I negozi ricevono uno ZIP, estraggono e fanno doppio-click!
  - Nessuna configurazione tecnica richiesta
  - Google Sheets separati per ogni negozio
- **Setup Wizard Migliorato**: Configurazione interattiva completa
- **Rate Limit Handling**: Exponential backoff automatico per API Google
- **Documentazione Franchise**: Guida completa per franchise manager

### 🏗️ v2.2 - Blueprint Refactor + Infrastructure

- **Flask Blueprints**: App.py ridotto da 1527 → 1037 righe
  - `routes/admin.py` - Route admin (login, dashboard, import)
  - `routes/achievements.py` - Route achievement (catalogo, dettaglio)
- **CI/CD Pipeline**: GitHub Actions per test automatici
- **Sistema Logging**: Structured logging con RotatingFileHandler
- **Backup Script**: `backup_sheets.py` per backup Google Sheets → CSV
- **Setup Locale**: Documentazione completa per test su Windows/Mac/Linux
- **DEVELOPMENT.md**: Nuova guida sviluppo con troubleshooting

### 🏅 Achievement Detail Page
- **Nuova pagina `/achievement/<id>`** per ogni achievement:
  - Lista completa di chi l'ha sbloccato
  - **Badge "Pioneer"** dorato per il primo a sbloccarlo
  - Data di unlock e link al profilo giocatore
  - Statistiche: X su Y giocatori (Z%)
  - Effetti speciali per achievement Legendary/Epic
- **Card cliccabili** nella pagina `/achievements` con:
  - Hover effects (scale + shadow)
  - Hint "Scopri chi" con freccia
  - Messaggio introduttivo invitante

### 🏠 Landing Page Rinnovata
- **Ticker LIVE** con stats globali (tutti i TCG, non solo uno)
  - Giocatori attivi, tornei disputati, achievement sbloccati
  - Domande random che creano curiosità
- **Social Links**: Instagram + WhatsApp integrati
- **CTAs engaging**: "Partecipa ai tornei" con link WhatsApp
- **Box "Prossimi Tornei"** con link Instagram per aggiornamenti

### 🔧 Bug Fixes & Improvements
- **Fixed**: Achievement system ora esclude stagioni ARCHIVED dal calcolo stats
- **Fixed**: Regex season ID accetta formati estesi (es. `PKM-FS25`, `RFB-S1`)
- **Fixed**: Ticker globale calcola stats corrette da tutti i TCG
- **Fixed**: Player list stats now show correct data (tournaments, wins, avg points)
- **Fixed**: Tournament record in player history shows actual W-T-L instead of wrong ranking
- **Fixed**: ARCHIVED seasons skip worst-2-tournament drop (data archive only)

### 📊 Advanced Player Charts
- **3 grafici interattivi** nella scheda giocatore:
  - **Doughnut Chart**: Match Record lifetime (W-T-L con percentuali)
  - **Bar Chart**: Distribuzione ranking (🥇 1°, 🥈 2°, 🥉 3°, Top8, oltre)
  - **Radar Chart**: Performance overview su 5 metriche (Win Rate, Top8 Rate, Victory Rate, Avg Perf, Consistency)
- **9 tooltip informativi** con spiegazioni dettagliate per ogni metrica
- **Formule ottimizzate**: Avg Performance normalizzato a 25pt, Consistency basato su std dev
- **Responsive design** con Chart.js 4.4.0

---

## 🚀 Quick Start

### Prerequisiti
```bash
- Python 3.8+
- Google Cloud Project con Sheets API abilitato
- Service Account credentials JSON
- PythonAnywhere account (per deploy)
```

### Installazione Locale

```bash
# 1. Clone repository
git clone <repository-url>
cd TanaLeague

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Configura credenziali
# - Scarica service_account_credentials.json da Google Cloud
# - Metti in tanaleague2/

# 4. Configura SHEET_ID
# - Modifica SHEET_ID in tanaleague2/config.py
# - Oppure in ogni import script

# 5. Setup Achievement System (UNA VOLTA!)
cd tanaleague2
python setup_achievements.py
# Questo crea i fogli Achievement_Definitions e Player_Achievements

# 6. Run app locale
python app.py
```

Webapp disponibile su `http://localhost:5000`

---

## 🏗️ Architettura

```
┌─────────────────┐
│  Google Sheets  │  ← Database (Config, Results, Players, Tournaments, Achievements)
└────────┬────────┘
         │ (gspread API)
         ↓
┌─────────────────┐
│   Flask App     │  ← Backend Python
│   + Blueprints  │  ← Modular routes (admin, achievements)
│   + Cache       │  ← Cache file-based (5 min TTL)
│   + Logging     │  ← Structured logging (RotatingFileHandler)
└────────┬────────┘
         │ (Jinja2)
         ↓
┌─────────────────┐
│  HTML Templates │  ← Frontend Bootstrap 5 + Chart.js
│   + Bootstrap   │
└─────────────────┘
```

### Google Sheets Structure

| Sheet | Descrizione |
|-------|-------------|
| **Config** | Configurazione stagioni (ID, nome, status, settings) |
| **Tournaments** | Lista tornei (ID, data, partecipanti, vincitore) |
| **Results** | Risultati individuali (giocatore, rank, punti, W-L-D) |
| **Players** | Anagrafica giocatori (membership, nome, TCG, stats lifetime) |
| **Seasonal_Standings_PROV** | Classifiche provvisorie (stagioni ACTIVE) |
| **Seasonal_Standings_FINAL** | Classifiche finali (stagioni CLOSED) |
| **Achievement_Definitions** | Definizioni 40 achievement (NEW!) |
| **Player_Achievements** | Achievement sbloccati (membership, ach_id, date) (NEW!) |
| **Pokemon_Matches** | Match H2H Pokemon (opzionale) |
| **Vouchers** | Buoni negozio (solo One Piece) |

---

## 📥 Import Tornei

### Architettura Unificata

Gli script utilizzano il modulo `import_base.py` che centralizza tutte le funzioni comuni:
- Connessione Google Sheets
- Calcolo punti TanaLeague
- Aggiornamento Players e Seasonal_Standings
- Sblocco achievement

### One Piece TCG (Multi-Round)

```bash
cd tanaleague2
python import_onepiece.py --rounds R1.csv,R2.csv,R3.csv,R4.csv --classifica ClassificaFinale.csv --season OP12
```

**Formato CSV richiesto**: Export dal portale ufficiale Bandai (uno per round + classifica finale)
- Calcola automaticamente W/T/L dal delta punti tra round (+3=Win, +1=Tie, +0=Loss)
- Legge OMW% dal file ClassificaFinale

### Pokémon TCG (TDF/XML)

```bash
cd tanaleague2
python import_pokemon.py --tdf path/to/tournament.tdf --season PKM-FS25
```

**Formato TDF richiesto**: Export da Play! Pokémon Tournament software

### Riftbound TCG (Multi-Round)

```bash
cd tanaleague2
python import_riftbound.py --rounds R1.csv,R2.csv,R3.csv --season RFB01
```

**Formato CSV richiesto**: Export CSV dal software gestione tornei (uno per round)
- Deve contenere: Player User ID, First/Last Name, Event Record (W-L-D)
- Multi-round fornisce stats dettagliate W-L-D come Pokémon!

### Test Mode (Dry Run)

Tutti gli import supportano `--test` per verificare senza scrivere:

```bash
python import_onepiece.py --rounds R1.csv,R2.csv,R3.csv,R4.csv --classifica Finale.csv --season OP12 --test
python import_pokemon.py --tdf file.tdf --season PKM-FS25 --test
python import_riftbound.py --rounds R1.csv,R2.csv,R3.csv --season RFB01 --test
```

### Reimport (Sovrascrittura)

Per correggere un torneo già importato, usa `--reimport`:

```bash
python import_onepiece.py --rounds R1.csv,R2.csv,R3.csv,R4.csv --classifica Finale.csv --season OP12 --reimport
```

---

## 🏅 Achievement System (NEW!)

### Setup (Una volta sola)

```bash
cd tanaleague2
python setup_achievements.py
```

Questo crea e popola:
- `Achievement_Definitions` (40 achievement predefiniti)
- `Player_Achievements` (vuoto, si popola automaticamente)

### Categorie Achievement (40 totali)

| Categoria | Count | Esempi |
|-----------|-------|--------|
| 🏆 **Glory** | 7 | First Blood, King of the Hill, Perfect Storm, Undefeated Season |
| ⚔️ **Giant Slayer** | 6 | Dragonslayer, Kingslayer, Gatekeeper, Upset Artist |
| 📈 **Consistency** | 8 | Hot Streak, Unstoppable Force, Season Warrior, Iron Wall |
| 🌍 **Legacy** | 8 | Debutto, Veteran, Gladiator, Hall of Famer, Triple Crown |
| 🎪 **Wildcards** | 4 | The Answer (42 pt), Lucky Seven, Triple Threat |
| ⏰ **Seasonal** | 3 | Opening Act, Grand Finale, Season Sweep |
| 💔 **Heartbreak** | 5 | Rookie Struggles, Forever Second, Storm Cloud |

### Auto-Unlock

Gli achievement si sbloccano **automaticamente** quando importi tornei:

```bash
python import_onepiece.py --csv file.csv --season OP12
# Output:
# ...
# 🎮 Check achievement...
# 🏆 0000012345: 🎬 First Blood
# 🏆 0000012345: 📅 Regular
# ✅ 2 achievement sbloccati!
```

### Visualizzazione

- **Profilo Giocatore** (`/player/<membership>`): Achievement sbloccati con emoji, descrizione, data
- **Pagina Achievement** (`/achievements`): Tutti i 40 achievement con % unlock, card cliccabili
- **Dettaglio Achievement** (`/achievement/<id>`): Chi l'ha sbloccato, badge Pioneer, stats

---

## 🚀 Deploy su PythonAnywhere

### 1. Upload Files

```bash
# Via git (consigliato)
git clone <repository-url>

# Oppure upload manuale:
# - Upload file Python via Files tab
# - Upload templates/ via Files tab
# - Upload service_account_credentials.json
```

### 2. Configura Web App

**Web tab → Add new web app:**
- Python version: 3.8+
- Framework: Flask
- WSGI file: `/home/yourusername/TanaLeague/tanaleague2/wsgi.py`

**Crea wsgi.py:**
```python
import sys
sys.path.insert(0, '/home/yourusername/TanaLeague/tanaleague2')

from app import app as application
```

### 3. Installa Dipendenze

```bash
pip install --user gspread google-auth pandas pdfplumber flask
```

### 4. Setup Achievement

```bash
cd ~/TanaLeague/tanaleague2
python setup_achievements.py
```

### 5. Reload

**Web tab → Reload button**

---

## 📚 Documentazione

| Documento | Descrizione |
|-----------|-------------|
| **[docs/NEW_STORE_SETUP.md](docs/NEW_STORE_SETUP.md)** | **START HERE!** Guida completa setup nuovo negozio |
| **[docs/SETUP.md](docs/SETUP.md)** | Guida installazione e configurazione |
| **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** | Guida sviluppo: test, logging, CI/CD |
| **[docs/IMPORT_GUIDE.md](docs/IMPORT_GUIDE.md)** | Come importare tornei da CSV/PDF/TDF |
| **[docs/ACHIEVEMENT_SYSTEM.md](docs/ACHIEVEMENT_SYSTEM.md)** | Sistema achievement in dettaglio |
| **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** | Cheatsheet comandi e operazioni comuni |
| **[docs/PYTHON_SCRIPTS.md](docs/PYTHON_SCRIPTS.md)** | Tutti gli script Python eseguibili |
| **[docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md)** | Guida operazioni admin webapp |
| **[docs/GOOGLE_SHEETS.md](docs/GOOGLE_SHEETS.md)** | Struttura database Google Sheets |
| **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** | Guida ai test automatici |
| **[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** | Migrazione server |
| **[docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** | Note tecniche |
| **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Risoluzione problemi |
| **[docs/FRANCHISE_GUIDE.md](docs/FRANCHISE_GUIDE.md)** | Guida modello franchise |

---

## 🏪 Franchise Model

TanaLeague supporta un modello franchise per distribuire il sistema ad altri negozi.

### Come Funziona

1. **Tu (Franchise Manager)**:
   - Gestisci UN Service Account Google
   - Crei pacchetti pre-configurati per ogni negozio
   - Ogni negozio ha il proprio Google Sheet separato

2. **I Negozi**:
   - Ricevono uno ZIP pre-configurato
   - Estraggono ed eseguono `install.bat` (Windows) o `install.sh` (Mac/Linux)
   - Doppio-click su `avvia.bat` per avviare
   - Nessuna configurazione tecnica richiesta!

### Creare un Pacchetto per un Nuovo Negozio

```bash
cd tanaleague2
python create_store_package.py
```

Lo script:
1. Chiede nome negozio, email, password admin
2. Crea automaticamente un Google Sheet
3. Inizializza tutti i fogli necessari
4. Genera un pacchetto ZIP pronto all'uso

### Contenuto del Pacchetto ZIP

```
TanaLeague_NomeNegozio/
├── tanaleague2/
│   ├── app.py
│   ├── config.py          # Pre-configurato!
│   ├── credentials.json   # Credenziali condivise
│   └── ...
├── install.bat            # Windows
├── avvia.bat              # Avvio Windows
└── LEGGIMI.txt            # Istruzioni
```

### Rate Limiting & Scalabilità

- **Limite API**: 300 req/min per progetto (condiviso tra tutti i negozi)
- **Retry automatico**: Il sistema gestisce automaticamente i rate limit
- **10 negozi**: Funziona senza problemi
- **50+ negozi**: Considera Service Account separati

Per dettagli completi: **[docs/FRANCHISE_GUIDE.md](docs/FRANCHISE_GUIDE.md)**

---

## 📁 Struttura Progetto

```
TanaLeague/
├── README.md                       # Questo file
├── requirements.txt                # Dipendenze Python
├── pytest.ini                      # Configurazione pytest
├── .gitignore                      # File esclusi da Git
├── install.bat                     # Script installazione Windows
├── install.sh                      # Script installazione Mac/Linux
│
├── .github/workflows/              # CI/CD
│   └── test.yml                    # GitHub Actions - test automatici
│
├── tests/                          # Test automatici
│   ├── conftest.py                 # Fixtures pytest
│   ├── test_app.py                 # Test routes
│   └── test_achievements.py        # Test achievement system
│
├── tanaleague2/                    # Codice principale
│   ├── app.py                      # Flask app + routes pubbliche
│   │
│   ├── routes/                     # Flask Blueprints (modular routes)
│   │   ├── __init__.py             # Blueprint registration
│   │   ├── admin.py                # Route admin (/admin/*)
│   │   └── achievements.py         # Route achievement (/achievements)
│   │
│   ├── cache.py                    # Cache manager Google Sheets
│   ├── config.py                   # Configurazione (NON in git!)
│   ├── config.example.py           # Template configurazione
│   ├── auth.py                     # Autenticazione admin
│   │
│   ├── achievements.py             # Logica unlock achievement
│   ├── setup_achievements.py       # Script setup sheets achievement
│   │
│   ├── import_base.py              # Funzioni comuni import
│   ├── import_onepiece.py          # Import One Piece Multi-Round
│   ├── import_riftbound.py         # Import Riftbound Multi-Round
│   ├── import_pokemon.py           # Import Pokémon (TDF/XML)
│   │
│   ├── sheet_utils.py              # Mappature colonne sheets
│   ├── player_stats.py             # CRUD Player_Stats sheet
│   ├── rebuild_player_stats.py     # Rebuild Player_Stats da Results
│   │
│   ├── stats_builder.py            # Builder statistiche avanzate
│   ├── stats_cache.py              # Cache file stats
│   │
│   ├── logger.py                   # Sistema logging strutturato
│   ├── backup_sheets.py            # Backup Google Sheets → CSV
│   │
│   ├── setup_wizard.py             # Setup interattivo
│   ├── init_database.py            # Inizializza fogli Google Sheet
│   ├── check_setup.py              # Verifica configurazione
│   ├── load_demo_data.py           # Carica dati demo
│   ├── create_store_package.py     # Crea pacchetti franchise (NEW!)
│   ├── api_utils.py                # Utility API con retry (NEW!)
│   │
│   ├── logs/                       # Log applicazione (auto-created)
│   │   └── tanaleague.log
│   │
│   ├── templates/                  # Template HTML Jinja2
│   │   ├── base.html               # Layout base + menu
│   │   ├── landing.html            # Homepage
│   │   ├── classifiche_page.html   # Lista classifiche
│   │   ├── classifica.html         # Classifica singola stagione
│   │   ├── player.html             # Profilo giocatore + grafici + achievement
│   │   ├── players.html            # Lista giocatori
│   │   ├── achievements.html       # Catalogo achievement (card cliccabili)
│   │   ├── achievement_detail.html # Dettaglio singolo achievement
│   │   ├── stats.html              # Stats avanzate
│   │   ├── admin/                  # Template admin panel
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   └── import_result.html
│   │   └── error.html              # Error page
│   │
│   └── static/                     # Assets statici
│       ├── style.css
│       └── logo.png
│
└── docs/                           # Documentazione
    ├── NEW_STORE_SETUP.md          # START HERE! Setup nuovo negozio
    ├── SETUP.md                    # Setup e installazione
    ├── DEVELOPMENT.md              # Guida sviluppo
    ├── IMPORT_GUIDE.md             # Guida import tornei
    ├── ACHIEVEMENT_SYSTEM.md       # Sistema achievement
    ├── QUICK_REFERENCE.md          # Cheatsheet comandi
    ├── PYTHON_SCRIPTS.md           # Script Python
    ├── ADMIN_GUIDE.md              # Operazioni admin
    ├── GOOGLE_SHEETS.md            # Struttura database
    ├── TESTING_GUIDE.md            # Test automatici
    ├── MIGRATION_GUIDE.md          # Migrazione server
    ├── TECHNICAL_NOTES.md          # Note tecniche
    └── TROUBLESHOOTING.md          # Risoluzione problemi
```

---

## 🔧 Manutenzione

### Backup Google Sheets

Il sistema crea backup automatici in `Backup_Log` sheet ogni import.

**Backup manuale:**
1. Google Sheets → File → Make a copy
2. Salva con data: `TanaLeague_Backup_2024-11-17`

### Cache Refresh

Cache si aggiorna automaticamente ogni 5 minuti.

**Refresh manuale:**
- Visita `/api/refresh` (classifiche)
- Visita `/api/stats/refresh/<scope>` (stats)

### Aggiungere Achievement

1. Apri `Achievement_Definitions` sheet
2. Aggiungi riga con: `achievement_id`, `name`, `description`, `category`, `rarity`, `emoji`, `points`, `requirement_type`, `requirement_value`
3. Modifica `achievements.py` per logica unlock (se `requirement_type=special`)

### Nuova Stagione

1. Apri `Config` sheet
2. Aggiungi riga: `season_id` (es. OP13), `tcg`, `name`, `season_num`, `status=ACTIVE`
3. Imposta vecchia stagione a `status=CLOSED`
4. (Opzionale) Vecchie stagioni → `status=ARCHIVED` per nasconderle

---

## 🛡️ Sicurezza

- **Service Account**: Credenziali Google in file separato (non in git!)
- **SHEET_ID**: Hardcoded negli script (cambia per deploy)
- **API Limits**: Google Sheets ha rate limits (100 req/100sec)
- **Cache**: Riduce chiamate API con cache 5 min
- **No SQL Injection**: Google Sheets non vulnerabile

---

## 📊 Statistiche Progetto

- **Linee di codice**: ~10,000+
- **File Python**: 12
- **Template HTML**: 16
- **Achievement**: 40
- **TCG Supportati**: 3
- **Stagioni Gestite**: 15+
- **Giocatori Attivi**: 50+
- **Tornei Totali**: 100+

---

## 🙏 Credits

- **Flask**: Web framework
- **Google Sheets API**: Database backend
- **Bootstrap 5**: Frontend framework
- **Font Awesome**: Icone
- **pandas**: Data manipulation
- **gspread**: Google Sheets Python client

---

## 📜 License

Progetto privato - Tutti i diritti riservati © 2024 La Tana delle Pulci

---

## 🤝 Supporto

**La Tana delle Pulci**
Viale Adamello 1, Lecco
Instagram: [@latanadellepulci](https://www.instagram.com/latanadellepulci/)

Per bug o feature request: Apri issue su GitHub

---

**Made with ❤️ for the TCG community**

*Last updated: November 2025 (v2.4 - Unified Import Architecture + Multi-Round CSV)*
