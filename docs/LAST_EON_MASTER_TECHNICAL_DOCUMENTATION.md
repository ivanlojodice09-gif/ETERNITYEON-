# LAST EON — Documentazione tecnica

**Versione del documento:** 1.0  
**Stato:** documento di progetto; codice e hardware richiedono test nell’ambiente reale.

> LAST EON è un progetto artistico e tecnologico in evoluzione. Le architetture e gli esempi descritti qui non devono essere considerati testati solo perché sono documentati.

## 1. Panoramica

LAST EON esplora la trasformazione di segnali provenienti da sensori o flussi digitali in esperienze visive e interattive.

La ricerca si sviluppa attorno a tre concetti:

- **Segnale** — un dato rilevato o ricevuto.
- **Relazione** — i legami tra ambiente, persone e sistemi digitali.
- **Trasformazione** — il passaggio dal dato a una forma visiva, sonora o narrativa.

Tecnologie previste o utilizzate nel progetto:

- Arduino per l’acquisizione sperimentale di dati da sensori.
- Python per la lettura, l’elaborazione e il trasporto dei dati.
- OSC o WebSocket come protocolli di comunicazione.
- TouchDesigner per la visualizzazione interattiva.
- GLSL per eventuali shader.

## 2. Stato e architetture

È importante distinguere due percorsi, che non sono la stessa integrazione.

### 2.1 Percorso Arduino → OSC → TouchDesigner

Flusso previsto:

```text
Sensori → Arduino → USB/seriale → bridge Python → OSC/UDP → TouchDesigner
```

Lo sketch Arduino e `bridge/osc_bridge.py` sono pensati per questo percorso. Il formato seriale previsto è una riga di quattro valori separati da virgole:

```text
0.1234,0.2345,0.3456,0.4567
```

Il bridge invia i valori agli indirizzi:

```text
/sensor/a
/sensor/b
/sensor/c
/sensor/noise
```

Configurazione predefinita documentata:

- seriale: `9600` baud;
- host OSC: `127.0.0.1`;
- porta OSC: `10000`.

TouchDesigner deve essere configurato per ricevere i messaggi OSC sulla porta scelta e per collegare i valori ai parametri della rete visuale.

### 2.2 Percorso WebSocket → elaborazione → TouchDesigner

Un possibile percorso per dati esterni o simulati è:

```text
Sorgente dati → server WebSocket → client Python → normalizzazione
→ elaborazione/storico → TouchDesigner
```

Questo percorso è **un’architettura proposta**. Non equivale al bridge seriale/OSC e non implica che esista un collegamento attivo a un exchange o a un servizio finanziario.

Un client WebSocket riceve messaggi da un server: da solo non genera i dati e non costituisce un trading bot. Non descrivere il sistema come capace di eseguire operazioni finanziarie, se tale funzionalità non è stata realmente implementata, testata e documentata.

## 3. File del repository

La parte Arduino/OSC fa riferimento a questi file:

```text
arduino/last_eon_input.ino
bridge/osc_bridge.py
bridge/requirements.txt
scripts/create_eternityeon_network.py
```

I file di documentazione e gli esempi possono trovarsi in `docs/` ed `examples/`.

Prima di eseguire `scripts/create_eternityeon_network.py`, revisionarlo: la versione presente potrebbe contenere sia input OSC sia seriale diretta e potrebbe eliminare una rete `ETERNITYEON` già esistente. Non eseguirlo su un progetto importante senza averne prima fatto una copia e verificato il codice.

## 4. Collegamento Arduino–OSC

### 4.1 Caricare lo sketch

Apri `arduino/last_eon_input.ino` con Arduino IDE, seleziona la scheda e la porta corrette e carica lo sketch.

Lo sketch previsto trasmette quattro valori analogici a `9600` baud. Chiudi il Serial Monitor prima di avviare il bridge: normalmente un solo programma alla volta può utilizzare la stessa porta seriale.

La conversione `analogRead(...) / 1023.0` è adatta alle schede con lettura analogica a 10 bit, come molte Arduino Uno e Nano. Altre schede, per esempio alcune ESP32, possono usare una risoluzione diversa: verifica la scheda e adatta la normalizzazione prima di interpretare i valori come compresi tra `0.0` e `1.0`.

### 4.2 Installare le dipendenze

Dalla cartella principale del repository:

```powershell
python -m pip install -r bridge/requirements.txt
```

Il file `bridge/requirements.txt` deve contenere:

```text
pyserial
python-osc
```

### 4.3 Avviare il bridge

Sostituisci `COM3` con la porta effettiva di Arduino.

Windows:

```powershell
python bridge/osc_bridge.py --serial-port COM3
```

Linux, esempio:

```bash
python bridge/osc_bridge.py --serial-port /dev/ttyACM0
```

macOS, esempio:

```bash
python bridge/osc_bridge.py --serial-port /dev/cu.usbmodemXXXX
```

Il bridge usa i valori predefiniti `9600` baud e `127.0.0.1:10000`. Se necessario, specifica i parametri:

```powershell
python bridge/osc_bridge.py --serial-port COM3 --baud 9600 --host 127.0.0.1 --osc-port 10000
```

Se TouchDesigner e il bridge sono su computer diversi, sostituisci `127.0.0.1` con l’indirizzo IP del computer che esegue TouchDesigner. Verifica anche le regole del firewall per il traffico UDP sulla porta configurata.

### 4.4 Configurare TouchDesigner

Configura in TouchDesigner un ricevitore OSC, per esempio un **OSC In CHOP**, sulla stessa porta usata dal bridge. Verifica la ricezione degli indirizzi:

```text
/sensor/a
/sensor/b
/sensor/c
/sensor/noise
```

La ricezione dei messaggi non collega automaticamente i dati alla visuale: i canali devono essere mappati ai parametri degli operatori. Controlla i nomi dei canali e il comportamento nella versione di TouchDesigner installata.

## 5. Configurazione JSON

Il seguente è un **esempio JSON valido a scopo illustrativo**. Non è garantito che i nomi delle chiavi siano letti dagli script presenti nel repository; devono essere allineati al codice che carica la configurazione.

```json
{
  "project": "LAST EON",
  "version": "1.0",
  "mode": "exhibition",
  "display": {
    "width": 1920,
    "height": 1080,
    "target_fps": 60
  },
  "communication": {
    "osc_host": "127.0.0.1",
    "osc_port": 10000,
    "serial_baud_rate": 9600,
    "websocket_port": 8765
  },
  "visual": {
    "feedback": 0.9,
    "speed": 1.0
  },
  "safety": {
    "safe_mode": true
  }
}
```

Salva la configurazione con estensione `.json`, usando codifica UTF-8. Prima di collegarla a un runtime, verifica che il programma utilizzi effettivamente queste chiavi e gestisca gli errori di file o di formato.

## 6. WebSocket, elaborazione e memoria

Una possibile organizzazione software è:

```text
Client WebSocket → normalizzazione → elaborazione dello stato
→ eventuale storico limitato → collegamento a TouchDesigner
```

Principi utili per un’implementazione:

- usare buffer limitati, ad esempio `deque(maxlen=...)`, per evitare una crescita senza limiti dello storico;
- limitare dimensione e numero di messaggi in coda;
- implementare riconnessione con attesa progressiva e un limite massimo;
- evitare di accumulare messaggi mentre la connessione è interrotta se basta conservare l’ultimo valore;
- mantenere la comunicazione di rete fuori dal loop grafico principale, se questo evita blocchi dell’interfaccia;
- acquisire misure di memoria, CPU e GPU sul computer e sul progetto effettivi.

Il numero di particelle, la risoluzione, il frame rate e il costo degli shader dipendono dall’hardware e dalla rete TouchDesigner. Stime di RAM o VRAM non sono garanzie di prestazioni: misurale con il progetto reale prima di un’esibizione.

## 7. GLSL e visualizzazione

Gli shader GLSL possono trasformare i canali ricevuti in variazioni di colore, movimento o intensità. Prima di usarli, verifica:

- versione GLSL e formato richiesti dal GLSL TOP della versione TouchDesigner installata;
- dichiarazioni di input e output richieste dall’operatore;
- nomi e tipi degli uniform;
- compatibilità della risoluzione e del carico GPU.

Un frammento GLSL copiato da una descrizione o da una nota non è necessariamente compilabile in TouchDesigner senza adattamenti.

## 8. Arduino e dispositivi fisici

Un eventuale collegamento a relè, pompa o altro attuatore richiede una verifica separata. Il timeout implementato nel software non sostituisce le protezioni elettriche e meccaniche indipendenti.

Prima di collegare un attuatore:

- verifica tensioni, correnti, isolamento e compatibilità del modulo;
- prevedi uno stato di avvio e di errore **spento**;
- prova prima con il carico scollegato o con un indicatore non pericoloso;
- installa protezioni hardware indipendenti adeguate al carico;
- calibra i sensori e verifica il comportamento in caso di disconnessione o blocco;
- non lasciare una pompa o un altro attuatore incustodito durante i test.

Il codice Arduino o il cablaggio descritto in una bozza non devono essere considerati sicuri finché non sono stati controllati e provati sull’hardware specifico.

## 9. PowerShell e generazione dei file

Il testo PowerShell ricevuto in precedenza è corrotto e contiene nomi di variabili e contenuti generati non coerenti. **Non salvarlo né eseguirlo come `setup_last_eon.ps1` senza riscriverlo e provarlo.**

Quando uno script di setup sarà revisionato, eseguilo prima su una cartella di prova e controlla i file creati prima di copiarli nel repository. L’opzione `-ExecutionPolicy Bypass` non corregge errori nello script e non ne verifica la sicurezza.

## 10. Checklist di verifica

Prima di dichiarare funzionante l’installazione:

- [ ] Lo sketch compila per la scheda selezionata.
- [ ] La porta seriale e il baud rate sono corretti.
- [ ] Arduino produce righe con quattro valori separati da virgole.
- [ ] Il bridge si avvia e legge la porta senza errori.
- [ ] TouchDesigner ascolta sulla porta OSC corretta.
- [ ] Arrivano tutti e quattro gli indirizzi OSC attesi.
- [ ] I canali ricevuti sono mappati ai parametri visuali desiderati.
- [ ] Il progetto TouchDesigner è stato salvato e riaperto per una prova.
- [ ] Hardware, carichi e protezioni sono stati provati separatamente e in sicurezza.
- [ ] Le prestazioni sono state misurate sul computer di destinazione.

## 11. Licenza e pubblicazione

Prima di descrivere il progetto come open source, aggiungi una licenza riconosciuta e il relativo testo nel file `LICENSE`. Una frase informale come “Free Knowledge” esprime un’intenzione, ma da sola non definisce i permessi di copia, modifica e ridistribuzione.

Non includere nel repository chiavi API, password, token o credenziali. Per un’integrazione finanziaria, usa dati di test e documenta chiaramente limiti, rischi e funzionalità effettivamente implementate.

## 12. Stato del documento

Questa documentazione descrive il flusso Arduino/OSC e una possibile architettura WebSocket. **Non certifica** che tutti gli script, gli shader, il setup PowerShell o il cablaggio siano eseguibili o testati.

Aggiorna questa pagina quando codice e configurazioni vengono effettivamente verificati, indicando ambiente, versione dei programmi e risultati dei test.