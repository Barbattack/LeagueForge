# LeagueForge - TODO List

Lista delle migliorie e task da completare per rendere il sistema più robusto e vendibile.

---

## 🔴 PRIORITÀ ALTA

### 1. Mapping dinamico delle colonne Google Sheets
**Problema:** Attualmente i mapping delle colonne sono hardcoded (indici 0, 1, 2...). Se qualcuno sposta una colonna nello sheet, tutto si rompe.

**Soluzione:** Implementare sistema di mapping dinamico che legge gli header dai Google Sheets e costruisce i mapping al volo.

**Impatto:**
- File da modificare: `sheet_utils.py`, `app.py`, `import_base.py`, `player_stats.py`, `rebuild_player_stats.py`, e tutti gli altri che usano COL_* mappings
- Rischio: MEDIO-ALTO (refactoring grande)
- Beneficio: Robustezza per negozianti non tecnici

**Requisiti testing:**
- Import di un torneo (tutte e 3 le tipologie: OP, PKM, RB)
- Rebuild player stats
- Tutte le pagine webapp
- Achievement system
- Classifiche stagionali

**Note:** Performance - serve caching intelligente per non leggere header ad ogni chiamata

**Status:** 🟡 DA FARE

---

## 🟢 PRIORITÀ MEDIA

_(Aggiungi qui future task)_

---

## ⚪ PRIORITÀ BASSA / NICE TO HAVE

_(Aggiungi qui future nice-to-have)_

---

## ✅ COMPLETATI

### Fix duplicate player cards
- ✅ Problema: Giocatori con stesso membership ma TCG diversi (es. PKM e PKMFS) apparivano come schede duplicate
- ✅ Soluzione: /players ora legge da Player_Stats con colonna total_points
- ✅ Completato: 2025-11-27

### Fix ARCHIVED seasons escluse da Player_Stats
- ✅ Problema: rebuild_player_stats.py escludeva stagioni ARCHIVED, quindi stats lifetime incomplete
- ✅ Soluzione: Rimosso filtro ARCHIVED - ora include TUTTI i tornei storici
- ✅ File modificato: `leagueforge2/rebuild_player_stats.py`
- ✅ Completato: 2025-11-28

### Validazione header Google Sheets (Opzione B)
- ✅ Problema: Colonne hardcoded - se qualcuno sposta una colonna tutto si rompe
- ✅ Soluzione: Aggiunta funzione `validate_sheet_headers()` in sheet_utils.py
- ✅ La funzione valida ordine e nomi colonne prima di operazioni critiche
- ✅ Implementata in: route /players di app.py
- ✅ File modificati: `leagueforge2/sheet_utils.py`, `leagueforge2/app.py`
- ✅ Completato: 2025-11-28
- ⚠️ NOTA: Questa è una soluzione temporanea. Per robustezza completa serve Opzione A (mapping dinamico) - vedi TODO priorità alta

---

**Last Updated:** 2025-11-28
