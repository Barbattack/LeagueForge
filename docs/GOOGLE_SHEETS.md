# Struttura Google Sheets - LeagueForge

Guida completa alla struttura del database Google Sheets.

---

## Indice

- [Panoramica](#-panoramica)
- [Config](#-config)
- [Tournaments](#-tournaments)
- [Results](#-results)
- [Players](#-players)
- [Player_Stats](#-player_stats)
- [Seasonal Standings](#-seasonal-standings)
- [Achievement System](#-achievement-system)
- [Altri Fogli](#-altri-fogli)
- [Relazioni tra Fogli](#-relazioni-tra-fogli)

---

## Panoramica

Il database LeagueForge usa un singolo Google Sheet con piu fogli (worksheets).

### Lista Fogli

| Foglio | Scopo | Popolato da |
|--------|-------|-------------|
| Config | Configurazione stagioni | Manuale |
| Tournaments | Lista tornei | Import script |
| Results | Risultati giocatori | Import script |
| Players | Anagrafica giocatori | Import script |
| Player_Stats | Statistiche aggregate (CQRS) | Import script + rebuild_player_stats.py |
| Seasonal_Standings_PROV | Classifiche provvisorie | Import script |
| Seasonal_Standings_FINAL | Classifiche finali | Manuale/Script |
| Achievement_Definitions | Definizioni achievement | setup_achievements.py |
| Player_Achievements | Achievement sbloccati | Import script |
| Pokemon_Matches | Match H2H Pokemon | import_pokemon.py |
| Vouchers | Buoni negozio OP | import_onepiece.py |
| Backup_Log | Log backup | import scripts |

---

## Config

Configurazione delle stagioni per ogni TCG.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Season_ID | String | ID univoco stagione | OP12, PKM-FS25, RFB01 |
| TCG | String | Gioco (onepiece/pokemon/riftbound) | onepiece |
| Name | String | Nome visualizzato | "Stagione 12" |
| Status | String | Stato (ACTIVE/CLOSED/ARCHIVED) | ACTIVE |
| Start_Date | Date | Data inizio | 2025-01-01 |
| End_Date | Date | Data fine | 2025-06-30 |
| Entry_Fee | Number | Quota iscrizione (EUR) | 5 |
| Pack_Cost | Number | Costo busta (EUR) | 4 |
| Min_Players | Number | Minimo giocatori | 4 |
| Max_Tournaments | Number | Max tornei stagione | 20 |

### Esempio Righe

```
Season_ID | TCG      | Name              | Status  | Start_Date | End_Date   | Entry_Fee | Pack_Cost
----------|----------|-------------------|---------|------------|------------|-----------|----------
OP12      | onepiece | Stagione 12       | ACTIVE  | 2025-01-01 | 2025-06-30 | 5         | 4
PKM-FS25  | pokemon  | Fall Season 2025  | ACTIVE  | 2025-09-01 | 2025-12-31 | 5         | 4
RFB01     | riftbound| Prima Stagione    | ACTIVE  | 2025-01-01 | 2025-12-31 | 5         | 4
OP11      | onepiece | Stagione 11       | ARCHIVED| 2024-07-01 | 2024-12-31 | 5         | 4
```

### Stati Stagione

| Stato | Descrizione | Visibile UI | Import OK | Achievement |
|-------|-------------|-------------|-----------|-------------|
| ACTIVE | Stagione in corso | Si | Si | Si |
| CLOSED | Stagione conclusa | Si | Si | Si |
| ARCHIVED | Archivio storico | No | Si | No |

---

## Tournaments

Lista di tutti i tornei importati.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Tournament_ID | String | ID univoco (Season_Date) | OP12_2025-06-12 |
| Season_ID | String | Riferimento a Config | OP12 |
| Date | Date | Data torneo | 2025-06-12 |
| Participants | Number | Numero partecipanti | 16 |
| Rounds | Number | Numero round | 4 |
| Winner | String | Nome vincitore | Pietro Cogliati |
| Winner_Membership | String | ID vincitore | 0000012345 |
| TCG | String | Gioco | onepiece |
| Import_Date | DateTime | Data/ora import | 2025-06-12 18:30:00 |

### Chiave Primaria

`Tournament_ID` = `{Season_ID}_{Date}`

Esempio: `OP12_2025-06-12`

---

## Results

Risultati individuali di ogni giocatore in ogni torneo.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Tournament_ID | String | Riferimento torneo | OP12_2025-06-12 |
| Membership_Number | String | ID giocatore | 0000012345 |
| Player_Name | String | Nome giocatore | Pietro Cogliati |
| Ranking | Number | Posizione finale | 1 |
| Record | String | W-L o W-T-L | 4-0, 3-0-1 |
| Win_Points | Number | Punti vittoria (W*3+T*1) | 12 |
| OMW | Number | Opponent Match Win % | 65.5 |
| Points_Victory | Number | Punti LeagueForge (vittorie) | 4 |
| Points_Ranking | Number | Punti LeagueForge (posizione) | 16 |
| Points_Total | Number | Totale punti LeagueForge | 20 |
| Match_W | Number | Vittorie match | 4 |
| Match_T | Number | Pareggi match | 0 |
| Match_L | Number | Sconfitte match | 0 |

### Chiave Primaria Composta

`Tournament_ID` + `Membership_Number`

### Note

- **One Piece**: Match_T sempre 0 (no pareggi)
- **Pokemon/Riftbound**: Match_T puo essere > 0
- **Points_Victory**: Numero di vittorie (W), NON win_points

---

## Players

Anagrafica giocatori con statistiche lifetime.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Membership_Number | String | ID univoco giocatore | 0000012345 |
| Player_Name | String | Nome completo | Pietro Cogliati |
| TCG | String | Gioco principale | onepiece |
| First_Seen | Date | Prima partecipazione | 2024-01-15 |
| Last_Seen | Date | Ultima partecipazione | 2025-06-12 |
| Total_Tournaments | Number | Tornei totali | 25 |
| Tournament_Wins | Number | Vittorie tornei (1° posto) | 5 |
| Match_W | Number | Vittorie match lifetime | 82 |
| Match_T | Number | Pareggi match lifetime | 3 |
| Match_L | Number | Sconfitte match lifetime | 15 |
| Total_Points | Number | Punti LeagueForge totali | 450 |

### Chiave Primaria

`Membership_Number`

### Aggiornamento

Le stats vengono aggiornate automaticamente ad ogni import torneo.

---

## Seasonal Standings

Classifiche stagionali. Due fogli: PROV (provvisorie) e FINAL (finali).

### Seasonal_Standings_PROV

Classifiche delle stagioni ACTIVE, aggiornate ad ogni import.

### Seasonal_Standings_FINAL

Classifiche delle stagioni CLOSED, copiate manualmente a fine stagione.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Season_ID | String | Riferimento stagione | OP12 |
| Rank | Number | Posizione classifica | 1 |
| Membership_Number | String | ID giocatore | 0000012345 |
| Player_Name | String | Nome giocatore | Pietro Cogliati |
| Tournaments_Played | Number | Tornei disputati | 8 |
| Best_Results | String | Migliori risultati considerati | "1,2,1,3,2,1" |
| Total_Points | Number | Punti totali (con scarto) | 125 |
| Avg_Points | Number | Punti medi per torneo | 15.6 |

### Regola Scarto

Se stagione ha >= 8 tornei giocati da un giocatore:
- Vengono contati solo i **migliori N-2 tornei**
- Esempio: 10 tornei → contano i migliori 8

Se stagione ARCHIVED:
- **Nessuno scarto** (tutti i tornei contano)

---

## Player_Stats

Statistiche aggregate pre-calcolate per ogni giocatore (CQRS read model).

### Descrizione

**Player_Stats** è un foglio di aggregazione che contiene statistiche lifetime calcolate da tutti i tornei nel foglio **Results**. Segue il pattern CQRS (Command Query Responsibility Segregation):
- **Write side**: Foglio Results (append-only durante import)
- **Read side**: Foglio Player_Stats (materializzato, per query veloci)

Viene utilizzato dalla route `/players` della webapp per mostrare le card dei giocatori senza duplicati.

### Colonne

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| Membership | String | ID univoco giocatore | 0000012345 |
| Name | String | Nome completo | Pietro Cogliati |
| TCG | String | TCG principale (con più tornei) | OP |
| Total Tournaments | Number | Tornei totali lifetime | 25 |
| Total Wins | Number | Vittorie tornei (1° posto) | 5 |
| Current Streak | Number | Top8 consecutivi attuali | 3 |
| Best Streak | Number | Miglior serie Top8 consecutivi | 7 |
| Top8 Count | Number | Totale piazzamenti Top8 | 18 |
| Last Rank | Number | Posizione ultimo torneo | 2 |
| Last Date | Date | Data ultimo torneo | 2025-11-23 |
| Seasons Count | Number | Stagioni diverse giocate | 4 |
| Updated At | DateTime | Ultimo aggiornamento | 2025-11-23 14:30 |
| Total Points | Number | Punti LeagueForge totali lifetime | 450.0 |

### Chiave Primaria Composta

`Membership` + `TCG`

Un giocatore può avere più righe se gioca a TCG diversi (es. OP e PKM).

### Aggiornamento

**Incrementale (automatico):**
- Durante import tornei tramite `batch_update_player_stats()` in `import_base.py`
- Aggiorna stats del singolo giocatore dopo ogni torneo

**Completo (manuale):**
```bash
cd leagueforge2
python rebuild_player_stats.py
```

Ricostruisce l'intero foglio da zero leggendo tutti i Results.

### Inclusione Stagioni ARCHIVED

**IMPORTANTE:** Player_Stats include TUTTI i tornei storici, incluse le stagioni ARCHIVED.

- **Stagioni ACTIVE/CLOSED**: Contano per achievement e classifiche competitive
- **Stagioni ARCHIVED**: Contano SOLO per stats lifetime personali (Total Tournaments, Total Points, ecc.)

Esempio: Un giocatore con 10 tornei in PKM99 (ARCHIVED) + 5 in PKM-FS25 (ACTIVE) avrà:
- `Total Tournaments = 15` (include ARCHIVED)
- `Total Points = somma di tutti i 15 tornei` (include ARCHIVED)

### Utilizzo nella Webapp

Route `/players` (app.py):
1. Legge Player_Stats invece di Players
2. Valida header colonne con `validate_sheet_headers()`
3. Mostra una card per membership number (no duplicati)
4. Calcola punti medi: `avg_points = total_points / total_tournaments`

### Validazione Header

A partire da Novembre 2025, la webapp valida automaticamente la struttura del foglio:
```python
from sheet_utils import validate_sheet_headers, COL_PLAYER_STATS

validation = validate_sheet_headers(ws_stats, COL_PLAYER_STATS, expected_headers)
if not validation['valid']:
    # Mostra errore chiaro all'utente
```

Questo previene crash se qualcuno sposta accidentalmente una colonna.

### Note Tecniche

- **Ordine colonne fisso**: Le colonne DEVONO essere nell'ordine specificato (indici hardcoded)
- **Header row**: Riga 3 del foglio (index 2)
- **Skip rows**: Le prime 3 righe (0-2) sono intestazioni/descrizioni
- **Performance**: Query molto più veloci rispetto a calcolare da Results ogni volta

---

## Achievement System

Due fogli per il sistema achievement.

### Achievement_Definitions

Definizioni dei 40+ achievement disponibili.

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| achievement_id | String | ID univoco | ACH_GLO_001 |
| name | String | Nome achievement | First Blood |
| description | String | Descrizione | Vinci il tuo primo torneo |
| category | String | Categoria | Glory |
| rarity | String | Rarita | Uncommon |
| emoji | String | Emoji | :trophy: |
| points | Number | Punti | 25 |
| requirement_type | String | Tipo requisito | tournament_wins |
| requirement_value | Mixed | Valore requisito | 1 |

### Categorie Achievement

| Categoria | Descrizione | Esempi |
|-----------|-------------|--------|
| Glory | Vittorie e trionfi | First Blood, Dynasty Builder |
| Giant Slayer | Battere avversari forti | Top Slayer, Giant Killer |
| Consistency | Costanza e presenza | Regular, Iron Man |
| Legacy | Traguardi storici | Veteran, Legend |
| Wildcards | Achievement speciali | Lucky 7, Collector |
| Seasonal | Stagionali | Season Champion |
| Heartbreak | "Sconfitte epiche" | Almost, Bridesmaid |

### Rarita

| Rarita | Punti | Difficolta |
|--------|-------|------------|
| Common | 10 | Facile |
| Uncommon | 25 | Normale |
| Rare | 50 | Difficile |
| Epic | 100 | Molto difficile |
| Legendary | 250 | Eccezionale |

### Player_Achievements

Achievement sbloccati dai giocatori.

| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| membership_number | String | ID giocatore | 0000012345 |
| achievement_id | String | ID achievement | ACH_GLO_001 |
| unlocked_at | DateTime | Data sblocco | 2025-06-12 18:30:00 |
| tournament_id | String | Torneo che ha sbloccato | OP12_2025-06-12 |
| season_id | String | Stagione | OP12 |

### Chiave Primaria Composta

`membership_number` + `achievement_id`

(Un giocatore non puo avere lo stesso achievement due volte)

---

## Altri Fogli

### Pokemon_Matches

Match Head-to-Head per tornei Pokemon.

| Colonna | Descrizione |
|---------|-------------|
| Tournament_ID | ID torneo |
| Round | Numero round |
| Table | Numero tavolo |
| Player1_Membership | ID giocatore 1 |
| Player1_Name | Nome giocatore 1 |
| Player2_Membership | ID giocatore 2 |
| Player2_Name | Nome giocatore 2 |
| Winner | 1, 2, o TIE |
| Outcome | Risultato (W/L/T) |

### Vouchers

Buoni negozio per tornei One Piece.

| Colonna | Descrizione |
|---------|-------------|
| Tournament_ID | ID torneo |
| Membership_Number | ID giocatore |
| Player_Name | Nome giocatore |
| Ranking | Posizione finale |
| Category | X-0, X-1, Altri |
| Voucher_Amount | Importo buono (EUR) |

### Backup_Log

Log dei backup e import.

| Colonna | Descrizione |
|---------|-------------|
| Timestamp | Data/ora operazione |
| Operation | Tipo (import, backup, delete) |
| Tournament_ID | Torneo interessato |
| Status | Risultato (success, error) |
| Details | Dettagli aggiuntivi |

---

## Relazioni tra Fogli

```
Config (Stagioni)
    │
    ├─── Tournaments (1:N)
    │         │
    │         ├─── Results (1:N per torneo)
    │         │
    │         ├─── Pokemon_Matches (1:N per torneo Pokemon)
    │         │
    │         └─── Vouchers (1:N per torneo One Piece)
    │
    └─── Seasonal_Standings (1:N per stagione)


Players (Giocatori)
    │
    ├─── Results (1:N - un giocatore ha molti risultati)
    │
    └─── Player_Achievements (1:N - un giocatore ha molti achievement)


Achievement_Definitions
    │
    └─── Player_Achievements (1:N - un achievement puo essere di molti giocatori)
```

### Chiavi di Relazione

| Da | A | Chiave |
|----|---|--------|
| Tournaments → Config | Season_ID | Season_ID |
| Results → Tournaments | Tournament_ID | Tournament_ID |
| Results → Players | Membership_Number | Membership_Number |
| Player_Achievements → Players | membership_number | Membership_Number |
| Player_Achievements → Achievement_Definitions | achievement_id | achievement_id |
| Seasonal_Standings → Config | Season_ID | Season_ID |
| Seasonal_Standings → Players | Membership_Number | Membership_Number |

---

## Best Practices

### Modifiche Manuali

1. **Sempre fare backup** prima di modificare manualmente
2. **Non modificare Tournament_ID** dopo l'import
3. **Non modificare Membership_Number** (chiave di relazione)
4. **Usare import scripts** quando possibile invece di modifica manuale

### Accesso Foglio

- **Service Account**: Ha accesso in lettura/scrittura via API
- **Utenti Google**: Possono avere accesso via condivisione
- **Backup regolari**: Consigliati settimanali

### Limiti Google Sheets

| Limite | Valore |
|--------|--------|
| Celle per foglio | 10 milioni |
| Colonne | 18.278 (A-ZZZ) |
| Righe | ~5 milioni |
| API requests | 60/min per utente |

Per progetti grandi, considera migrazione a database reale (PostgreSQL, MongoDB).

---

**Ultimo aggiornamento:** Novembre 2025
