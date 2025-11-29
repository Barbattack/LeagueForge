# 🚀 Deploy LeagueForge su Render.com

Guida completa per deployare LeagueForge su Render.com con auto-deploy da GitHub.

---

## 📋 Prerequisiti

Prima di iniziare assicurati di avere:
- ✅ Repository GitHub con LeagueForge
- ✅ Google Sheet creato e configurato
- ✅ Service Account Google con credenziali JSON
- ✅ Account GitHub (per login Render)

---

## 🎯 STEP 1: Prepara Repository

Assicurati che il branch principale (main o master) contenga:
- `requirements.txt` con `gunicorn`
- `render.yaml` (opzionale, auto-configurazione)
- `leagueforge/utils_credentials.py` (gestione credenziali cloud)

---

## 🔐 STEP 2: Prepara Credenziali Google

Apri il file delle credenziali del service account (es. `leagueforge-479711-ec2cd4c0b4a7.json`).

**IMPORTANTE**: Dovrai copiare TUTTO il contenuto del file JSON.

Esempio contenuto:
```json
{
  "type": "service_account",
  "project_id": "leagueforge-479711",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "leagueforge@leagueforge-479711.iam.gserviceaccount.com",
  ...
}
```

**Copia TUTTO** (dalle prime parentesi alle ultime) - servirà nello Step 5.

---

## 🌐 STEP 3: Crea Account Render

1. Vai su https://render.com
2. Click **"Get Started"** o **"Sign Up"**
3. **Usa "Sign in with GitHub"** (consigliato!)
4. Autorizza Render ad accedere ai tuoi repository

---

## ⚙️ STEP 4: Crea Web Service

1. Dalla Dashboard Render, click **"New +"** (in alto a destra)
2. Seleziona **"Web Service"**
3. Connetti il repository:
   - Se non vedi il repository, click **"Configure account"** e autorizza l'accesso
   - Seleziona: **`Barbattack/LeagueForge`**
4. Configurazione servizio:

| Campo | Valore |
|-------|--------|
| **Name** | `leagueforge` (o nome a tua scelta) |
| **Region** | Europe (Frankfurt) - per GDPR |
| **Branch** | `main` (o il branch che preferisci) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `cd leagueforge && gunicorn app:app --bind 0.0.0.0:$PORT` |
| **Instance Type** | **Free** |

5. **NON cliccare "Create Web Service" ancora** - prima configura le variabili d'ambiente!

---

## 🔑 STEP 5: Configura Environment Variables

Prima di deployare, configura queste variabili nella sezione **"Environment Variables"**:

### Variabili Obbligatorie

| Key | Value | Note |
|-----|-------|------|
| `SHEET_ID` | `1G_pCJ26YatDGAeF_FxqU0gfWXR0T1ShG9EbGIdn4Pgg` | Il tuo Google Sheet ID |
| `GOOGLE_CREDENTIALS_JSON` | `{...}` | **TUTTO** il contenuto del file JSON |
| `SECRET_KEY` | `[chiave casuale]` | Genera con: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASSWORD_HASH` | `pbkdf2:sha256:...` | Genera con: `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('TUA_PASSWORD'))"` |

### Variabili Opzionali

| Key | Value | Default |
|-----|-------|---------|
| `ADMIN_USERNAME` | `admin` | Username admin |
| `STORE_NAME` | `LeagueForge` | Nome negozio |
| `DEBUG` | `False` | Mai `True` in produzione! |

### Come inserire GOOGLE_CREDENTIALS_JSON

1. Click **"Add Environment Variable"**
2. Key: `GOOGLE_CREDENTIALS_JSON`
3. Value: Incolla **TUTTO** il contenuto del file JSON
   - Include le parentesi graffe `{ }`
   - Mantieni TUTTE le virgolette e backslash
   - NON modificare nulla
4. Click **"Add"**

**Esempio visivo:**
```
Key:   GOOGLE_CREDENTIALS_JSON
Value: {"type":"service_account","project_id":"leagueforge-479711", ...}
       ↑ Inizia dalla parentesi graffa                                 ↑ Finisce qui
```

---

## 🚀 STEP 6: Deploy!

1. Scroll in fondo
2. Click **"Create Web Service"**
3. Render inizierà il build automaticamente

**Processo di deploy (~2-3 minuti):**
```
→ Cloning repository...
→ Installing dependencies...
→ Starting server...
✓ Deploy successful!
```

Vedrai i logs in tempo reale. Se tutto va bene vedrai:
```
[INFO] Booting worker with pid: 123
[INFO] Starting gunicorn 21.x.x
```

---

## 🎉 STEP 7: Testa la Webapp

La tua webapp sarà disponibile su:
```
https://leagueforge.onrender.com
```
(o il nome che hai scelto)

**Test rapidi:**
1. Apri l'URL → dovresti vedere la homepage LeagueForge
2. Vai su `/admin/login` → testa login admin
3. Controlla che carichi i dati dal Google Sheet

---

## ⚡ Auto-Deploy da GitHub

**MAGIA**: Ogni volta che fai push su GitHub (branch configurato), Render deploya automaticamente!

```bash
git add .
git commit -m "Update classifiche"
git push
→ Render rileva il push e deploya automaticamente! 🎉
```

Vedi il progresso nella Dashboard Render → "Events"

---

## 🔍 Troubleshooting

### Errore: "Application failed to start"

**Check 1 - Logs:**
- Dashboard Render → "Logs"
- Cerca errori Python (ImportError, ModuleNotFoundError)

**Check 2 - Environment Variables:**
```
Missing: SHEET_ID
→ Aggiungi nella sezione Environment
```

**Check 3 - Credenziali Google:**
```
Error: 'NoneType' object has no attribute...
→ Verifica GOOGLE_CREDENTIALS_JSON sia valido JSON
```

### Sleep Mode (Free Tier)

App va in sleep dopo 15 min inattività. Al primo accesso:
- ⏱️ Cold start: ~30 secondi
- ✅ Poi risponde normalmente

**Soluzione:** Upgrade a **Starter** ($7/mese) → sempre attivo

### Credenziali Google non funzionano

1. Verifica che service account abbia accesso al Google Sheet (Editor)
2. Controlla che `GOOGLE_CREDENTIALS_JSON` sia JSON **valido**
3. Usa validator: https://jsonlint.com

---

## 💰 Costi

| Tier | Prezzo | Caratteristiche |
|------|--------|-----------------|
| **Free** | $0 | 750h/mese, sleep dopo 15min |
| **Starter** | $7/mese | Sempre attivo, più risorse |

**Modello Franchise:**
- Ogni negozio → proprio account Render free
- O condividi account e crei servizi separati ($7/mese ciascuno)

---

## 📚 Risorse

- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Status: https://status.render.com

---

## 🎯 Prossimi Passi

Dopo il primo deploy di successo:
1. Personalizza STORE_NAME, colori, logo
2. Configura dominio custom (opzionale)
3. Monitora logs e performance
4. Setup backup automatico Google Sheets

**Buon deployment! 🚀**
