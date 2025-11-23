# 🧪 Guida ai Test - TanaLeague

Guida completa al sistema di test automatici di TanaLeague.

---

## 📋 Indice

- [Cos'è il Testing](#-cosè-il-testing)
- [Struttura File Test](#-struttura-file-test)
- [Come Eseguire i Test](#-come-eseguire-i-test)
- [Spiegazione Test Esistenti](#-spiegazione-test-esistenti)
- [Come Aggiungere Nuovi Test](#-come-aggiungere-nuovi-test)
- [CI/CD con GitHub Actions](#-cicd-con-github-actions)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Cos'è il Testing

I test automatici sono codice che verifica che l'applicazione funzioni correttamente.

### Perché usare i test?

| Senza Test | Con Test |
|------------|----------|
| "Funziona sul mio PC" | Funziona ovunque |
| Bug scoperti dagli utenti | Bug scoperti prima del deploy |
| Paura di modificare codice | Modifichi con sicurezza |
| Nessuna documentazione | I test documentano il comportamento |

### Tipi di Test in TanaLeague

1. **Unit Test**: Testano singole funzioni (es. `_is_valid_season_id`)
2. **Integration Test**: Testano route Flask (es. homepage carica?)
3. **Mock Test**: Usano dati finti per non dipendere da Google Sheets

---

## 📁 Struttura File Test

```
tests/
├── __init__.py           # File vuoto (necessario per Python)
├── conftest.py           # Configurazione pytest + fixtures + mock data
├── test_app.py           # Test delle route Flask
└── test_achievements.py  # Test del sistema achievement
```

### conftest.py - Cosa Contiene

```python
# Fixtures = oggetti riutilizzabili nei test

@pytest.fixture
def app():
    """Crea app Flask per testing con mock della cache"""
    # Ritorna app configurata per test

@pytest.fixture
def client(app):
    """Client HTTP per fare richieste all'app"""
    return app.test_client()

@pytest.fixture
def mock_data():
    """Dati finti che simulano Google Sheets"""
    return {
        'seasons': [...],
        'standings_by_season': {...},
        'tournaments_by_season': {...}
    }
```

---

## ▶️ Come Eseguire i Test

### Prerequisiti

```bash
pip install pytest pytest-cov
```

### Comandi Base

```bash
# Esegui TUTTI i test
pytest

# Output dettagliato
pytest -v

# Solo test specifici
pytest tests/test_app.py
pytest tests/test_achievements.py

# Solo test con nome specifico
pytest -k "landing"
pytest -k "season"

# Mostra print() durante i test
pytest -s

# Ferma al primo errore
pytest -x
```

### Coverage (Copertura Codice)

```bash
# Mostra quanto codice è testato
pytest --cov=tanaleague2

# Report dettagliato HTML
pytest --cov=tanaleague2 --cov-report=html
# Apri htmlcov/index.html nel browser
```

---

## 📝 Spiegazione Test Esistenti

### test_app.py

#### TestPublicPages
Verifica che le pagine pubbliche carichino senza errori.

```python
def test_landing_page_loads(self, client):
    """Homepage deve ritornare 200 OK"""
    response = client.get('/')
    assert response.status_code == 200

def test_classifiche_page_loads(self, client):
    """Pagina classifiche deve ritornare 200 OK"""
    response = client.get('/classifiche')
    assert response.status_code == 200
```

**Cosa testa**: Le pagine si caricano? Non ci sono errori 500?

#### TestSeasonIdValidation
Verifica la funzione `_is_valid_season_id()`.

```python
def test_valid_base_format(self):
    """OP12, PKM25, RFB1 sono validi"""
    assert _is_valid_season_id('OP12') == True
    assert _is_valid_season_id('PKM25') == True

def test_valid_extended_format(self):
    """PKM-FS25, RFB-S1 sono validi"""
    assert _is_valid_season_id('PKM-FS25') == True

def test_invalid_formats(self):
    """Stringhe invalide ritornano False"""
    assert _is_valid_season_id('INVALID') == False
    assert _is_valid_season_id('') == False
```

**Cosa testa**: La validazione dei season ID funziona correttamente?

#### TestErrorHandling
Verifica gestione errori.

```python
def test_404_page(self, client):
    """Pagina non esistente ritorna 404"""
    response = client.get('/pagina-che-non-esiste')
    assert response.status_code == 404
```

**Cosa testa**: Gli errori vengono gestiti correttamente?

---

### test_achievements.py

#### TestSimpleAchievements
Verifica la logica di unlock degli achievement.

```python
def test_check_tournaments_played_unlocks(self):
    """Achievement 'Regular' si sblocca dopo 5 tornei"""
    player_stats = {'tournaments_played': 5}
    # Verifica che l'achievement venga sbloccato

def test_already_unlocked_not_duplicated(self):
    """Achievement già sbloccato non viene duplicato"""
    # Verifica che non ci siano duplicati
```

**Cosa testa**: Gli achievement si sbloccano correttamente?

#### TestArchivedSeasonsExclusion
Verifica esclusione stagioni ARCHIVED.

```python
def test_archived_seasons_not_counted(self):
    """Stagioni ARCHIVED non contano per stats"""
    # Verifica che ARCHIVED sia escluso
```

**Cosa testa**: Le stagioni archiviate vengono escluse?

---

## ➕ Come Aggiungere Nuovi Test

### 1. Crea nuovo file test (opzionale)

```python
# tests/test_nuovo.py

import pytest

class TestNuovaFeature:
    def test_qualcosa(self):
        assert 1 + 1 == 2
```

### 2. Oppure aggiungi a file esistente

```python
# In tests/test_app.py, aggiungi:

class TestNuovaRoute:
    def test_nuova_pagina(self, client):
        response = client.get('/nuova-pagina')
        assert response.status_code == 200
```

### 3. Pattern comuni

```python
# Test che una pagina carichi
def test_page_loads(self, client):
    response = client.get('/url')
    assert response.status_code == 200

# Test che contenga testo specifico
def test_page_content(self, client):
    response = client.get('/url')
    assert b'Testo Atteso' in response.data

# Test con dati mock
def test_with_mock(self, mock_data):
    result = funzione(mock_data)
    assert result == valore_atteso

# Test che sollevi eccezione
def test_raises_error(self):
    with pytest.raises(ValueError):
        funzione_che_fallisce()
```

---

## 🔄 CI/CD con GitHub Actions

### Come Funziona

1. Fai push su GitHub
2. GitHub Actions legge `.github/workflows/test.yml`
3. Avvia macchina virtuale Ubuntu
4. Installa Python e dipendenze
5. Esegue `pytest`
6. Mostra risultato: ✅ o ❌

### File: .github/workflows/test.yml

```yaml
name: Tests

on:
  push:
    branches: [main, master, develop, feature/*, claude/*]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -v
```

### Vedere Risultati

1. Vai su GitHub → Repository
2. Click tab **Actions**
3. Vedi lista esecuzioni:
   - ✅ Verde = Test passati
   - ❌ Rosso = Test falliti (click per dettagli)

---

## 🔧 Troubleshooting

### Test falliscono localmente

```bash
# Verifica dipendenze
pip install -r requirements.txt

# Verifica versione Python
python --version  # Deve essere 3.10+
```

### Import Error nei test

```bash
# Aggiungi cartella al path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/tanaleague2"
pytest
```

### Mock non funziona

```python
# Verifica che il path del mock sia corretto
# Il path deve essere dove viene USATO, non dove viene DEFINITO
with patch('app.cache') as mock:  # Se usato in app.py
    ...
```

### Test passano localmente ma falliscono su CI

1. Controlla versione Python su CI vs locale
2. Controlla dipendenze in requirements.txt
3. Verifica che non ci siano path hardcoded

---

## 📚 Risorse Utili

- [Documentazione pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.0.x/testing/)

---

**Ultimo aggiornamento:** Novembre 2025
