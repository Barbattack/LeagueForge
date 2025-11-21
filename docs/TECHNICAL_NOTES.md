# 🔧 Technical Notes - TanaLeague

**Note tecniche di implementazione per sviluppatori**

Questo documento contiene dettagli tecnici implementativi per la manutenzione e l'estensione del sistema TanaLeague. Per guide utente, vedere [IMPORT_GUIDE.md](IMPORT_GUIDE.md) e [SETUP.md](SETUP.md).

---

## 📋 Indice

1. [Pokemon TCG](#pokemon-tcg)
2. [One Piece TCG](#one-piece-tcg)
3. [Riftbound TCG](#riftbound-tcg)

---

## 🎴 Pokemon TCG

### Formato Input: TDF/XML

File `.tdf` sono XML con struttura:
```xml
<tournament>
  <players>
    <player id="123" name="Rossi, Mario" />
  </players>
  <rounds>
    <round number="1">
      <pairing player1="123" player2="456" result="W" />
    </round>
  </rounds>
</tournament>
```

### Sistema Punti con Pareggi

**Match Points nel PDF:**
```python
win_points = W * 3 + T * 1 + L * 0
```

**IMPORTANTE:** Il campo `Points_Victory` in Results è diverso:
```python
# Nel foglio Results, colonna 7 (Pts_Victory)
points_victory = W  # NON win_points/3!
```

Questo è intenzionale per compatibilità storica con il sistema Pokémon.

### BYE Handling

```python
if result == "BYE":
    # Conta come vittoria automatica
    match_w += 1
    win_points += 3
```

### Multi-Round Aggregation

Lo script processa tutti i round e aggrega:
```python
for round in rounds:
    for match in round.pairings:
        player_stats[player_id]['W'] += 1 if win else 0
        player_stats[player_id]['T'] += 1 if tie else 0
        player_stats[player_id]['L'] += 1 if loss else 0
```

---

## 🏴‍☠️ One Piece TCG

### Formato Input: CSV

```csv
Ranking,Name,Points,OMW,Player ID,Deck
1,Rossi Mario,9,65.5,OP123,Roronoa Zoro
```

**IMPORTANTE:** Non ha tracking W/T/L nel CSV. Le colonne 10-12 in Results rimangono vuote.

### Sistema Punti Semplificato

```python
# One Piece non ha pareggi
points_victory = points / 3  # Punti dal CSV diviso 3
points_ranking = n_participants - (rank - 1)
points_total = points_victory + points_ranking
```

### OMW% dal CSV

A differenza di Pokemon (calcolato da match), One Piece legge OMW% direttamente dal CSV.

---

## 🎮 Riftbound TCG

### Formato Input: PDF

#### Problema: extract_text() non funziona

I PDF Riftbound hanno font/layout che rendono `extract_text()` inaffidabile:
```python
text = page.extract_text()
# Ritorna solo ~1000 caratteri invece del contenuto completo
# Non contiene i rank (righe con solo numero)
```

#### Soluzione: Strategia ibrida

**STRATEGIA 1: Estrazione tabelle (tentativo)**
```python
tables = page.extract_tables()
# PRO: Molto affidabile quando funziona
# CONTRO: Non sempre riconosce tabelle in questi PDF
```

**STRATEGIA 2: Analisi coordinate (MAIN)**

Usa coordinate fisiche delle parole nel PDF:

```python
# 1. Estrai parole con coordinate
words = page.extract_words()
# Ogni word: {text, x0, x1, top, bottom, ...}

# 2. Raggruppa per Y (stessa riga orizzontale)
lines_dict = {}
for word in words:
    y = round(word['top'])  # Arrotonda per lievi differenze
    if y not in lines_dict:
        lines_dict[y] = []
    lines_dict[y].append(word)

# 3. Ordina righe dall'alto in basso
sorted_lines = sorted(lines_dict.items())

# 4. Ordina parole in ogni riga da sinistra a destra
for y, words_in_line in sorted_lines:
    words_in_line.sort(key=lambda w: w['x0'])
    line_text = ' '.join([w['text'] for w in words_in_line])
```

**Vantaggi:**
- ✅ Non dipende da `extract_text()`
- ✅ Usa posizioni fisiche
- ✅ Robusto contro layout variabili
- ✅ Funziona con font problematici

### State Machine per Parsing Multilinea

Il formato PDF ha rank/nome/nickname/stats su righe separate:

```
1                          ← Rank
Cogliati, Pietro           ← Nome
(2metalupo)                ← Nickname = Membership
12 4-0-0 62.5% 100% 62.5% ← Stats
```

**Stati:**
```python
current_rank = None      # int 1-99
current_name = None      # str
current_nickname = None  # str (membership number)
```

**Transizioni:**

```python
# IDLE → RANK_FOUND
if line matches r'^(\d{1,2})\b':
    current_rank = matched_number
    # Controlla se nickname sulla stessa riga
    if '(nickname)' in rest_of_line:
        extract_both()
    else:
        current_name = rest_of_line (se presente)

# RANK_FOUND → NICKNAME_FOUND
if current_rank and not current_nickname:
    if '(nickname)' in line:
        current_nickname = extract_nickname()
    elif line and not current_name:
        current_name = line

# COMPLETE → STATS_FOUND → SAVE
if all(current_rank, current_name, current_nickname):
    if line matches STATS_PATTERN:
        save_player()
        reset_state()
```

### Regex Patterns

```python
# Rank (1-99)
RANK_PATTERN = r'^(\d{1,2})\b'

# Nickname tra parentesi (= Membership)
NICKNAME_PATTERN = r'\(([^)]+)\)'

# Stats completi
STATS_PATTERN = r'(\d+)\s+(\d+)-(\d+)-(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%'
#                  ^pts    ^W    ^L    ^D     ^OMW      ^GW       ^OGW
```

**ATTENZIONE:** Nel PDF il formato è W-L-D (non W-D-L):
```python
stats_match = re.search(STATS_PATTERN, line)
w = int(stats_match.group(2))  # Vittorie
l = int(stats_match.group(3))  # Sconfitte
d = int(stats_match.group(4))  # Pareggi (Draws/Ties)
```

### Sistema Punti (come Pokemon)

```python
# Match points
win_points = w * 3 + d * 1 + l * 0

# TanaLeague points
points_victory = win_points / 3
points_ranking = n_participants - (rank - 1)
points_total = points_victory + points_ranking
```

### Colonne Results Sheet

```
Col 11: W (vittorie match)
Col 12: T (pareggi/ties - nel PDF sono "D" draws)
Col 13: L (sconfitte match)
```

### Troubleshooting Specifico

#### "Could get FontBBox from font descriptor"
- **Tipo:** Warning (non blocca)
- **Causa:** Font PDF con metadati incompleti
- **Soluzione:** Ignora

#### "Trovati 0 ranks"
- **Causa:** `extract_text()` fallisce
- **Debug:** Verifica che strategia 2 sia attiva
- **Check:** Quante parole trova `extract_words()`? (dovrebbe essere 200+)

#### "Nessun giocatore trovato"
- **Debug checklist:**
  1. Stampa `len(all_words)` - dovrebbe essere 200+
  2. Stampa `len(sorted_lines)` - dovrebbe essere 50+
  3. Stampa prime 20 righe ricostruite - vedi i rank?
  4. Testa regex patterns su testo di esempio

**Esempio debug da aggiungere:**
```python
print(f"📝 Trovate {len(all_words)} parole")
print(f"📏 Raggruppate in {len(sorted_lines)} righe")
print("\n🐛 Prime 20 righe:")
for i, (y, words) in enumerate(sorted_lines[:20]):
    words.sort(key=lambda w: w['x0'])
    text = ' '.join([w['text'] for w in words])
    print(f"  {i:2d} (y={y}): [{text}]")
```

#### Y-coordinate grouping tolerance

Se righe non vengono raggruppate correttamente, aumenta tolleranza:
```python
# Invece di:
y = round(word['top'])

# Usa:
y = round(word['top'] / 2) * 2  # Raggruppa ogni 2 pixel
```

---

## 🗄️ Google Sheets - Dettagli Implementativi

### Batch Operations per API Quota

**IMPORTANTE:** Google Sheets API ha limiti di quota. Usa sempre batch operations:

```python
# ❌ SBAGLIATO - 100 API calls
for row in rows:
    worksheet.append_row(row)

# ✅ CORRETTO - 1 API call
worksheet.append_rows(rows)
```

**Limiti:**
- 300 requests per 60 secondi per progetto
- 60 requests per 60 secondi per utente

### Update vs Append

```python
# Append (nuovo torneo)
ws_results.append_rows(formatted_results)

# Update (ricalcolo stats)
ws_players.batch_update([
    {'range': f'A{row_num}:K{row_num}', 'values': [[...]]},
    ...
])
```

### Column Indices (0-based vs 1-based)

**ATTENZIONE:** gspread usa 1-based, ma list slicing usa 0-based:

```python
# Leggere colonna 3 (Membership)
row = ws.get_all_values()[row_index]
membership = row[2]  # 0-based: colonna 3 = index 2

# Aggiornare colonna 3
ws.update_cell(row_num, 3, value)  # 1-based: colonna 3 = col 3
```

### Results Sheet - Column Mapping

```
Col 1 (row[0]):  Result_ID
Col 2 (row[1]):  Tournament_ID
Col 3 (row[2]):  Membership
Col 4 (row[3]):  Rank
Col 5 (row[4]):  Win_Points
Col 6 (row[5]):  OMW
Col 7 (row[6]):  Pts_Victory
Col 8 (row[7]):  Pts_Ranking
Col 9 (row[8]):  Pts_Total
Col 10 (row[9]): Name
Col 11 (row[10]): W   ← Match tracking
Col 12 (row[11]): T   ← Match tracking
Col 13 (row[12]): L   ← Match tracking
```

### Players Sheet - Column Mapping

```
Col 1 (row[0]):  Membership
Col 2 (row[1]):  Name
Col 3 (row[2]):  TCG
Col 4 (row[3]):  First_Seen
Col 5 (row[4]):  Last_Seen
Col 6 (row[5]):  Total_Tournaments
Col 7 (row[6]):  Tournament_Wins
Col 8 (row[7]):  Match_W
Col 9 (row[8]):  Match_T
Col 10 (row[9]): Match_L
Col 11 (row[10]): Total_Points
```

**IMPORTANTE per fix player stats:**
Quando leggi dati da Players per mostrare in `/players`, usa gli indici corretti:
```python
# ✅ CORRETTO
p.tournaments = row[5]  # Col 6: Total_Tournaments
p.wins = row[6]         # Col 7: Tournament_Wins
p.points = row[10]      # Col 11: Total_Points
```

---

## 🏆 Seasonal Standings - Worst-N Drop Logic

### Configurazione per TCG

```python
# One Piece & Riftbound: drop 2 worst tournaments dopo 8+ tornei
if total_tournaments >= 8:
    max_to_count = total_tournaments - 2
else:
    max_to_count = total_tournaments

# Pokemon: stesso sistema
```

### ARCHIVED Seasons Exemption

**IMPORTANTE:** Le stagioni con status ARCHIVED NON applicano lo scarto:

```python
# Leggi status da Config sheet
season_status = config_row[4].strip().upper()

if season_status == "ARCHIVED":
    max_to_count = total_tournaments  # NO DROP
    print("⚠️  Scarto: NESSUNO (stagione ARCHIVED - archivio dati)")
else:
    # Applica logica normale
    if total_tournaments >= 8:
        max_to_count = total_tournaments - 2
```

**Razionale:** Le stagioni ARCHIVED servono solo come archivio storico, non come competizione attiva. Applicare lo scarto sarebbe fuorviante.

---

## 🎨 Frontend - Chart.js Implementation

### Version

**Chart.js 4.4.0** (da CDN)

### Doughnut Chart - Match Record

```javascript
new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Vittorie', 'Pareggi', 'Sconfitte'],
        datasets: [{
            data: [wins, ties, losses],
            backgroundColor: ['#22c55e', '#fbbf24', '#ef4444']
        }]
    },
    options: {
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});
```

### Bar Chart - Ranking Distribution

```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['1° Posto', '2° Posto', '3° Posto', 'Top 8', 'Altro'],
        datasets: [{
            data: [count_1st, count_2nd, count_3rd, count_top8, count_other],
            backgroundColor: ['#fbbf24', '#e5e7eb', '#cd7f32', '#3b82f6', '#94a3b8']
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 } }
        }
    }
});
```

### Radar Chart - Performance Overview

**5 metriche normalizzate 0-100:**

```python
# Backend calculation
win_rate = (tournament_wins / tournaments_played) * 100
top8_rate = (top8_count / tournaments_played) * 100
victory_rate = (tournament_wins / tournaments_played) * 100  # 1st place only
avg_performance = min(100, (avg_points / 25) * 100)  # 25 points = 100%

# Consistency: based on std deviation
if len(points) > 1:
    std_dev = statistics.stdev(points)
    consistency = max(0, (1 - std_dev / 10) * 100)  # max std_dev = 10 → 0%
else:
    consistency = 100  # Solo 1 torneo = massima consistenza
```

```javascript
new Chart(ctx, {
    type: 'radar',
    data: {
        labels: ['Win Rate', 'Top8 Rate', 'Victory Rate', 'Avg Perf', 'Consistency'],
        datasets: [{
            label: 'Performance',
            data: [win_rate, top8_rate, victory_rate, avg_perf, consistency],
            backgroundColor: 'rgba(102, 126, 234, 0.2)',
            borderColor: 'rgb(102, 126, 234)'
        }]
    },
    options: {
        scales: {
            r: { min: 0, max: 100, ticks: { stepSize: 20 } }
        }
    }
});
```

### Tooltip Best Practices

```javascript
// ✅ Tooltip interattivi su icone info
<span class="info-icon" title="Percentuale di tornei vinti">ℹ️</span>

// ✅ Formattazione valori
title="Win Rate: 15.4%"  // Con unità di misura
title="Media: 15.8 punti" // Numeri con 1 decimale
```

---

## 🔍 Debugging Tips

### Check Column Indices

Quando i dati non corrispondono:
```python
# Stampa header e prima riga
print("Header:", ws.row_values(1))
print("Row 2:", ws.row_values(2))
print("Indices:", {i: val for i, val in enumerate(ws.row_values(2))})
```

### Test Regex

```python
import re
test_cases = [
    "1",
    "Cogliati, Pietro",
    "(2metalupo)",
    "12 4-0-0 62.5% 100% 62.5%"
]
for line in test_cases:
    print(f"Testing: [{line}]")
    # Test your patterns here
```

### Dry Run Mode

Aggiungi sempre modalità test:
```python
if test_mode:
    print("⚠️  TEST MODE - Nessuna scrittura")
    # Show what would be written
    for row in data:
        print(row)
else:
    # Actual write
    worksheet.append_rows(data)
```

---

## 📚 Riferimenti Codice

### parse_pdf() completo - Riftbound

File: `tanaleague2/import_riftbound.py`

Funzione chiave da consultare per:
- Estrazione coordinate PDF
- State machine multilinea
- Gestione edge cases (nome su più righe, nickname mancante, etc.)

### update_players_stats() - Tutti i TCG

Presente in tutti e 3 gli import scripts.

**IMPORTANTE:** Ricalcola SEMPRE da zero da Results sheet:
```python
# NON incrementare stats esistenti
# MA ricalcolare tutto da Results
for result in all_results:
    if result.membership == player_membership:
        # Accumula
```

Questo evita inconsistenze da import parziali o errori.

---

**Fine Technical Notes**

Ultimo aggiornamento: 21 Novembre 2025
