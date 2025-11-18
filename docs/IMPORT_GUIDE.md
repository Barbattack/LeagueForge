# 📥 Guida Import Tornei

Guida completa per importare tornei da CSV, PDF e TDF nei 3 TCG supportati.

---

## 📋 Indice

- [One Piece (CSV)](#-one-piece-tcg-csv)
- [Pokémon (TDF/XML)](#-pokémon-tcg-tdfxml)
- [Riftbound (PDF)](#-riftbound-tcg-pdf)
- [Test Mode](#-test-mode-dry-run)
- [Troubleshooting](#-troubleshooting)

---

## 🏴‍☠️ One Piece TCG (CSV)

### Formato File

**Sorgente**: Export da [Limitlesstcg](https://play.limitlesstcg.com/)

**Formato**: CSV con le seguenti colonne (ordine importante):
```
Ranking, User Name, Membership Number, Win Points, OMW %, Record, Points_Victory, Points_Ranking, Points_Total
```

**Esempio CSV:**
```csv
Ranking,User Name,Membership Number,Win Points,OMW %,Record
1,Cogliati Pietro,12345,12,65.5,4-0
2,Rossi Mario,67890,9,62.3,3-1
...
```

### Nome File

Il nome del file **deve** contenere la data in uno dei seguenti formati:

- `YYYY_MM_DD_OP12.csv` → es. `2025_06_12_OP12.csv`
- `DD_MM_YYYY_OP12.csv` → es. `12_06_2025_OP12.csv`
- `YYYY-MM-DD_OP12.csv` → es. `2025-06-12_OP12.csv`
- `DD_Month_YYYY_OP12.csv` → es. `12_June_2025_OP12.csv`

**La data viene estratta automaticamente dal nome file!**

### Import Command

```bash
cd tanaleague2
python import_tournament.py --csv path/to/file.csv --season OP12
```

### Parametri

- `--csv`: Path al file CSV (obbligatorio)
- `--season`: ID stagione (es. OP12, OP13) (obbligatorio)
- `--test`: Test mode - verifica senza scrivere (opzionale)

### Cosa Fa

1. ✅ Valida formato CSV e data nel filename
2. ✅ Calcola punti TanaLeague (vittoria + ranking)
3. ✅ Identifica X-0, X-1, Altri per buoni negozio
4. ✅ Calcola distribuzione buoni
5. ✅ Scrive in: Tournaments, Results, Vouchers, Players
6. ✅ Aggiorna Seasonal_Standings_PROV
7. ✅ Check e sblocca achievement automaticamente
8. ✅ Crea backup in Backup_Log

### Output Esempio

```
🚀 IMPORT TORNEO: 2025_06_12_OP12.csv
📊 Stagione: OP12

📂 Lettura CSV...
   👥 Partecipanti: 16
   📅 Data: 2025-06-12
   🎮 Round: 4
   🏆 Vincitore: Cogliati Pietro

⚙️  Recupero configurazione OP12...
   💶 Entry fee: 5€
   📦 Pack cost: 4€

🧮 Calcolo punti...
🎯 Identificazione X-0/X-1...
💰 Calcolo buoni negozio...
   💵 Fondo totale: 80€
   📦 Costo buste: 64€
   💸 Distribuito: 80€
   💰 Rimane: 0€

💾 Creazione backup...
📝 Scrittura dati...
   📊 Foglio Tournaments...
   📊 Foglio Results...
   📊 Foglio Vouchers...
   📊 Foglio Players...
   📊 Foglio Seasonal_Standings...
   🎮 Check achievement...
   🏆 0000012345: 🎬 First Blood
   ✅ 1 achievement sbloccato!

✅ IMPORT COMPLETATO!
```

---

## ⚡ Pokémon TCG (TDF/XML)

### Formato File

**Sorgente**: Export da Play! Pokémon Tournament software

**Formato**: TDF (XML interno)

**Contenuto**: File XML che contiene:
- Informazioni torneo (nome, data, formato)
- Lista giocatori (player ID, nome)
- Standings finali (rank, record, tiebreakers)
- Match results H2H (opzionale)

### Import Command

```bash
cd tanaleague2
python parse_pokemon_tdf.py --tdf path/to/tournament.tdf --season PKM-FS25
```

### Parametri

- `--tdf`: Path al file TDF (obbligatorio)
- `--season`: ID stagione (es. PKM-FS25, PKM-WIN25) (obbligatorio)
- `--test`: Test mode (opzionale)

### Cosa Fa

1. ✅ Parsa XML del file TDF
2. ✅ Estrae standings con rank, W-L-D, tiebreakers
3. ✅ Calcola punti TanaLeague
4. ✅ Estrae match H2H (se disponibili)
5. ✅ Scrive in: Tournaments, Results, Pokemon_Matches, Players
6. ✅ Aggiorna Seasonal_Standings_PROV
7. ✅ Check e sblocca achievement automaticamente

### Output Esempio

```
🚀 IMPORT POKEMON TOURNAMENT

📂 Parsing TDF file: tournament.tdf
   🏆 Torneo: Pokemon League Cup
   📅 Data: 2025-06-15
   👥 Partecipanti: 24

🧮 Calcolo punti TanaLeague...
📊 Importazione Pokemon TDF...

✅ Tournament: PKM-FS25_2025-06-15
✅ Results: 24 giocatori
✅ Matches: 96 match
✅ Players: 8 nuovi, 16 aggiornati
✅ Seasonal Standings aggiornate per PKM-FS25

🎮 Check achievement...
🏆 0000067890: 🎬 Debutto
🏆 0000012345: 📅 Regular
✅ 2 achievement sbloccati!

🎉 IMPORT COMPLETATO!
```

### Note Pokémon

- **Display Nomi**: I nomi vengono mostrati come "Nome I." (es. "Pietro C.")
- **Match H2H**: Se disponibili, vengono salvati in `Pokemon_Matches` sheet
- **Sistema Punti**: W=3, D=1, L=0 (supporta pareggi)

---

## 🌌 Riftbound TCG (PDF)

### Formato File

**Sorgente**: PDF export dal software di gestione tornei

**Formato**: PDF con tabelle strutturate

**Struttura Richiesta**: Il PDF deve contenere almeno una tabella con:
```
Rank | Name (Nickname) | Points | W-L-D | OMW% | GW% | OGW%
```

**Esempio Tabella:**
```
1  | Cogliati, Pietro (2metalupo) | 12 | 4-0-0 | 62.5% | 100% | 62.5%
2  | Rossi, Mario (HotelMotel)    | 9  | 3-1-0 | 58.3% | 75%  | 60.0%
```

**Note Importanti:**
- Il nickname DEVE essere tra parentesi: `(nickname)`
- Il nickname diventa il Membership Number
- Supporta nickname con spazi: `(Hotel Motel)` funziona!

### Import Command

```bash
cd tanaleague2
python import_riftbound.py --pdf path/to/tournament.pdf --season RFB01
```

### Parametri

- `--pdf`: Path al file PDF (obbligatorio)
- `--season`: ID stagione (es. RFB01, RFB-WIN25) (obbligatorio)
- `--test`: Test mode (opzionale)

### Cosa Fa

1. ✅ Parsa PDF con pdfplumber (estrazione tabelle)
2. ✅ Estrae nickname da `(parentesi)`
3. ✅ Gestisce nickname multilinea (es. `Hotel\nMotel`)
4. ✅ Calcola punti TanaLeague
5. ✅ Scrive in: Tournaments, Results, Players
6. ✅ Aggiorna Seasonal_Standings_PROV
7. ✅ Check e sblocca achievement automaticamente

### Output Esempio

```
🔍 Parsing PDF: RFB_2025_11_10.pdf

🔍 Strategia 1: Estrazione tabelle...
  📊 Pagina 1: 1 tabelle trovate
    Tabella 1: 18 righe

Giocatori trovati: 16

🎯 Elaborazione risultati...
  ✓ Rank 1: Cogliati, Pietro (2metalupo) - 4-0-0
  ✓ Rank 2: Rossi, Mario (HotelMotel) - 3-1-0
  ...

📊 Importazione in Google Sheet...
✅ Tournament: RFB01_2025-11-10
✅ Results: 16 giocatori
✅ Players: 4 nuovi, 12 aggiornati
✅ Seasonal Standings aggiornate per RFB01

🎮 Check achievement...
🏆 0002metalupo: 🎬 First Blood
🏆 0002metalupo: 🎯 Podium Climber
✅ 2 achievement sbloccati!

🎉 IMPORT COMPLETATO!
```

### Note Riftbound

- **Display Nomi**: Mostra il nickname (Membership Number) invece del nome completo
- **Nickname Parsing**: Robusto - gestisce spazi, multilinea, caratteri speciali
- **Sistema Punti**: W=3, D=1, L=0 (supporta pareggi)

---

## 🧪 Test Mode (Dry Run)

**Tutti e 3 gli script** supportano la modalità test per verificare il file senza scrivere su Google Sheets.

### One Piece

```bash
python import_tournament.py --csv file.csv --season OP12 --test
```

### Pokémon

```bash
python parse_pokemon_tdf.py --tdf file.tdf --season PKM-FS25 --test
```

### Riftbound

```bash
python import_riftbound.py --pdf file.pdf --season RFB01 --test
```

### Cosa Fa Test Mode

- ✅ Legge e parsa il file
- ✅ Valida formato e dati
- ✅ Calcola punti e standings
- ✅ Mostra output completo
- ❌ **NON scrive** su Google Sheets
- ❌ **NON crea** backup
- ❌ **NON sblocca** achievement

**Usa test mode per:**
- Verificare formato file prima di importare
- Debuggare problemi di parsing
- Vedere anteprima risultati

---

## 🔧 Troubleshooting

### Errore: "Nessun giocatore trovato nel PDF"

**Causa**: PDF non ha tabelle strutturate o formato non riconosciuto

**Soluzione**:
1. Verifica che il PDF contenga tabelle (non solo testo)
2. Controlla che i nickname siano tra `(parentesi)`
3. Prova a esportare nuovamente il PDF dal software

### Errore: "ValueError: Date format not recognized"

**Causa**: Nome file CSV non contiene data in formato riconosciuto

**Soluzione**:
Rinomina il file in uno di questi formati:
- `2025_06_12_OP12.csv`
- `12_06_2025_OP12.csv`
- `2025-06-12_OP12.csv`

### Errore: "Torneo già importato"

**Causa**: Tournament ID già esiste nel foglio Tournaments

**Opzioni**:
1. Rispondi `y` per sovrascrivere (sostituisce dati)
2. Rispondi `n` per annullare
3. Cambia data nel filename se è un torneo diverso

### Errore: "gspread.exceptions.APIError: RESOURCE_EXHAUSTED"

**Causa**: Troppi request a Google Sheets API

**Soluzione**:
- Aspetta 1-2 minuti
- Riprova import
- Evita import multipli simultanei

### Warning: "Achievement check failed"

**Causa**: Sheet Achievement_Definitions o Player_Achievements non esistono

**Soluzione**:
```bash
cd tanaleague2
python setup_achievements.py
```

Questo crea i fogli necessari.

### Nickname con spazi non rilevati (Riftbound)

**Causa**: Multilinea nel PDF - il parser attuale gestisce questo caso!

**Verifica**:
- Il nickname deve essere tra parentesi: `(Hotel Motel)`
- Lo script sostituisce `\n` con spazi automaticamente

---

## 📊 Confronto Import

| Feature | One Piece (CSV) | Pokémon (TDF) | Riftbound (PDF) |
|---------|----------------|---------------|-----------------|
| **Formato** | CSV | XML/TDF | PDF |
| **Sorgente** | Limitlesstcg | Play! Pokémon | Software gestione |
| **Match H2H** | ❌ No | ✅ Sì | ❌ No |
| **Pareggi** | ❌ No (W/L) | ✅ Sì (W/D/L) | ✅ Sì (W/D/L) |
| **Buoni Negozio** | ✅ Sì | ❌ No | ❌ No |
| **Display Nome** | Full Name | Nome I. | Nickname |
| **Test Mode** | ✅ Sì | ✅ Sì | ✅ Sì |
| **Achievement** | ✅ Auto | ✅ Auto | ✅ Auto |
| **Standings** | ✅ Auto | ✅ Auto | ✅ Auto |

---

## 🎯 Best Practices

1. **Usa sempre Test Mode prima** dell'import reale
2. **Verifica formato file** prima di importare
3. **Backup Google Sheet** prima di import grandi
4. **Un import alla volta** (evita race conditions)
5. **Controlla output** per eventuali warning
6. **Verifica standings** sulla webapp dopo import

---

## 📞 Supporto

**Problemi non risolti?**

1. Controlla [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Verifica log output dettagliato
3. Apri issue su GitHub con:
   - Comando eseguito
   - Output completo
   - File di esempio (se possibile)

---

**Happy Importing! 🎮**
