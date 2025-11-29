# Guida Admin - LeagueForge

Guida completa per le operazioni di amministrazione della webapp.

---

## Indice

- [Accesso Admin](#-accesso-admin)
- [Dashboard Admin](#-dashboard-admin)
- [Import Tornei via Web](#-import-tornei-via-web)
- [Gestione Stagioni](#-gestione-stagioni)
- [Gestione Achievement](#-gestione-achievement)
- [Manutenzione](#-manutenzione)
- [Sicurezza](#-sicurezza)

---

## Accesso Admin

### URL Login

```
https://your-store.pythonanywhere.com/admin/login
```

Oppure in locale:
```
http://localhost:5000/admin/login
```

### Credenziali

Le credenziali sono configurate in `config.py`:

| Campo | Variabile config.py |
|-------|---------------------|
| Username | `ADMIN_USERNAME` |
| Password | Hash in `ADMIN_PASSWORD_HASH` |

### Sessione

- **Durata**: 30 minuti (configurabile in `SESSION_TIMEOUT`)
- **Scadenza**: Logout automatico dopo inattività
- **Logout manuale**: Click su "Esci" o vai a `/admin/logout`

### Cambiare Password Admin

1. Genera nuovo hash:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NUOVA_PASSWORD'))"
```

2. Copia l'output (inizia con `pbkdf2:`)

3. Modifica `config.py`:
```python
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:600000$..."  # Incolla qui
```

4. Reload webapp (su PythonAnywhere: tab Web → Reload)

---

## Dashboard Admin

### URL Dashboard

```
/admin/
```

### Funzionalita Disponibili

| Pulsante | Azione | Note |
|----------|--------|------|
| **Import One Piece** | Importa torneo OP da CSV | Richiede file CSV |
| **Import Pokemon** | Importa torneo PKM da TDF | Richiede file TDF |
| **Import Riftbound** | Importa torneo RFB da CSV | Supporta multi-round |
| **Esci** | Logout admin | Termina sessione |

### Navigazione

- **Navbar**: Accesso rapido a tutte le sezioni webapp
- **Breadcrumb**: Mostra posizione corrente
- **Footer**: Link utili e info versione

---

## Import Tornei via Web

### Procedura Generale

1. Login come admin (`/admin/login`)
2. Vai alla dashboard (`/admin/`)
3. Click sul pulsante import del TCG desiderato
4. Compila il form:
   - **File**: Seleziona CSV/TDF dal tuo PC
   - **Stagione**: Seleziona dal dropdown (es. OP12, PKM-FS25)
5. Click "Importa"
6. Attendi completamento
7. Verifica risultato

### Import One Piece (CSV)

**Form Fields:**
- File CSV: Export da Limitlesstcg
- Stagione: Dropdown stagioni OP attive

**Requisiti File:**
- Formato: CSV con header
- Colonne: Ranking, User Name, Membership Number, Win Points, OMW %, Record
- Nome file: Deve contenere data (es. `2025_11_23_OP12.csv`)

**Risultato:**
- Torneo aggiunto a Tournaments
- Risultati in Results
- Stats giocatori aggiornate in Players
- Classifica stagionale aggiornata
- Achievement sbloccati automaticamente

### Import Pokemon (TDF)

**Form Fields:**
- File TDF: Export da Play! Pokemon
- Stagione: Dropdown stagioni PKM attive

**Requisiti File:**
- Formato: TDF (XML interno)
- Contenuto: Standings, player info, match results

**Risultato:**
- Torneo aggiunto a Tournaments
- Risultati in Results
- Match H2H in Pokemon_Matches (se disponibili)
- Stats giocatori aggiornate
- Achievement sbloccati

### Import Riftbound (CSV)

**Form Fields:**
- File CSV: Uno o piu file (separati da virgola per multi-round)
- Stagione: Dropdown stagioni RFB attive

**Requisiti File:**
- Formato: CSV multi-round
- Colonne: User ID, First Name, Last Name, Event Record
- Multi-round: R1.csv, R2.csv, R3.csv

**Risultato:**
- Torneo aggregato da tutti i round
- Stats W-L-D dettagliate
- Achievement sbloccati

### Gestione Errori Import

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| "File non valido" | Formato errato | Verifica formato CSV/TDF |
| "Stagione non trovata" | Season ID non esiste | Crea stagione in Config sheet |
| "Torneo gia importato" | Stesso Tournament ID | Usa --reimport da CLI |
| "Errore Google Sheets" | API limit o connessione | Attendi e riprova |

### Note Import

- **Test Mode**: Non disponibile via web, usa CLI per dry-run
- **Reimport**: Non disponibile via web, usa CLI con `--reimport`
- **Progress**: La pagina mostra risultato al completamento
- **Timeout**: Import grandi potrebbero richiedere tempo

---

## Gestione Stagioni

### Dove Configurare

Le stagioni sono definite nel foglio `Config` del Google Sheet.

### Campi Stagione

| Campo | Descrizione | Esempio |
|-------|-------------|---------|
| `Season_ID` | Identificatore unico | OP12, PKM-FS25, RFB01 |
| `TCG` | Gioco di riferimento | onepiece, pokemon, riftbound |
| `Name` | Nome visualizzato | "Stagione 12", "Fall Season 2025" |
| `Status` | Stato stagione | ACTIVE, CLOSED, ARCHIVED |
| `Start_Date` | Data inizio | 2025-01-01 |
| `End_Date` | Data fine | 2025-06-30 |
| `Entry_Fee` | Quota iscrizione | 5 |
| `Pack_Cost` | Costo busta | 4 |

### Stati Stagione

| Stato | Visibile | Import | Achievement | Scarto Tornei |
|-------|----------|--------|-------------|---------------|
| **ACTIVE** | Si | Si | Si | Si (se >= 8 tornei) |
| **CLOSED** | Si | Si | Si | Si |
| **ARCHIVED** | No | Si | No | No |

### Creare Nuova Stagione

1. Apri Google Sheet
2. Vai al foglio `Config`
3. Aggiungi nuova riga con dati stagione
4. Reload webapp (cache si aggiorna in 5 min)

### Archiviare Stagione

1. Apri Google Sheet → foglio `Config`
2. Trova riga della stagione
3. Cambia Status da "ACTIVE" o "CLOSED" a "ARCHIVED"
4. La stagione sparisce dai dropdown ma i dati restano

---

## Gestione Achievement

### Visualizzare Achievement

- **Catalogo**: `/achievements`
- **Dettaglio**: `/achievement/<id>` (es. `/achievement/ACH_GLO_001`)

### Come Funziona Unlock

1. Durante import torneo, il sistema controlla tutti i giocatori
2. Per ogni achievement, verifica se requisiti sono soddisfatti
3. Se si, aggiunge record in `Player_Achievements`
4. Il profilo giocatore mostra achievement sbloccati

### Achievement NON si Sbloccano?

1. Verifica che stagione non sia ARCHIVED
2. Controlla che foglio `Achievement_Definitions` esista
3. Controlla che foglio `Player_Achievements` esista
4. Se mancano, esegui: `python setup_achievements.py`

### Aggiungere Nuovo Achievement

1. Apri Google Sheet → `Achievement_Definitions`
2. Aggiungi nuova riga con:
   - `achievement_id`: ID unico (es. ACH_NEW_001)
   - `name`: Nome visualizzato
   - `description`: Descrizione
   - `category`: Categoria (Glory, Legacy, etc.)
   - `rarity`: Rarita (Common, Uncommon, Rare, Epic, Legendary)
   - `emoji`: Emoji rappresentativa
   - `points`: Punti achievement
   - `requirement_type`: Tipo requisito
   - `requirement_value`: Valore requisito

### Rimuovere Achievement Sbloccato

1. Apri Google Sheet → `Player_Achievements`
2. Trova riga con membership_number e achievement_id
3. Elimina la riga
4. Il profilo giocatore si aggiorna automaticamente

---

## Manutenzione

### Refresh Cache

La cache si aggiorna automaticamente ogni 5 minuti.

**Forzare refresh:**
1. Reload webapp (PythonAnywhere: Web → Reload)
2. Oppure attendi 5 minuti

### Backup Manuale

```bash
cd leagueforge2
python backup_sheets.py
```

I file vengono salvati in `backups/YYYY-MM-DD_HH-MM-SS/`

### Controllare Logs

**PythonAnywhere:**
1. Tab Web → Error log
2. Tab Web → Server log
3. Files → `leagueforge2/logs/leagueforge.log`

**Locale:**
```bash
cat leagueforge2/logs/leagueforge.log
```

### Verificare Stato App

Testa queste URL:

| URL | Risposta Attesa |
|-----|-----------------|
| `/` | Homepage (200 OK) |
| `/classifiche` | Lista stagioni |
| `/achievements` | Catalogo achievement |
| `/admin/login` | Form login |

### Aggiornare Codice

**PythonAnywhere:**
```bash
cd ~/LeagueForge
git pull origin main
# Tab Web → Reload
```

**Locale:**
```bash
cd LeagueForge
git pull origin main
python leagueforge2/app.py
```

---

## Sicurezza

### Best Practices

1. **Password forte**: Usa password complessa per admin
2. **HTTPS**: Sempre usa HTTPS in produzione
3. **Config.py**: MAI committare su Git (e in .gitignore)
4. **Credentials.json**: MAI committare su Git
5. **Sessione**: Fai logout dopo uso admin
6. **Backup**: Backup regolari del Google Sheet

### File Sensibili

| File | Contiene | Protezione |
|------|----------|------------|
| `config.py` | Password hash, secret key | .gitignore |
| `service_account_credentials.json` | Credenziali Google | .gitignore |
| `cache_data.json` | Dati cached | .gitignore |

### Recupero Accesso

Se perdi accesso admin:

1. Accedi a PythonAnywhere (o server)
2. Modifica `config.py` con nuovo hash password
3. Reload webapp

### Rotazione Credenziali

Consigliato ogni 6 mesi:

1. Genera nuova SECRET_KEY
2. Genera nuovo ADMIN_PASSWORD_HASH
3. Aggiorna config.py
4. Reload webapp
5. Ri-effettua login

---

## Checklist Operazioni Comuni

### Import Torneo Settimanale

- [ ] Login admin
- [ ] Scarica file risultati (CSV/TDF)
- [ ] Verifica nome file contiene data
- [ ] Import via dashboard o CLI
- [ ] Verifica classifica aggiornata
- [ ] Verifica achievement sbloccati
- [ ] Logout

### Inizio Nuova Stagione

- [ ] Backup stagione precedente
- [ ] Cambia status vecchia stagione in CLOSED
- [ ] Crea nuova stagione in Config
- [ ] Verifica dropdown mostra nuova stagione
- [ ] Test import primo torneo

### Fine Stagione

- [ ] Backup completo
- [ ] Cambia status in CLOSED (o ARCHIVED se storico)
- [ ] Verifica classifica finale corretta
- [ ] Screenshot/export per archivio

---

**Ultimo aggiornamento:** Novembre 2025
