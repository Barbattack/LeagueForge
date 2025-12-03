# Guida Admin - LeagueForge

Guida completa per le operazioni di amministrazione della webapp.

---

## Indice

- [Admin Panel Web](#-admin-panel-web)
- [Import Tornei](#-import-tornei)
- [Gestione Stagioni](#-gestione-stagioni)
- [Gestione Achievement](#-gestione-achievement)
- [Manutenzione](#-manutenzione)
- [Sicurezza](#-sicurezza)

---

## 🚧 Admin Panel Web

**Status:** In fase di re-development

Il precedente admin panel web (`/admin/login`, `/admin/dashboard`) è stato rimosso ed è in fase di completa ricostruzione con nuovo design e funzionalità migliorate.

### Funzionalità in Arrivo

- Login admin con sessione sicura
- Dashboard con overview statistiche
- Import tornei via web UI (CSV, TDF, PDF)
- Gestione stagioni
- Configurazione negozio (logo, info contatto, branding)
- Sistema di notifiche e logs

### Nel Frattempo

Per operazioni admin, usa:
- **Import tornei**: Script Python CLI (vedi sezione Import Tornei)
- **Gestione stagioni**: Google Sheets (vedi sezione Gestione Stagioni)
- **Gestione achievement**: Google Sheets (vedi sezione Gestione Achievement)

---

## 📥 Import Tornei

### Metodo CLI (Script Python)

Gli script Python per import tornei sono ancora completamente funzionanti:

**One Piece TCG:**
```bash
cd leagueforge2
python import_onepiece.py --csv path/to/YYYY_MM_DD_OP12.csv --season OP12
```

**Pokemon TCG:**
```bash
python import_pokemon.py --tdf path/to/tournament.tdf --season PKM-FS25
```

**Riftbound TCG:**
```bash
python import_riftbound.py --csv path/to/tournament.csv --season RFB01
```

### Opzioni Comuni

| Flag | Descrizione |
|------|-------------|
| `--test` | Test mode (dry run, non scrive) |
| `--verbose` | Output dettagliato |
| `--help` | Mostra aiuto completo |

### Documentazione Dettagliata

Vedi `docs/IMPORT_GUIDE.md` per istruzioni complete su formati file, troubleshooting e procedure dettagliate.

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

1. **Password forte**: Usa password complessa per admin (quando sarà disponibile)
2. **HTTPS**: Sempre usa HTTPS in produzione
3. **Config.py**: MAI committare su Git (e in .gitignore)
4. **Credentials.json**: MAI committare su Git
5. **Backup**: Backup regolari del Google Sheet

### File Sensibili

| File | Contiene | Protezione |
|------|----------|------------|
| `config.py` | Password hash, secret key | .gitignore |
| `service_account_credentials.json` | Credenziali Google | .gitignore |
| `cache_data.json` | Dati cached | .gitignore |

### Rotazione Credenziali

Consigliato ogni 6 mesi:

1. Genera nuova SECRET_KEY
2. Aggiorna config.py
3. Reload webapp

---

## Checklist Operazioni Comuni

### Import Torneo Settimanale

- [ ] Scarica file risultati (CSV/TDF)
- [ ] Verifica nome file contiene data
- [ ] Import via script CLI
- [ ] Verifica classifica aggiornata
- [ ] Verifica achievement sbloccati

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

**Ultimo aggiornamento:** Dicembre 2024
