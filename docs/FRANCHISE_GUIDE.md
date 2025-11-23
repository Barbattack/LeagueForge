# TanaLeague - Guida Franchise

Guida completa per gestire il modello franchise di TanaLeague.

## Panoramica

Il modello franchise ti permette di:
- Gestire UN SOLO Service Account Google (tu)
- Creare pacchetti pre-configurati per ogni negozio
- I negozi ricevono uno ZIP, fanno doppio-click, e funziona!

## Requisiti

### Per Te (Franchise Manager)
- Python 3.8+ installato
- Account Google Cloud Console con Service Account
- File `credentials.json` del Service Account
- `config.py` configurato nel tuo ambiente

### Per i Negozi
- Windows, Mac o Linux
- Python 3.8+ installato
- Connessione internet

## Setup Iniziale (Una Volta Sola)

### 1. Crea il Service Account

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto: "TanaLeague-Franchise"
3. Abilita le API:
   - Google Sheets API
   - Google Drive API
4. Crea un Service Account:
   - Nome: "tanaleague-franchise"
   - Scarica il file JSON delle chiavi
5. Salva il file come `credentials.json` nella cartella `tanaleague2/`

### 2. Configura il Tuo Ambiente

```bash
cd tanaleague2
python setup_wizard.py
```

Segui il wizard per configurare il TUO ambiente di sviluppo.

### 3. Testa il Sistema

```bash
python check_setup.py
python app.py
```

Verifica che tutto funzioni sul tuo sistema.

## Creare un Pacchetto per un Nuovo Negozio

### Comando Rapido

```bash
cd tanaleague2
python create_store_package.py
```

### Processo Completo

1. **Esegui lo script**:
   ```bash
   python create_store_package.py
   ```

2. **Inserisci i dati**:
   - Nome negozio (es. "Game Corner Milano")
   - Email del negozio (per condividere il Google Sheet)
   - Password admin (default: tanaleague123)

3. **Lo script automaticamente**:
   - Crea un nuovo Google Sheet per il negozio
   - Inizializza tutti i fogli necessari (Config, Tournaments, Results, ecc.)
   - Condivide il Google Sheet con l'email del negozio
   - Genera un pacchetto ZIP pre-configurato

4. **Output**:
   - File ZIP: `packages/TanaLeague_NomeNegozio.zip`
   - Link Google Sheet per condivisione

### Contenuto del Pacchetto ZIP

```
TanaLeague_NomeNegozio/
├── tanaleague2/
│   ├── app.py
│   ├── config.py          # Pre-configurato!
│   ├── credentials.json   # Le TUE credenziali
│   ├── templates/
│   ├── static/
│   └── ...
├── install.bat            # Installazione Windows
├── avvia.bat              # Avvio Windows
└── LEGGIMI.txt            # Istruzioni per il negozio
```

## Istruzioni per i Negozi

Quando invii il pacchetto a un negozio, includi queste istruzioni:

### Per Windows

1. **Installa Python** (se non l'hai):
   - Vai su https://www.python.org/downloads/
   - Scarica e installa Python
   - IMPORTANTE: Seleziona "Add Python to PATH"

2. **Estrai il pacchetto**:
   - Estrai lo ZIP in una cartella (es. Desktop)

3. **Installa** (prima volta):
   - Doppio click su `install.bat`
   - Attendi che finisca

4. **Avvia** (ogni giorno):
   - Doppio click su `avvia.bat`
   - Apri nel browser: http://localhost:5000

5. **Accesso Admin**:
   - URL: http://localhost:5000/admin/login
   - Username: admin
   - Password: (quella che hai fornito)

### Per Mac/Linux

```bash
# Estrai lo ZIP
unzip TanaLeague_NomeNegozio.zip
cd TanaLeague_NomeNegozio

# Installa (prima volta)
cd tanaleague2
pip3 install -r requirements.txt

# Avvia
python3 app.py
```

## Gestione Quote API

### Limiti Google Sheets API

- **Limite**: 300 richieste/minuto per progetto
- **Condiviso**: Tra TUTTI i negozi che usano il tuo Service Account

### Per 10 Negozi

Con 10 negozi attivi:
- ~30 richieste/minuto per negozio (media)
- Raramente si raggiunge il limite
- Il sistema ha retry automatico

### Retry Automatico

Il sistema include `api_utils.py` che:
- Rileva errori di rate limit
- Attende automaticamente (exponential backoff)
- Riprova fino a 3 volte
- Mostra messaggi user-friendly

### Monitoraggio

Controlla l'utilizzo su [Google Cloud Console](https://console.cloud.google.com/):
1. API e servizi > Dashboard
2. Seleziona "Google Sheets API"
3. Visualizza metriche di utilizzo

### Se Raggiungi il Limite

Opzioni:
1. **Aspetta**: Il limite si resetta ogni minuto
2. **Scala il progetto**: Richiedi quota maggiore a Google
3. **Separa progetti**: Crea Service Account separati per negozi ad alto volume

## Manutenzione

### Aggiornare un Negozio

1. Prepara i file aggiornati
2. Crea un nuovo pacchetto con `create_store_package.py`
3. Chiedi al negozio di:
   - Fermare l'applicazione (CTRL+C)
   - Sovrascrivere i file (TRANNE config.py!)
   - Riavviare

### Backup

Ogni negozio ha il proprio Google Sheet. I dati sono sempre accessibili anche senza l'applicazione.

### Problemi Comuni

| Problema | Soluzione |
|----------|-----------|
| "Python non trovato" | Reinstalla Python con "Add to PATH" |
| "Errore connessione Sheet" | Verifica internet, riprova |
| "API quota exceeded" | Attendi 1 minuto, riprova |
| "Permission denied" | Verifica condivisione Google Sheet |

## Sicurezza

### Credenziali

- Le credenziali del Service Account sono copiate in ogni pacchetto
- I negozi NON vedono la chiave completa (è in un file JSON)
- Ogni negozio ha il PROPRIO Google Sheet (dati separati)

### Accesso ai Dati

- Tu (franchise manager): Accesso a TUTTI i Google Sheet
- Negozio: Accesso SOLO al proprio Google Sheet
- Service Account: Accesso a tutti (necessario per funzionare)

### Best Practices

1. **Password admin**: Usa password diverse per ogni negozio
2. **Email negozio**: Condividi sempre il Google Sheet con il negozio
3. **Backup**: Consiglia ai negozi di esportare i dati periodicamente
4. **Aggiornamenti**: Tieni traccia delle versioni inviate a ogni negozio

## Scalabilità

### Fino a 10 Negozi

- Un solo Service Account funziona bene
- Nessun costo aggiuntivo
- Gestione centralizzata

### 10-50 Negozi

- Considera Service Account separati per regione
- Monitora attentamente le quote
- Valuta caching più aggressivo

### 50+ Negozi

- Passa a un'architettura con database centrale
- Considera hosting cloud (Railway, Render, ecc.)
- Implementa load balancing

## Checklist Nuovo Negozio

- [ ] Raccogli informazioni (nome, email, password desiderata)
- [ ] Esegui `python create_store_package.py`
- [ ] Verifica creazione Google Sheet
- [ ] Testa il pacchetto localmente (opzionale)
- [ ] Invia ZIP al negozio
- [ ] Invia istruzioni LEGGIMI.txt
- [ ] Verifica che il negozio riesca ad avviare
- [ ] Condividi link supporto

## Supporto

Per problemi:
1. Verifica `LEGGIMI.txt` nel pacchetto
2. Chiedi al negozio screenshot dell'errore
3. Controlla Google Cloud Console per errori API
4. Verifica che il Google Sheet sia accessibile

---

*Ultima modifica: Novembre 2025*
