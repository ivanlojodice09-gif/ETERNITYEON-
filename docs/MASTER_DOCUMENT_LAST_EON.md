# LAST EON — Master Document

**Versione:** 2026.1  
**Stato:** bozza tecnica da verificare con il progetto e l’hardware reali  
**Focus:** installazione interattiva che esplora la relazione tra segnali bioelettrici, ambiente e forme audiovisive  
**Tecnologie previste:** TouchDesigner, Python, GLSL, Arduino e configurazione JSON

> Questo documento descrive un’architettura e include esempi di codice. Gli esempi non sono dichiarati come già testati: nomi degli operatori TouchDesigner, parametri, porte seriali, pin e polarità del relè devono essere verificati nell’installazione effettiva.

## 1. Panoramica

LAST EON trasforma segnali acquisiti da sensori e input ambientali in elementi visivi e sonori. La struttura prevista comprende:

- **Acquisizione:** sensori collegati al sistema di elaborazione.
- **Elaborazione:** filtraggio, normalizzazione e mappatura dei dati in TouchDesigner.
- **Rendering:** composizione visuale tramite TOP e shader GLSL.
- **Controllo hardware:** comunicazione seriale con Arduino per eventuali attuatori.
- **Configurazione:** parametri esterni in un file JSON.

Il segnale GSR è influenzato da diversi fattori e non va interpretato, da solo, come misura diretta o conclusiva dello stato di una pianta o di una persona.

## 2. Struttura dei file prevista

```text
ETERNITYEON-/
├── README.md
├── index.html
├── project.json
├── docs/
│   └── MASTER_DOCUMENT_LAST_EON.md
└── examples/
    ├── datacore_memory_aware.py
    └── websocket_client.py
```

Il file di configurazione di esempio riportato sotto si chiama `config_lasteon.json`. Aggiungilo alla struttura solo se lo script TouchDesigner lo usa davvero.

## 3. Configurazione JSON

Esempio di parametri esterni per il prototipo:

```json
{
  "project": "Last Eon",
  "version": "2026.1",
  "frequencies": {
    "omega_min": 0.5,
    "omega_max": 4.0,
    "gain_factor": 2.5
  },
  "thresholds": {
    "touch_caos": 0.75,
    "stress_water": 0.20,
    "group_symbiosis": 1.5,
    "fade_speed": 0.05
  },
  "display": {
    "resolution": [3840, 1080],
    "refresh_rate": 120
  }
}
```

I valori sono iniziali e illustrativi. Calibrali in base ai sensori, alla scena, al display e all’hardware effettivamente utilizzati.

## 4. TouchDesigner: caricamento della configurazione

Esempio Python da adattare a un Text DAT o a un’estensione TouchDesigner. Gli operatori `constant_bio`, `render_final` e `window1` devono esistere nel progetto e avere i parametri previsti.

```python
import json
import os


def onStart():
    config_path = os.path.join(project.folder, "config_lasteon.json")

    if not os.path.exists(config_path):
        print("LAST EON: file config_lasteon.json non trovato.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            data = json.load(config_file)

        bio = op("constant_bio")
        render = op("render_final")
        window = op("window1")

        if bio is None or render is None or window is None:
            raise RuntimeError("Verificare gli operatori richiesti nel progetto.")

        bio.par.value0 = data["frequencies"]["gain_factor"]
        bio.par.value1 = data["thresholds"]["touch_caos"]

        width, height = data["display"]["resolution"]
        render.par.w = width
        render.par.h = height

        # Aprire la finestra solo dopo aver verificato il setup di uscita.
        window.par.winopen.pulse()
        print("LAST EON: configurazione caricata.")

    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print("LAST EON: errore nel caricamento della configurazione:", error)
```

Verifica la callback corretta per la versione di TouchDesigner in uso e controlla i nomi dei parametri nell’interfaccia del progetto.

## 5. Elaborazione del segnale

Possibile catena di lavoro in TouchDesigner, da calibrare con i dati acquisiti:

1. Leggere il segnale dai CHOP corretti per il sensore e l’interfaccia utilizzati.
2. Osservare una linea di base e normalizzare il segnale rispetto all’ambiente.
3. Applicare filtraggio e smoothing per ridurre rumore e variazioni troppo rapide.
4. Mappare il valore elaborato su parametri visuali, per esempio intensità, velocità o transizione tra stati.
5. Testare le soglie con registrazioni e input controllati prima dell’uso dal vivo.

Pseudocodice concettuale per una transizione visuale:

```python
# Esempio concettuale: adattare callback, canali e operatori al progetto.
threshold = op("constant_bio")["caos_trigger"]
target = 1.0 if value > threshold else 0.0
op("logic_transition").par.value0 = target
```

Non inviare comandi a un attuatore sulla sola base di un sensore non calibrato. Per gli attuatori servono condizioni di sicurezza indipendenti e testate.

## 6. Esempio shader GLSL

Frammento illustrativo per un GLSL TOP. Verifica la versione GLSL e le variabili e gli uniform disponibili nel progetto TouchDesigner.

```glsl
uniform float uOmega;
uniform float uTime;
uniform float uCaos;

out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    float pulse = sin(uTime * uOmega) * 0.5 + 0.5;

    float line = smoothstep(
        0.15,
        0.0,
        abs(uv.y - 0.5 + sin(uv.x * 10.0 + uTime) * (0.1 + uCaos * 0.3))
    );

    vec3 color = mix(
        vec3(0.05, 0.1, 0.4),
        vec3(1.0, 0.7, 0.2),
        clamp(uCaos, 0.0, 1.0)
    );

    fragColor = vec4(color * line * (pulse + 0.2), 1.0);
}
```

## 7. Arduino e controllo dell’attuatore

Il seguente sketch è un **esempio da banco**, non una certificazione di sicurezza. La polarità di attivazione del modulo relè può variare: verifica il datasheet e testa inizialmente senza pompa collegata. Per carichi reali, usa alimentazione, isolamento e protezioni adeguati.

```cpp
const int RELAY_PIN = 8;
const unsigned long TIMEOUT_MS = 5000;

unsigned long lastWaterTime = 0;
bool relayActive = false;

void setRelay(bool active) {
  // Verificare se il modulo relè è active-HIGH o active-LOW.
  digitalWrite(RELAY_PIN, active ? HIGH : LOW);
  relayActive = active;
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);
}

void loop() {
  while (Serial.available() > 0) {
    const char command = Serial.read();

    if (command == 'W') {
      setRelay(true);
      lastWaterTime = millis();
    } else if (command == 'S') {
      setRelay(false);
    }
  }

  if (relayActive && millis() - lastWaterTime >= TIMEOUT_MS) {
    setRelay(false);
  }
}
```

Il timeout limita la durata di una singola attivazione, ma non sostituisce un arresto d’emergenza, una protezione elettrica o una verifica dell’impianto. Un comando `W` ripetuto aggiorna il timer: considera questo comportamento durante i test.

## 8. Hardware e rendering

Configurazione riportata come ipotesi progettuale, da confermare:

- **Computer:** Asus ROG Z13.
- **Uscita video prevista:** 3840 × 1080 a 120 Hz, se supportata dall’intera catena video.
- **Sensori:** collegamento e circuito d’ingresso da definire in base al sensore reale; non collegare elettrodi o sensori direttamente a ingressi non adatti.
- **Attuatore:** eventuale pompa DC tramite modulo relè compatibile, con alimentazione separata e protezioni appropriate.
- **Pipeline visuale possibile:** noise → GLSL/Bloom → feedback → blur.

Controlla la risoluzione e la frequenza effettive, la compatibilità dei dispositivi, il cablaggio, la dissipazione e la stabilità prima dell’esibizione.

## 9. Procedura di avvio e verifica

1. Controlla cablaggi, alimentazioni e modalità di arresto dell’attuatore.
2. Avvia TouchDesigner e verifica che gli operatori e i file di configurazione siano presenti.
3. Collega Arduino e conferma la porta seriale e la velocità di comunicazione.
4. Verifica l’acquisizione dei sensori senza attivare carichi.
5. Calibra linea di base, filtri e soglie con input controllati.
6. Prova le transizioni visuali e verifica che un errore o una disconnessione lasci l’attuatore in stato sicuro.
7. Solo dopo i test, collega e prova l’attuatore secondo le specifiche del produttore e le norme applicabili.

## 10. Note di manutenzione

- Mantieni una sola versione di ciascuna sezione di codice e documenta le modifiche.
- Annota le versioni di TouchDesigner, librerie, firmware Arduino e hardware utilizzati.
- Separa codice testato, pseudocodice e parametri sperimentali.
- Non presentare misure bioelettriche come diagnosi o prova scientifica senza una metodologia validata.