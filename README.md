# gtfs_app

Un'applicazione per la gestione, visualizzazione e analisi di dati GTFS (General Transit Feed Specification), sviluppata in Python.

## Descrizione

`gtfs_app` è un progetto open source che consente di caricare, esplorare e manipolare feed GTFS, comunemente utilizzati per rappresentare dati di trasporto pubblico come orari, fermate, percorsi e agenzie. L'applicazione offre funzionalità per la validazione dei dati, l'analisi delle tratte e la visualizzazione delle informazioni tramite un'interfaccia intuitiva.

## Caratteristiche principali

- Importazione di feed GTFS (.zip)
- Esplorazione delle tabelle principali (stops, routes, trips, stop_times, calendar, agency, etc.)
- Filtri e ricerca su fermate, percorsi e viaggi
- Analisi degli orari e delle frequenze di servizio
- Esportazione dei dati filtrati o modificati
- Possibile integrazione di mappe per la visualizzazione geografica (se implementato)

## Installazione

1. Clona questo repository:
   ```bash
   git clone https://github.com/ranuncolo95/gtfs_app.git
   cd gtfs_app
   ```

2. (Opzionale) Crea un ambiente virtuale:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Utilizzo

Dopo aver installato le dipendenze, puoi avviare l'applicazione con:

```bash
python main.py
```

Segui le istruzioni a schermo per caricare un feed GTFS e iniziare l'esplorazione.

## Struttura del progetto

- `main.py`: entry point dell'applicazione
- `gtfs/`: moduli per la gestione e analisi dei dati GTFS
- `utils/`: funzioni di utilità e helper
- `data/`: (eventuale) directory per i file di esempio o output
- `requirements.txt`: elenco delle dipendenze Python

## Dipendenze principali

- Python >= 3.8
- pandas
- numpy
- (eventuale) geopandas, folium, streamlit, flask ecc.

## Contribuire

Contributi e segnalazioni di bug sono benvenuti! Apri una issue o una pull request per proporre miglioramenti o segnalare problemi.

## Licenza

Questo progetto è distribuito sotto licenza MIT.

---

**Autore:** [ranuncolo95](https://github.com/ranuncolo95)

---

## Dettaglio delle funzioni presenti in `models`

All'interno della directory `app/src/models`, le funzioni principali riguardano la logica di calcolo dei percorsi e la gestione dei dati GTFS.

### `map_updates.py`

Contiene due funzioni principali esposte come endpoint (usate tipicamente da FastAPI):

#### 1. `async def read_root(request: Request)`
Restituisce la pagina principale (`index.html`) dell'applicazione tramite le template Jinja2, passando variabili come `shiny_url`.  
**Scopo:** Visualizzazione interfaccia principale.

#### 2. `async def calculate_route(request: Request)`
Questa funzione è il cuore della logica di calcolo del percorso dati origine/destinazione.  
Le sue fasi principali sono:

- **Parsing input:** Riceve un JSON con `origin` e `destination`.
- **Recupero fermate:** Scarica tutte le fermate dal database e trova quella più vicina alla destinazione usando `get_stop_destinazione`.
- **Gestione orario:** Considera una finestra temporale di un’ora per trovare i possibili trip in arrivo alla fermata di destinazione.
- **Ricerca trip:** Trova i trip (corsa) che arrivano alla fermata di destinazione nell’intervallo di tempo specificato.
- **Recupero stop_times:** Scarica tutte le stop_times relative ai trip trovati.
- **Associazione fermata di partenza:** Tra le stop_times trovate, seleziona quella più vicina all’origine.
- **Isolamento del viaggio:** Ricava la sequenza di stop_times tra fermata di partenza e destinazione.
- **Recupero dati shape:** Dato il trip selezionato, trova lo shape (polilinea) associato e isola la porzione di shape compresa tra partenza e destinazione.
- **GeoDataFrame:** Costruisce i dati geografici (GeoJSON) sia per shape che per le fermate.
- **Restituzione risultato:** Restituisce un dizionario con tutte le info utili sulla soluzione di percorso trovata.

Gestisce anche errori restituendo HTTP 500 in caso di eccezioni.

---

### `defs.py`

#### 1. `def get_stop_destinazione(lat, lon, stops_df)`
Data una latitudine e longitudine, restituisce la fermata più vicina tra quelle disponibili in `stops_df`, calcolando la distanza con la funzione `haversine_ref_point`.

---

### Esempio di flusso per calcolo percorso

1. L’utente fornisce origine e destinazione sulla mappa.
2. Il backend tramite `calculate_route`:
   - Trova fermata reale più vicina a destinazione.
   - Trova i trip che passano da lì nell’orario richiesto.
   - Ricava il trip più adatto e la fermata di partenza più vicina.
   - Esporta shape e fermate in formato GeoJSON per la mappa.

---

### Altre note

- Le funzioni si appoggiano su MongoDB Atlas per l’accesso ai dati GTFS.
- Si fa uso intensivo di pandas e geopandas per manipolazione dati tabellari e geografici.
- Le funzioni sono pensate per essere asincrone e integrate in un framework FastAPI.

Per approfondimenti sul calcolo delle distanze o sulla struttura dati GTFS, vedi anche i commenti nei file `main.ipynb` e `defs.py`.

---

## Pattern Model-View-Controller (MVC) implementato

L'applicazione segue una struttura ispirata al pattern **Model-View-Controller (MVC)**, che separa la logica di business, la gestione delle richieste e la presentazione dei dati in componenti distinti per una migliore organizzazione e manutenibilità del codice.

### Flusso principale

1. **main.py / main.ipynb**
   - Punto di ingresso dell'applicazione.
   - Qui vengono inizializzati il server e le route principali.
   - Le richieste degli utenti (come il calcolo percorso) vengono indirizzate verso i **controller**.

2. **Cartella `controls`**
   - Contiene i **controller**, responsabili di ricevere le richieste dall'esterno (ad esempio tramite FastAPI), validare gli input e orchestrare chiamate verso i **models**.
   - Esempio:  
     Il file `app/src/controls/map_updates.py` espone funzioni asincrone come `read_root` e `calculate_route` che richiamano le rispettive funzioni nei modelli (`models`).
   - Qui si gestisce la logica di routing e il coordinamento tra view e model.

3. **Cartella `models`**
   - Qui risiede la logica di business e l'accesso ai dati.
   - Le funzioni nei moduli di `models` interagiscono direttamente con il database (MongoDB nel caso di GTFS), elaborano i dati, applicano algoritmi (ad esempio per il calcolo del percorso o delle distanze) e restituiscono strutture dati pronte per la presentazione.
   - Esempi: ricerca fermate più vicine, elaborazione delle shape, generazione di GeoJSON, ecc.

4. **View**
   - Lato backend, la view è rappresentata dai template HTML che vengono renderizzati tramite Jinja2 (es: `index.html`).
   - Questi template ricevono dati dal controller e li presentano all’utente finale, spesso integrando anche componenti frontend dinamiche (JS, mappe, ecc).

### Schema riassuntivo del flusso

```
Utente
  │
  ▼
(main.py) → ROUTE/API → (controls) → Controller → (models) → Modello/dati
  │                                              │
  └──────────────> (view) ←────────────<──────────┘
```

- **main.py**: Avvia il server e riceve le richieste.
- **controls**: Smista e gestisce la logica applicativa delle richieste.
- **models**: Implementa la logica di accesso ai dati, le operazioni di calcolo e manipolazione.
- **view**: Presenta i dati finali all’utente.

### Vantaggi della struttura

- **Separazione delle responsabilità**: Ogni componente ha un ruolo ben definito.
- **Facilità di manutenzione**: È semplice modificare la logica di business senza intaccare la presentazione.
- **Testabilità**: Le funzioni di model sono facilmente testabili in modo isolato.
- **Scalabilità**: Nuove funzionalità possono essere aggiunte in modo modulare e ordinato.

---

Questa architettura consente di mantenere il codice organizzato, chiaro e facilmente estendibile per future evoluzioni dell'applicativo.

---

## Pratiche CRUD utilizzate nell'interazione con MongoDB

Nel contesto di questa applicazione, l’interazione con il database **MongoDB** segue le tipiche pratiche CRUD (Create, Read, Update, Delete), ma – come da tua indicazione – **viene utilizzata esclusivamente l’operazione di Read**.

### Operazione utilizzata: **Read**

- **Read** (Lettura):  
  È l’unica operazione CRUD implementata nel backend. Viene utilizzata per recuperare dati dalle collezioni MongoDB, come fermate (`cagliari_ctm_stops`), percorsi (`cagliari_ctm_trips`), shape (`cagliari_ctm_shapes`), e orari (`cagliari_ctm_stop_times`).
  
  Le query vengono effettuate tipicamente tramite il metodo `.find()` del driver PyMongo. Esempi di utilizzo:
  ```python
  # Lettura di tutte le fermate
  stops_df = pd.DataFrame(list(db["cagliari_ctm_stops"].find()))

  # Ricerca shape associate a uno specifico shape_id
  shapes_cursor = db["cagliari_ctm_shapes"].find(
      {"shape_id": shape_id},
      {"_id": 0, "shape_id": 1, "shape_pt_lat": 1, "shape_pt_lon": 1, "shape_pt_sequence": 1}
  ).sort([("shape_pt_sequence", ASCENDING)])
  df_shapes_filtered = pd.DataFrame(list(shapes_cursor))
  ```

  Le query possono essere filtrate usando parametri di ricerca e ordinamento, e i dati vengono poi convertiti in DataFrame per ulteriori elaborazioni.

### Operazioni **non** utilizzate

- **Create** (Creazione):  
  Non vengono effettuati inserimenti di nuovi documenti (no `.insert_one()` o `.insert_many()`).

- **Update** (Aggiornamento):  
  Nessuna modifica ai dati esistenti (no `.update_one()`, `.update_many()`).

- **Delete** (Cancellazione):  
  Nessuna eliminazione di dati (no `.delete_one()`, `.delete_many()`).

---

### Vantaggi di questa scelta

- **Sicurezza dei dati:**  
  Nessuna possibilità di modificare accidentalmente i dati GTFS originali, che vengono solo consultati.
- **Semplicità:**  
  La logica del backend è focalizzata sull’analisi e la presentazione del dato, non sulla sua gestione o persistenza.

---

### Conclusione

L’applicazione funziona come un “lettore intelligente” dei dati GTFS su MongoDB, garantendo integrità e sicurezza del dato originale grazie all’utilizzo esclusivo di operazioni di **Read**.