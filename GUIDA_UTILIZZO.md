# Guida all’uso — ETERNITYEON-

Questa guida descrive i file principali della repository, come avviare la componente web e come provare il percorso prototipale Arduino → Python → OSC → TouchDesigner.

> **Stato:** prototipo. Le istruzioni descrivono il codice presente nella repository, ma non attestano che l’intero sistema sia stato collaudato con ogni scheda, computer o versione software. Verifica la configurazione nel tuo ambiente.

## Indice

- [Struttura della repository](#struttura-della-repository)
- [Prerequisiti](#prerequisiti)
- [Componente web](#componente-web)
- [Percorso Arduino–Python–OSC](#percorso-arduinopythonosc)
- [TouchDesigner](#touchdesigner)
- [Esempio DataCore](#esempio-datacore)
- [Esempio WebSocket](#esempio-websocket)
- [Script per TouchDesigner](#script-per-touchdesigner)
- [Documentazione e altri file](#documentazione-e-altri-file)
- [Problemi comuni](#problemi-comuni)
- [Sicurezza e limiti](#sicurezza-e-limiti)

## Struttura della repository

```text
ETERNITYEON-/
├── arduino/
│   └── last_eon_input.ino
├── bridge/
│   ├── osc_bridge.py
│   └── requirements.txt
├── docs/
│   ├── LAST_EON_DOCUMENTATION.md.   (nome attuale con punto finale)
│   ├── LAST_EON_MASTER_TECHNICAL_DOCUMENTATION.md
│   ├── LAST_EON_TRADING_ARCHITECTURE.md
│   ├── MASTER_DOCUMENT_LAST_EON.md
│   └── OTTIMIZZAZIONE_MEMORIA_WEBSOCKET.md
├── examples/
│   ├── datacore_memory_aware.py
│   ├── websocket_client.py
│   └── examples/
│       └── websocket_client.py      (copia dello stesso client)
├── scripts/
│   └── create_eternityeon_network.py
├── index.html
├── project.json
├── LICENSE
└── README.md
```

La repository contiene più componenti indipendenti. In particolare, la pagina web, il bridge Arduino/OSC, gli esempi WebSocket e gli script TouchDesigner non costituiscono automaticamente un unico programma.

## Prerequisiti

Per provare tutto il percorso Arduino–TouchDesigner servono:

- una scheda Arduino compatibile e collegata al computer;
- Arduino IDE per caricare lo sketch;
- Python 3;
- TouchDesigner configurato per ricevere OSC;
- sensori o segnali compatibili con gli ingressi analogici della scheda.

Per provare solo la pagina web serve un browser e Python 3, oppure un altro server l’animazione.
- `project.json` fornisce testi e dati visualizzati dalla pagina.

La pagina carica il JSON con `fetch('./project.json')`. Per questo è preferibile servirla da un server locale invece di aprire direttamente `index.html` dal file system.

### Avvio locale

Apri un terminale nella cartella principale della repository ed esegui:

```bash
python -m http.server 8000
```

Poi apri nel browser:

```text
http://localhost:8000
```

Per arrestare il server, torna al terminale e premi `Ctrl+C`.

I controlli **Intensità**, **Frequenza** e **Costanza** modificano l’animazione grafica nel canvas. Non controllano Arduino o TouchDesigner.

Se la pagina mostra i testi di riserva invece dei contenuti del JSON, controlla che `project.json` sia nella stessa cartella di `index.html` e che la console del browser non mostri errori.

## Percorso Arduino–Python–OSC

Il percorso previsto è:

```text
Input analogici → Arduino → USB/seriale → bridge Python → OSC/UDP → TouchDesigner
```

### 1. Sketch Arduino

Il file `arduino/last_eon_input.ino`:

- legge quattro ingressi analogici, `A0`–`A3`;
- invia quattro valori separati da virgole;
- termina ogni riga con un ritorno a capo;
- usa una velocità seriale di `9600` baud;
- invia un campione ogni circa 50 ms.

Esempio di riga inviata:

```text
0.1234,0.2345,0.3456,0.4567
```

Carica lo sketch con Arduino IDE dopo aver selezionato la scheda e la porta corrette. Chiudi il Serial Monitor prima di avviare il bridge, perché potrebbe occupare la porta seriale.

**Nota sulla scheda:** il codice divide le letture per `1023.0`, assumendo una risoluzione ADC a 10 bit. Controlla la risoluzione e i pin della tua scheda; in particolare, alcune configurazioni ESP32 richiedono modifiche. Non collegare tensioni superiori a quelle ammesse dagli ingressi della scheda.

### 2. Dipendenze del bridge

Il file `bridge/requirements.txt` elenca `pyserial` e `python-osc`. Dalla cartella principale installale con:

```bash
python -m pip install -r bridge/requirements.txt
```

### 3. Avvio del bridge

Il file `bridge/osc_bridge.py` legge le righe seriali, ignora quelle che non contengono esattamente quattro numeri validi e invia i valori tramite OSC.

Sostituisci il nome della porta con quello effettivo della tua scheda.

**Windows, esempio:**

```powershell
python bridge/osc_bridge.py --serial-port COM3
```

**Linux, esempio:**

```bash
python bridge/osc_bridge.py --serial-port /dev/ttyACM0
```

**macOS, esempio:**

```bash
python bridge/osc_bridge.py --serial-port /dev/cu.usbmodemXXXX
```

Parametri disponibili:

```text
--serial-port   Porta seriale della scheda (obbligatoria)
--baud          Velocità seriale; predefinita: 9600
--host          Indirizzo del computer che riceve OSC; predefinito: 127.0.0.1
--osc-port      Porta OSC; predefinita: 10000
```

Esempio con tutti i parametri:

```bash
python bridge/osc_bridge.py --serial-port COM3 --baud 9600 --host 127.0.0.1 --osc-port 10000
```

Il bridge invia questi indirizzi OSC:

```text
/sensor/a
/sensor/b
/sensor/c
/sensor/noise
```

Per fermarlo, premi `Ctrl+C`.

Se TouchDesigner è su un altro computer, sostituisci `127.0.0.1` con l’indirizzo IP di quel computer e verifica la connettività di rete e le regole del firewall per UDP.

## TouchDesigner

Per il percorso consigliato tramite bridge:

1. Avvia il bridge Python.
2. In TouchDesigner configura un **OSC In CHOP** sulla porta `10000`.
3. Verifica che arrivino i messaggi `/sensor/a`, `/sensor/b`, `/sensor/c` e `/sensor/noise`.
4. Collega i canali ricevuti ai parametri della tua rete visuale.

Il bridge invia OSC; non crea da solo una rete TouchDesigner e non configura automaticamente i nodi del progetto.

## Esempio DataCore

`examples/datacore_memory_aware.py` è un esempio Python autonomo. La classe `DataCore` mantiene uno stato corrente, una cronologia limitata e un piccolo buffer circolare per calcolare un trend.

Puoi eseguirlo dalla cartella principale con:

```bash
python examples/datacore_memory_aware.py
```

Stampa lo stato corrente, una misura di evoluzione tra gli ultimi campioni e il trend.

Questo file è un esempio separato: il bridge seriale non lo importa né lo collega automaticamente a TouchDesigner. Il parametro `storage_path` è memorizzato nell’oggetto, ma nell’implementazione presente non viene usato per salvare dati su disco.

## Esempio WebSocket

`examples/websocket_client.py` è un client di esempio che si collega all’indirizzo configurato nel file, attualmente:

```text
ws://127.0.0.1:8765
```

Il client richiede un server WebSocket raggiungibile a quell’indirizzo. La repository non fornisce, con questo file, un server WebSocket da avviare.

Il pacchetto `websockets` non è elencato in `bridge/requirements.txt`. Se vuoi provare il client, installalo separatamente:

```bash
python -m pip install websockets
```

Poi avvia il client:

```bash
python examples/websocket_client.py
```

Per usarlo con un altro server, modifica l’URI nel blocco `main()` del file. Il client riceve messaggi JSON; non è il bridge seriale/OSC e non si collega automaticamente a servizi esterni.

La copia in `examples/examples/websocket_client.py` è un duplicato presente nella repository; l’esempio principale è `examples/websocket_client.py`.

## Script per TouchDesigner

`scripts/create_eternityeon_network.py` è uno script destinato all’ambiente Python di TouchDesigner: usa funzioni e operatori TouchDesigner, come `op`, `baseCOMP` e `oscInCHOP`. Non è uno script Python generico da lanciare dal terminale.

**Attenzione:** se in `/project1` esiste già un operatore chiamato `ETERNITYEON`, lo script lo elimina prima di crearne uno nuovo. Prima di eseguirlo:

1. salva il progetto TouchDesigner;
2. crea una copia di sicurezza;
3. controlla il contenuto dello script e verifica la compatibilità con la tua versione di TouchDesigner;
4. eseguilo solo nel progetto di prova o dopo aver protetto il lavoro esistente.

Lo script crea una rete dimostrativa, ma la configurazione degli operatori e dei dispositivi può richiedere adattamenti. Non è necessario per usare il bridge OSC se hai già configurato manualmente un ricevitore OSC in TouchDesigner.

## Documentazione e altri file

- `README.md` presenta il progetto e le istruzioni essenziali.
- `docs/OTTIMIZZAZIONE_MEMORIA_WEBSOCKET.md` raccoglie note tecniche ed esempi su memoria e WebSocket.
- `docs/LAST_EON_MASTER_TECHNICAL_DOCUMENTATION.md`, `docs/MASTER_DOCUMENT_LAST_EON.md` e `docs/LAST_EON_TRADING_ARCHITECTURE.md` sono documenti di progetto: verifica le istruzioni e lo stato delle funzionalità prima di applicarle.
- `docs/LAST_EON_DOCUMENTATION.md.` ha attualmente un punto finale nel nome del file. Se il collegamento o l’apertura del file crea problemi, rinominalo rimuovendo il punto finale e aggiorna i riferimenti che lo utilizzano.
- `LICENSE` contiene le condizioni d’uso. Leggila prima di riutilizzare o distribuire codice, documentazione o materiali.
- `.gitignore` indica a Git quali file locali ignorare.

I documenti e gli esempi che descrivono WebSocket, trading, memoria o integrazioni future non dimostrano che tali sistemi siano già collegati, collaudati o pronti per la produzione.

## Problemi comuni

### La pagina non carica `project.json`

- Avvia la pagina con un server locale.
- Verifica che `index.html` e `project.json` siano nella cartella principale.
- Controlla nella console del browser se il percorso o il JSON restituisce un errore.

### Il bridge non apre la porta seriale

- Verifica il nome della porta (`COM3`, `/dev/ttyACM0` o quello corretto per il tuo sistema).
- Chiudi Arduino Serial Monitor e altri programmi che potrebbero usare la porta.
- Controlla cavo USB, permessi e selezione della scheda.

### TouchDesigner non riceve OSC

- Verifica che l’OSC In CHOP ascolti sulla porta `10000`.
- Verifica che host e porta del bridge corrispondano alla configurazione TouchDesigner.
- Se usi due computer, controlla l’indirizzo IP e il firewall.
- Controlla che il bridge abbia avviato la lettura e che la scheda invii righe nel formato previsto.

### Il client WebSocket non si collega

- Verifica che un server WebSocket sia effettivamente in esecuzione su `127.0.0.1:8765`, oppure aggiorna l’URI nel client.
- Verifica che il pacchetto `websockets` sia installato.
- Assicurati che il server invii messaggi JSON validi.

## Sicurezza e limiti

- Verifica tensioni, correnti, pin, cablaggio e protezioni prima di collegare sensori o attuatori.
- Non lasciare attuatori incustoditi durante i test.
- I dati dei sensori non sono diagnosi mediche né misure scientifiche validate.
- Non pubblicare credenziali, token, chiavi o dati personali.
- Non considerare gli esempi o gli script come sistemi pronti per la produzione senza averli prima verificati.
- Fai copie di sicurezza dei progetti prima di eseguire script che li modificano.
- Consulta `LICENSE` per le condizioni d’uso.

---

**LAST EON · Guida all’utilizzo**  
Documento descrittivo della repository: verifica sempre i file e la configurazione effettivamente presenti nel branch che stai usando.