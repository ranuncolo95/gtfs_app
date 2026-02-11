# gtfs_app

Applicazione didattica per calcolo e visualizzazione di percorsi a partire da dati GTFS su MongoDB, con backend FastAPI e visualizzazione mappa tramite app Shiny montata dentro FastAPI

## Funzionalità principali

- Geocoding tramite provider MapTiler (`/api/geocode`).
- Calcolo percorso tra origine/destinazione con data e ora (`/api/calculate-route`). 
- Visualizzazione mappa tramite Shiny montata su una route dedicata (default: `/shiny`). 
- Lettura dati GTFS da MongoDB (operazioni read-only). 

## Requisiti

- Python 3.10+ (consigliato 3.11/3.12). 
- Dipendenze principali: `fastapi`, `uvicorn`, `pandas`, `geopandas`, `pymongo`, `shiny`, librerie frontend per la mappa. 

## Configurazione

### File `.env`

Il file `.env` deve stare sotto `src/`:

```text
src/.env
SHINY_URL=/shiny
MAPTILER_API_KEY="your_key"
MAPTILER_GEOCODE_LIMIT=5
MAPTILER_TIMEOUT_S=5
``` 

Note: 
- `SHINY_URL` è la route su cui viene montata l’app Shiny. 
- `MAPTILER_API_KEY` è necessaria per abilitare il geocoding. 
- `MAPTILER_GEOCODE_LIMIT` limita il numero massimo di risultati. 
- `MAPTILER_TIMEOUT_S` imposta il timeout delle chiamate al provider. 
- Eventuali variabili aggiuntive (es. connessione MongoDB) possono essere fornite come variabili d’ambiente di sistema, se richieste dalla tua configurazione. 

## Installazione

Clona il repository: 

```bash
git clone https://github.com/ranuncolo95/gtfs_app.git
cd gtfs_app
``` 

Crea e attiva un virtualenv: 

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
``` 

Installa le dipendenze: 

```bash
pip install -r requirements.txt
``` 

Crea il file `src/.env` con i campi indicati sopra. 

## Avvio applicazione

Puoi avviare in uno di questi modi: 

Opzione A — avvio tramite script: 

```bash
python -m src.main
``` 

Opzione B — avvio diretto con uvicorn: 

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
``` 

Apri poi: 
- Home: http://127.0.0.1:8000 

## Struttura del progetto (layered)

Il progetto è organizzato per separazione dei layer: 

- `src/web/` — Web layer: endpoint FastAPI (HTTP, parsing input, response), mapping eccezioni applicative → status code HTTP. 
- `src/service/` — Service layer: use-case e orchestrazione (logica applicativa), nessuna dipendenza da FastAPI. 
- `src/data/` — Data layer: accesso a MongoDB e funzioni di calcolo/estrazione GTFS (`pandas`/`geopandas`), nessuna dipendenza da FastAPI. 
- `src/model/` — Model layer: modelli Pydantic (request/response DTO). 
- `src/core/` — Config e dipendenze: settings e Dependency Injection. 
- `src/shiny/` — App Shiny montata dentro FastAPI. 
- `src/view/` — Template e static (HTML/JS/CSS). 

## Flusso principale: calcolo rotta (high level)

L’utente compila il form in homepage (origine/destinazione/data/ora).   
Il browser invia `POST /api/calculate-route` (form data). 

Web layer (`src/web/calculate_route.py`): 
- Valida/parsa input. 
- Chiama il Service layer. 
- Ritorna una risposta HTML minimale che invia il payload via `postMessage` (per integrazione con iframe/UI). 

Service layer (`src/service/map_update.py`): 
- Implementa lo use-case “calcola rotta”. 
- Chiama il Data layer. 
- Costruisce l’output (DTO) per il frontend. 

Data layer (`src/data/...`): 
- Legge collezioni GTFS da MongoDB. 
- Seleziona trip compatibili con data/ora e fermate. 
- Costruisce GeoJSON (shape + stops) per visualizzazione mappa. 

## CRUD e MongoDB

L’applicazione usa MongoDB in modalità sola lettura (CRUD: Read): 

- Fermate (`stops`). 
- Viaggi (`trips`). 
- Sequenze e orari (`stop_times`). 
- Shape (`shapes`). 
- Calendario (`calendar`). 

Non sono previste operazioni di insert/update/delete nel flusso applicativo. 

## Licenza

MIT. 

Autore: [ranuncolo95](https://github.com/ranuncolo95) 
