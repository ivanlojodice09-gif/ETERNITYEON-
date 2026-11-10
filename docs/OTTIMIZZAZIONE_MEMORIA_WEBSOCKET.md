# LAST EON — Ottimizzazione Memoria & Integrazione WebSocket

Questa nota raccoglie le linee guida operative per il runtime di LAST EON in exhibition, con focus su:
- DataCore e gestione della history in RAM
- TouchDesigner e memoria GPU
- runtime SAFE_MODE
- WebSocket client e backpressure

## 1. Vincolo critico: memoria

LAST EON opera a 120 fps su LED wall 3840x1080 con 50.000+ particelle e feedback. In questo contesto, la memoria è il vincolo critico:
- CPU RAM
- GPU VRAM
- WebSocket buffer in memoria

Il target operativo è:
- CPU < 80%
- GPU < 85%
- RAM < 90%
- temperatura < 85°C

## 2. DataCore: history e stato

### Principi
- `max_history` va trattato come soft limit (default 10.000 stati).
- Oltre il limite, usare trim FIFO.
- Tenere in RAM solo la finestra recente utile ai trend.
- `export_history()` su disco, non in RAM continua.
- Snapshot solo su eventi critici: calibratura, SAFE_MODE, shutdown.
- Non fare dump di stato a ogni frame a 60 fps.

### Dimensione tipica di uno stato
Uno stato può essere rappresentato come:
- 4 float
- timestamp
- metadata minima

In pratica, un singolo stato occupa circa 40–60 byte in forma compattata. Con 10.000 stati si ottiene circa 0.5–0.6 MB in RAM, ma l’overhead Python e i dizionari possono far crescere il valore reale.

### Best practice
- Mantenere `history` come deque con `maxlen` per evitare trim manuale e allocazioni ripetute.
- Per i trend, usare buffer circolare (ring buffer) e calcolare il valore su una finestra fissa.
- `get_trend(window=30)` è preferibile a scansione completa della history ogni frame.
- I dati storici lunghi vanno esportati su disco.

## 3. TouchDesigner: GPU e feedback

### Riferimenti operativi
- `particle_count` va limitato; 50.000 particelle è già alto. In exhibition si possono testare 20.000–30.000.
- `Feedback TOP` a 0.96 è aggressivo. Valori inferiori riducono accumulo e consumo di VRAM.
- Evitare risoluzioni variabili per non frammentare la VRAM.
- Fissare la risoluzione di output a 3840x1080.
- Usare Probe e Performance Monitor (Alt+Y) per individuare leak.
- Fare `Free Extra GPU Memory` sui TOP quando la risoluzione cresce o diminuisce.
- Preferire TOP/GLSL (parallel su GPU) a CHOP lunghi (sequenziali su CPU).
- Usare instancing e Particle POP (GPU) invece di SOP particle classici se possibile.
- Disattivare viewer non necessari in Perform Mode.

### Nota importante
Il feedback e le risoluzioni dinamiche sono tra i maggiori fattori di crescita di VRAM. La stabilità dell’eshibition è ottenuta con un setup rigido e prevedibile.

## 4. Runtime e SAFE_MODE

### Regole di sicurezza
- CPU < 80%
- GPU < 85%
- RAM < 90%
- Temperatura < 85°C

In `SAFE_MODE`:
- ridurre `particle_count`
- abbassare il feedback
- disabilitare attuatori e sottosistemi non essenziali
- evitare allocazioni di nuova memoria nel loop a 60 fps
- riutilizzare i buffer
- fare `json.load()` solo su hot-reload, non ogni frame

## 5. WebSocket: buffer e backpressure

WebSocket è il canale real-time originario di LAST EON. Trasporta tick, sensori, dati scientifici e simulazioni.

### Requisiti per il runtime
- connettività persistente con reconnect automatico
- exponential backoff + jitter
- payload piccoli e frequenti (JSON o binario leggero)
- normalizzazione immediata in `NetworkCore` (0–1)
- timeout e heartbeat per rilevare connessioni zombie
- nessuna crescita illimitata della coda durante disconnessione

### Best practice
- `max_queue` basso, ad esempio 8–16 frame, per attivare backpressure precoce
- `max_size` dei messaggi limitato, ad esempio 64 KiB se i payload sono piccoli
- drop o ring buffer in caso di disconnessione
- `write_limit` contenuto per non ritardare il backpressure

## 6. Footprint tipico in Exhibition Mode

Stime indicative:
- DataCore history (10k): ~0.6 MB RAM
- Python runtime + libs: ~80–150 MB
- TouchDesigner network con 50k particelle: ~1.5–3 GB VRAM, dipende da shader e feedback
- Framebuffer 3840x1080: ~50–80 MB VRAM per layer
- WebSocket buffers: pochi MB con `max_queue` contenuto

Target:
- restare sotto il 90% di RAM sistema
- restare sotto l’85% di VRAM GPU

## 7. DataCore memory-aware (esempio)

```python
from collections import deque
import time


class DataCore:
    def __init__(self, storage_path="data/", max_history=10000):
        self.history = deque(maxlen=max_history)
        self.current_state = {
            "energy": 0.0,
            "relation": 0.0,
            "complexity": 0.0,
            "time": 0.0,
        }
        self.storage = storage_path
        self._ring = [0.0] * 64
        self._ring_idx = 0

    def update_state(self, energy, relation, complexity):
        energy = max(0.0, min(1.0, float(energy)))
        relation = max(0.0, min(1.0, float(relation)))
        complexity = max(0.0, min(1.0, float(complexity)))

        self.current_state = {
            "energy": energy,
            "relation": relation,
            "complexity": complexity,
            "time": time.time(),
        }

        self.history.append(self.current_state.copy())

        # ring buffer per trend veloce
        self._ring[self._ring_idx % 64] = complexity
        self._ring_idx += 1
        return self.current_state

    def calculate_evolution(self):
        if len(self.history) < 2:
            return 0.0
        return abs(self.history[-1]["complexity"] - self.history[-2]["complexity"])

    def get_trend_fast(self):
        """Calcola una stima veloce senza copiare la history."""
        n = min(64, self._ring_idx)
        if n < 2:
            return 0.0

        last_idx = (self._ring_idx - 1) % 64
        start_idx = (self._ring_idx - n) % 64
        return (self._ring[last_idx] - self._ring[start_idx]) / max(1, n - 1)