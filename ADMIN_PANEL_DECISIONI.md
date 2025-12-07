# LeagueForge - Admin Panel: Decisioni di Progettazione

> Documento di riferimento per lo sviluppo dell'Admin Panel.
> Creato: 2025-12-07
> Ultimo aggiornamento: 2025-12-07

---

## INDICE

1. [Contesto e Obiettivi](#1-contesto-e-obiettivi)
2. [Architettura Dati](#2-architettura-dati)
3. [Flusso Import](#3-flusso-import)
4. [Gestione Duplicati](#4-gestione-duplicati)
5. [Gestione Stagioni](#5-gestione-stagioni)
6. [UI Admin Panel](#6-ui-admin-panel)
7. [Gestione Errori e Recovery](#7-gestione-errori-e-recovery)
8. [Differenze tra TCG](#8-differenze-tra-tcg)
9. [Decisioni Tecniche](#9-decisioni-tecniche)
10. [File da Modificare](#10-file-da-modificare)
11. [Fasi di Implementazione](#11-fasi-di-implementazione)

---

## 1. CONTESTO E OBIETTIVI

### Cosa è LeagueForge
Web app Flask per gestire tornei TCG (Trading Card Games):
- One Piece (OP)
- Pokémon (PKM)
- Riftbound (RFB)

### Obiettivo Admin Panel
Permettere a utenti non tecnici (gestori di negozi) di:
- Importare file CSV/TDF dei tornei
- Gestire stagioni (creare, chiudere)
- Vedere preview prima di importare
- Ricevere feedback chiaro su errori

### Modello di Business
- SaaS multi-tenant (hosting su Render)
- 1 admin per negozio
- Utenti non tecnici

---

## 2. ARCHITETTURA DATI

### Fonte di Verità
**Results è l'UNICA fonte di verità.**

```
FILE UFFICIALI (CSV/TDF)
    │
    ├── Parsing + Validazione
    ├── Calcolo W/T/L e punti LeagueForge
    │
    ▼
RESULTS (1 riga = 1 giocatore in 1 torneo)
    │
    ├── Derivato → PLAYERS (aggregato lifetime, ricalcolato)
    ├── Derivato → STANDINGS (classifica stagione, ricalcolata)
    └── Derivato → PLAYER_STATS (aggregati pre-calcolati)
```

### Principio Chiave
Se Results è corretto, Players e Standings possono sempre essere ricalcolati.
Le funzioni `update_players()` e `update_seasonal_standings()` sono **idempotenti**.

### Google Sheets come Database
- Manteniamo Google Sheets (no migrazione a DB per ora)
- Rate limit: 60 req/min → gestito con delay 1.2s tra chiamate
- Nessuna transazione atomica → gestito con validazione preventiva

---

## 3. FLUSSO IMPORT

### Step-by-Step

```
STEP 1: SELEZIONE
├── Utente sceglie TCG (One Piece / Pokémon / Riftbound)
└── Utente sceglie Season (dropdown, ARCHIVED nascosto con checkbox)

STEP 2: UPLOAD FILE
├── OP: Slot ordinati R1, R2, R3... + Classifica Finale (obbligatoria)
├── PKM: Singolo file TDF
└── RFB: Slot ordinati R1, R2, R3...

STEP 3: VALIDAZIONE FILE (in memoria, 0 scritture API)
├── Formato file corretto?
├── Encoding UTF-8?
├── Colonne/tag obbligatori presenti?
├── Dati parsabili?
└── Per OP/RFB: ordine round coerente? (punti crescenti)

STEP 4: CALCOLO DATI (in memoria, 0 scritture API)
├── Parse completo
├── Calcolo W/T/L
├── Calcolo punti LeagueForge
└── Generazione tournament_id

STEP 5: CHECK DUPLICATI (1-2 chiamate API lettura)
├── Esiste già tournament_id?
└── Stessa data + >80% stessi giocatori? → BLOCCO

STEP 6: PREVIEW
├── Tabella con tutti i partecipanti
├── Statistiche: N giocatori, vincitore, data
└── Utente verifica e conferma

STEP 7: SCRITTURA (chiamate API)
├── SE sovrascrivi: Cancella vecchi dati PRIMA
├── Scrivi Tournaments
├── Scrivi Results
├── Scrivi Matches (PKM/RFB)
└── Progress bar + log testuale

STEP 8: AGGIORNAMENTO DERIVATI
├── update_players()
├── update_seasonal_standings()
├── batch_update_player_stats()
└── check_and_unlock_achievements() (solo se NON ARCHIVED)

STEP 9: RISULTATO
├── Successo: riepilogo
└── Fallimento parziale: messaggio + pulsante "Completa Import"
```

### Round Variabili
OP e RFB possono avere 3, 4, 5, 6+ round. L'utente decide quanti caricare.

### Ordine File Critico
Per OP e RFB, l'ordine dei round è FONDAMENTALE.
UI con slot numerati forza l'utente a caricare in ordine.
Validazione: punti max crescenti tra round.

---

## 4. GESTIONE DUPLICATI

### Rilevamento
1. **Stesso tournament_id** (season + data)
2. **Stessa data + >80% stessi giocatori** (probabilmente stesso torneo)

### Comportamento
- Duplicato rilevato → **BLOCCO**
- Opzioni: **Annulla** o **Sovrascrivi**
- ~~"Importa comunque"~~ → **ELIMINATO** (causerebbe dati duplicati)

### Sovrascrivi (Opzione C)
1. Validazione completa PRIMA di qualsiasi scrittura
2. Cancella dati vecchi
3. Scrivi dati nuovi
4. Se fallisce dopo cancellazione → messaggio chiaro + possibilità di riprovare

---

## 5. GESTIONE STAGIONI

### Stati

| Stato | Descrizione | Scarto 2 peggiori | Achievement |
|-------|-------------|-------------------|-------------|
| ACTIVE | Stagione in corso | NO | SÌ |
| CLOSED | Stagione terminata | SÌ (se ≥8 tornei) | SÌ |
| ARCHIVED | Dati storici | NO | NO |

### Flusso Stati
```
ACTIVE → CLOSED (manuale, con ricalcolo classifica)
```
Le stagioni NON diventano mai ARCHIVED automaticamente.

### Stagioni ARCHIVED
- Una sola per TCG: OP99, PKM99, RFB99
- Servono per importare dati storici
- Nascoste di default nell'UI, accessibili con checkbox
- Achievement NON si sbloccano

### Scarto 2 Peggiori Giornate
- Si applica SOLO quando stagione è CLOSED
- Si applica SOLO se stagione ha ≥8 tornei
- **NOTA:** Il codice attuale è SBAGLIATO (applica sempre). Da correggere.

### Formato ID Stagioni

| TCG | Formato | Esempio | Nome Automatico |
|-----|---------|---------|-----------------|
| One Piece | `OP{numero}` | OP12, OP13 | "One Piece - Stagione 13" |
| Riftbound | `RFB{numero}` | RFB01, RFB02 | "Riftbound - Stagione 2" |
| Pokémon | `PKM-{iniziali}{anno}` | PKM-FS25 | "Pokémon - Fiamme Spettrali 2025" |

### Creazione Stagione
- Utente sceglie TCG
- Per OP/RFB: sceglie numero (suggerito: ultimo + 1)
- Per PKM: scrive nome espansione, sistema estrae iniziali + anno
- Nome descrittivo generato automaticamente

### Chiusura Stagione
- Cambia status ACTIVE → CLOSED
- Ricalcola classifica con scarto 2 peggiori (se ≥8 tornei)
- Achievement restano sbloccati

---

## 6. UI ADMIN PANEL

### Import - Slot Ordinati (OP/RFB)

```
┌─────────────────────────────────────────────────────────────┐
│  IMPORT TORNEO ONE PIECE                                    │
├─────────────────────────────────────────────────────────────┤
│  📁 ROUND 1                          [Carica file]          │
│     └─ file1.csv                                            │
│        Preview: 12 giocatori, max 3 punti                   │
│                                                             │
│  📁 ROUND 2                          [Carica file]          │
│     └─ file2.csv                                            │
│        Preview: 12 giocatori, max 6 punti                   │
│                                                             │
│  📁 ROUND 3                          [Carica file]          │
│                                                             │
│  📁 CLASSIFICA FINALE (obbligatorio) [Carica file]          │
│                                                             │
│  [+ Aggiungi Round]                     [Valida e Continua] │
└─────────────────────────────────────────────────────────────┘
```

### Gestione Stagioni

```
┌─────────────────────────────────────────────────────────────┐
│  GESTIONE STAGIONI                                          │
├─────────────────────────────────────────────────────────────┤
│  ONE PIECE                                                  │
│  ├─ OP12 (ATTIVA)                    [Chiudi Stagione]     │
│  └─ OP11 (CHIUSA)                                          │
│                                                             │
│  [+ Crea Nuova Stagione]                                    │
└─────────────────────────────────────────────────────────────┘
```

### Progress durante Import

- Barra di avanzamento visiva
- Log testuale chiaro ("Scrittura Results... OK")
- Entrambi visibili contemporaneamente

---

## 7. GESTIONE ERRORI E RECOVERY

### Import Fallito a Metà
Se l'import fallisce dopo aver scritto Results ma prima di Players/Standings:

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  IMPORT NON COMPLETATO                                  │
├─────────────────────────────────────────────────────────────┤
│  I dati del torneo sono stati salvati, ma l'aggiornamento   │
│  delle classifiche non è andato a buon fine.                │
│                                                             │
│  Clicca "Completa" per finalizzare l'import.                │
│                                                             │
│  [Completa Import]                                          │
└─────────────────────────────────────────────────────────────┘
```

### Pulsante "Completa Import"
Esegue solo:
- `update_players()`
- `update_seasonal_standings()`
- `batch_update_player_stats()`

Queste funzioni sono idempotenti, quindi sicure da rieseguire.

---

## 8. DIFFERENZE TRA TCG

### One Piece (OP)
- **File:** N file round CSV + 1 ClassificaFinale CSV (obbligatoria)
- **Fonte:** Portale Bandai
- **W/T/L:** Calcolati dal delta punti tra round
- **Matches H2H:** NON disponibili (file non contengono questa info)
- **Vouchers:** SÌ (solo OP per ora)

### Pokémon (PKM)
- **File:** 1 file TDF (XML)
- **Fonte:** TOM (Tournament Operations Manager)
- **W/T/L:** Estratti direttamente dal TDF
- **Matches H2H:** SÌ (scritti in Pokemon_Matches)
- **Vouchers:** NO (per ora)

### Riftbound (RFB)
- **File:** N file round CSV
- **Fonte:** Carde.io
- **W/T/L:** Estratti da Event Record (W-L-D)
- **Matches H2H:** SÌ (scritti in Riftbound_Matches)
- **Vouchers:** NO (per ora)

---

## 9. DECISIONI TECNICHE

### Subprocess vs Chiamata Diretta
**DECISIONE:** ✅ Chiamata diretta + re-parse al confirm

**Motivazioni:**
- Preview possibile prima di scrivere
- Validazione separata dalla scrittura
- Controllo granulare step-by-step
- Progress bar reale
- Nessun overhead processo

**Gestione stato tra richieste:**
- File temp salvati all'upload
- Al confirm, ri-parsiamo (veloce, pochi secondi)
- Se file temp scaduti → messaggio "Ricarica i file"

### Analisi Timeout e Performance

**Scoperta importante:** Il codice usa batch write (`append_rows`).
70 giocatori = 70 righe scritte in 1 sola chiamata API, non 70 chiamate!

**Calcolo tempo import (70 giocatori):**

| Operazione | Chiamate API |
|------------|--------------|
| Letture iniziali | 4 |
| Scrittura Tournaments | 1 |
| Scrittura Results (batch) | 1 |
| Scrittura Matches | 1 |
| Update Players (batch) | 2 |
| Update Standings | 3 |
| Update Player_Stats (batch) | 2 |
| Check achievements | 3 |
| **TOTALE** | **~17 chiamate** |

Con delay 1.2s: **17 × 1.2s = ~20 secondi** ✅

**Timeout Render:**
- Default: 30 secondi
- Raccomandazione: Aumentare a 120 secondi per sicurezza
- Location: Render Dashboard → Service → Settings → Request Timeout

### Rinomina Seasonal_Standings_PROV
**DECISIONE:** Lasciamo stare per ora

---

## 10. FILE DA MODIFICARE

### Modifiche

| File | Tipo Modifica |
|------|---------------|
| `routes/admin.py` | Riscrittura quasi totale |
| `import_base.py` | Fix logica scarto (solo CLOSED) |
| `import_pokemon.py` | Fix logica scarto (solo CLOSED) |
| `import_onepiece.py` | Adattare per nuovo flusso |
| `import_riftbound.py` | Adattare per nuovo flusso |
| `import_validator.py` | Validazione ordine round, check 80% |
| `templates/admin/dashboard.html` | Riscrittura totale |
| `templates/admin/import_result.html` | Aggiungere "Completa Import" |

### Nuovi File

| File | Scopo |
|------|-------|
| `templates/admin/import_wizard.html` | UI wizard multi-step |
| `templates/admin/seasons.html` | Gestione stagioni |
| `templates/admin/import_preview.html` | Preview dati |
| `season_manager.py` | Logica stagioni |
| `import_controller.py` | Controller unificato import |

---

## 11. FASI DI IMPLEMENTAZIONE

```
FASE 1 - FIX CRITICI
├── Fix path sbagliato in admin.py (leagueforge2 → leagueforge)
└── Fix logica scarto (solo se CLOSED)

FASE 2 - REFACTORING IMPORT
├── Creare import_controller.py
├── Modificare import_*.py per chiamata diretta
└── Rimuovere dipendenza subprocess

FASE 3 - NUOVA UI IMPORT
├── Creare templates wizard/preview
├── Nuovo flusso in routes/admin.py
└── Validazione ordine round

FASE 4 - GESTIONE STAGIONI
├── Creare season_manager.py
├── UI gestione stagioni
└── Endpoint crea/chiudi

FASE 5 - POLISH
├── Progress bar + log real-time
├── Pulsante "Completa Import"
└── Test end-to-end
```

---

## FILE DI TEST DISPONIBILI

Nel branch `claude/setup-leagueforge-deploy-01An8xE6ZJPHfv7pwtg21Hyh`:

**Pokémon:**
- `novembre_2025_11_12.tdf`

**One Piece:**
- `OP_2025_11_13_R1.csv`
- `OP_2025_11_13_R2.csv`
- `OP_2025_11_13_R3.csv`
- `OP_2025_11_13_R4.csv`
- `OP_2025_11_13_ClassificaFinale.csv`

**Riftbound:**
- `RFB_2025_11_17_R1.csv`
- `RFB_2025_11_17_R2.csv`
- `RFB_2025_11_17_R3.csv`
- `RFB_2025_11_17_R4.csv`

---

## NOTE E CONSIDERAZIONI

### Limiti API Google Sheets
- 60 req/min per utente
- Import tipico (20 giocatori): ~10-12 chiamate
- Delay 1.2s tra chiamate già implementato

### Idempotenza
Le seguenti funzioni sono idempotenti (sicure da rieseguire):
- `update_players()` - ricalcola tutto da Results
- `update_seasonal_standings()` - ricalcola tutto da Results
- `batch_update_player_stats()` - ricalcola da dati

### Achievement
- Si sbloccano solo per stagioni NON ARCHIVED
- Restano sbloccati anche dopo chiusura stagione
- Check automatico durante import

---

*Documento da aggiornare man mano che vengono prese nuove decisioni.*
