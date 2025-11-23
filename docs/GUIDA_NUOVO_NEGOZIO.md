# Guida: Aggiungere un Nuovo Negozio a TanaLeague

Questa guida ti accompagna passo-passo quando un negozio ti chiede di usare TanaLeague.

---

## Prima di Iniziare

### Requisiti (da verificare UNA VOLTA, la prima volta)

- [ ] Python 3.8+ installato sul TUO computer
- [ ] File `credentials.json` del Service Account nella cartella `tanaleague2/`
- [ ] `config.py` configurato con le tue credenziali master
- [ ] Repository TanaLeague aggiornato

### Verifica Rapida

```bash
cd tanaleague2
python check_setup.py
```

Se tutto OK, sei pronto!

---

## Checklist Nuovo Negozio

### 1. Raccogli le Informazioni

Chiedi al negozio:

| Informazione | Esempio | Note |
|--------------|---------|------|
| **Nome negozio** | "Game Corner Milano" | Come vuole apparire |
| **Email** | negozio@email.com | Per condividere il Google Sheet |
| **Password admin** | (suggerisci tu) | Minimo 6 caratteri |

**Suggerimento password**: Usa qualcosa di semplice ma non banale, tipo `NomeNegozio2025!`

---

### 2. Crea il Pacchetto

```bash
cd tanaleague2
python create_store_package.py
```

**Cosa ti chiede:**
```
Nome del negozio: Game Corner Milano
Email del negozio: gamecorner@email.com
Password admin [default: tanaleague123]: GameCorner2025!

Procedere? (y/n): y
```

**Cosa succede:**
1. Crea un nuovo Google Sheet "TanaLeague - Game Corner Milano"
2. Inizializza tutti i fogli (Config, Tournaments, Results, ecc.)
3. Condivide automaticamente con l'email del negozio
4. Genera `packages/TanaLeague_Game_Corner_Milano.zip`

**Output finale:**
```
📦 File: packages/TanaLeague_Game_Corner_Milano.zip
📊 Google Sheet: https://docs.google.com/spreadsheets/d/ABC123...
🔑 Password admin: GameCorner2025!
```

---

### 3. Verifica il Google Sheet

1. Apri il link del Google Sheet
2. Verifica che ci siano tutti i fogli:
   - Config (con 3 stagioni esempio)
   - Tournaments
   - Results
   - Players
   - Achievement_Definitions (con 30+ achievement)
   - Player_Achievements
   - Seasonal_Standings_PROV
   - Seasonal_Standings_FINAL
   - Vouchers
   - Pokemon_Matches
   - Riftbound_Matches
   - Backup_Log

3. Verifica che sia condiviso con l'email del negozio

---

### 4. Prepara le Istruzioni per il Negozio

Copia e personalizza questo messaggio:

```
Ciao! 🎮

Ecco TanaLeague pronto per [NOME NEGOZIO]!

📦 FILE: [allega TanaLeague_NomeNegozio.zip]

📋 ISTRUZIONI:

1. PREREQUISITO: Installa Python
   - Vai su https://www.python.org/downloads/
   - Scarica e installa
   - IMPORTANTE: Seleziona "Add Python to PATH"!

2. INSTALLAZIONE (una volta sola):
   - Estrai lo ZIP in una cartella
   - Doppio click su "install.bat"
   - Aspetta che finisca

3. AVVIO (ogni giorno):
   - Doppio click su "avvia.bat"
   - Apri nel browser: http://localhost:5000

4. ACCESSO ADMIN:
   - URL: http://localhost:5000/admin/login
   - Username: admin
   - Password: [PASSWORD]

5. IL TUO GOOGLE SHEET:
   - Link: [LINK GOOGLE SHEET]
   - Qui trovi tutti i dati dei tornei
   - Puoi consultarlo anche senza l'app

📞 Per problemi contattami!
```

---

### 5. Invia il Pacchetto

**Opzioni di invio:**

| Metodo | Pro | Contro |
|--------|-----|--------|
| **WeTransfer** | Facile, gratuito | Link scade |
| **Google Drive** | Permanente | Richiede account |
| **Email diretta** | Semplice | Limite 25MB |
| **Telegram/WhatsApp** | Immediato | Compressione |

**Consiglio**: WeTransfer per file grandi, Email per file piccoli.

---

### 6. Supporto Post-Installazione

**Problemi comuni e soluzioni:**

| Problema | Soluzione |
|----------|-----------|
| "Python non trovato" | Reinstalla Python con "Add to PATH" selezionato |
| "Errore connessione" | Verifica internet, riprova |
| "API quota exceeded" | Aspetta 1 minuto, il sistema riprova automaticamente |
| "Permission denied" | Verifica che l'email sia corretta nel Google Sheet |
| "Modulo non trovato" | Esegui di nuovo install.bat |

**Se il negozio non riesce:**
1. Chiedi screenshot dell'errore
2. Verifica che Python sia installato: `python --version` nel terminale
3. Verifica che il Google Sheet sia accessibile

---

### 7. Registra il Negozio

Tieni traccia dei negozi attivi. Crea un file o usa un foglio:

| Negozio | Email | Data Attivazione | Google Sheet ID | Note |
|---------|-------|------------------|-----------------|------|
| Game Corner Milano | gc@email.com | 2025-11-23 | ABC123... | OK |
| Ludoteca Roma | lr@email.com | 2025-11-25 | DEF456... | Usa solo Pokemon |

---

## Operazioni Ricorrenti

### Quando il Negozio Chiede Aiuto

1. **"Come importo un torneo?"**
   - Admin Panel → Import → Seleziona TCG → Carica file
   - Oppure da terminale: `python import_onepiece.py --csv file.csv --season OP01`

2. **"Come creo una nuova stagione?"**
   - Apri Google Sheet → Foglio "Config"
   - Aggiungi nuova riga con: Season_ID, TCG, Name, Status=ACTIVE
   - Imposta la vecchia stagione a Status=CLOSED

3. **"I dati non si aggiornano"**
   - La cache si aggiorna ogni 5 minuti
   - Per forzare: visita `/api/refresh`

4. **"Voglio personalizzare i colori"**
   - Modifica `config.py` → STORE_PRIMARY_COLOR, STORE_SECONDARY_COLOR
   - Riavvia l'app

### Aggiornare un Negozio

Se rilasci una nuova versione:

1. Prepara i file aggiornati
2. Crea un nuovo pacchetto (opzionale, o invia solo i file modificati)
3. Istruzioni per il negozio:
   - Ferma l'app (CTRL+C)
   - Sostituisci i file (TRANNE config.py!)
   - Riavvia con avvia.bat

---

## Riepilogo Comandi

```bash
# Crea pacchetto per nuovo negozio
cd tanaleague2
python create_store_package.py

# Verifica il tuo setup
python check_setup.py

# Testa l'app localmente
python app.py
```

---

## Contatti Utili

- **Google Cloud Console**: https://console.cloud.google.com/
- **Python Download**: https://www.python.org/downloads/
- **WeTransfer**: https://wetransfer.com/

---

## Note Personali

Usa questo spazio per le tue note:

```
[Le tue note qui]
```

---

*Guida creata: Novembre 2025*
