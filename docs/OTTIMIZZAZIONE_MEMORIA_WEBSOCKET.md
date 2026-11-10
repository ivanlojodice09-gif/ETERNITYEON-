# LAST EON — Ottimizzazione Memoria & Integrazione WebSocket

Analisi tecnica e codici di esempio, versione 2026.1.

## 1. Ottimizzazione della memoria

LAST EON è pensato per operare a 120 fps su un LED wall 3840×1080 con 50.000+ particelle e feedback. La memoria — RAM di sistema e VRAM della GPU — è un vincolo critico. Le aree principali sono DataCore (Python), rete TouchDesigner e buffer WebSocket.

### DataCore: history e stato

- Impostare `max_history` (default: 10.000 stati) e conservare solo gli stati più recenti, con rimozione FIFO.
- Una stima compatta di uno stato è circa 40–60 byte; 10.000 stati sarebbero circa 0,5–0,6 MB in formato compatto. In Python l’uso effettivo può essere maggiore per l’overhead di dizionari e oggetti.
- Esportare la cronologia su disco; in RAM mantenere la finestra recente utile ai trend.
- Usare una finestra limitata, per esempio `get_trend(window=30)`, invece di scandire tutta la cronologia a ogni frame.
- Salvare snapshot solo in occasione di eventi, come calibrazione, SAFE_MODE o arresto, non a ogni frame.

### TouchDesigner: GPU, particelle e feedback

- Limitare `particle_count`: 50.000 è già elevato; in exhibition si possono testare 20.000–30.000.
- Un valore di feedback TOP pari a `0.96` può essere aggressivo; valori inferiori riducono l’accumulo visivo.
- Mantenere una risoluzione fissa di 3840×1080, evitando cambi continui di risoluzione.
- Usare Probe (Palette) e Performance Monitor (Alt+Y) per individuare colli di bottiglia o possibili perdite di risorse.
- Valutare `Free Extra GPU Memory` sui TOP dopo variazioni di risoluzione.
- Preferire TOP/GLSL per elaborazioni parallele su GPU quando appropriato.
- Valutare instancing e Particle POP invece di sistemi SOP tradizionali, se compatibili con il progetto.
- Disattivare i viewer non necessari in Perform Mode.

### Runtime e SAFE_MODE

Soglie indicative da verificare sulla macchina reale:

- CPU: sotto l’80%
- GPU: sotto l’85%
- RAM: sotto il 90%
- Temperatura: sotto gli 85 °C

In `SAFE_MODE`:

- ridurre il numero di particelle;
- abbassare il feedback;
- disabilitare attuatori e sottosistemi non essenziali;
- riutilizzare i buffer e limitare le allocazioni nel loop;
- eseguire `json.load()` solo al caricamento o durante un hot-reload, non a ogni frame.

### Buffer WebSocket

- Impostare `max_queue` su un valore contenuto, per esempio 8–16.
- Limitare `max_size` se i payload sono piccoli, per esempio a 64 KiB.
- Evitare code illimitate durante una disconnessione; usare drop o un ring buffer limitato.
- Configurare il limite di scrittura (`write_limit`) in base alla versione della libreria e al carico.

### Stime indicative in Exhibition Mode

- DataCore history (10.000 stati): circa 0,6 MB, stima compatta; l’uso reale di Python può essere superiore.
- Runtime Python e librerie: circa 80–150 MB.
- Rete TouchDesigner con 50.000 particelle: circa 1,5–3 GB di VRAM, secondo shader e feedback.
- Framebuffer 3840×1080: circa 50–80 MB di VRAM per layer.
- Buffer WebSocket: pochi MB se le code sono limitate.

Le stime dipendono dall’hardware e dalla configurazione: misurare il consumo sul sistema effettivo.

## 2. Esempio DataCore memory-aware

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

        self._ring[self._ring_idx % len(self._ring)] = complexity
        self._ring_idx += 1
        return self.current_state

    def calculate_evolution(self):
        if len(self.history) < 2:
            return 0.0
        return abs(
            self.history[-1]["complexity"]
            - self.history[-2]["complexity"]
        )

    def get_trend_fast(self):
        """Differenza media per campione tra gli estremi degli ultimi campioni."""
        n = min(len(self._ring), self._ring_idx)
        if n < 2:
            return 0.0

        last_idx = (self._ring_idx - 1) % len(self._ring)
        start_idx = (self._ring_idx - n) % len(self._ring)
        return (
            self._ring[last_idx] - self._ring[start_idx]
        ) / (n - 1)


if __name__ == "__main__":
    core = DataCore()
    for i in range(10):
        core.update_state(0.1 * i, 0.2 * i, 0.3 * i)

    print(core.current_state)
    print("evolution:", core.calculate_evolution())
    print("trend:", core.get_trend_fast())
```

Il ring buffer limita la memoria usata per i campioni del trend. `get_trend_fast()` calcola la differenza media tra il primo e l’ultimo campione della finestra; non è una regressione statistica.

## 3. Architettura e flusso WebSocket

WebSocket può trasportare tick, sensori, dati scientifici e simulazioni.

Flusso logico:

`SOURCE -> WS server -> LAST EON client (asyncio) -> NetworkCore.receive_data() -> normalize -> DataCore/Symbiosis -> Runtime.apply_parameters() -> TouchDesigner`

Esempio di messaggio:

```json
{
  "time": 1710000000.123,
  "type": "tick",
  "symbol": "DATA",
  "value": 123.45,
  "meta": {
    "source": "ws_bridge"
  }
}
```

Esempio di dati normalizzati:

```json
{
  "bio_energy": 0.65,
  "environment": 0.40,
  "external_signal": 0.80
}
```

## 4. Esempio WebSocket client

Questo esempio richiede il pacchetto `websockets`. L’API può variare in base alla versione installata; verifica la compatibilità prima di usarlo in produzione.

```python
import asyncio
import json
import random
import time
from typing import Any, Callable, Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
except ImportError:
    websockets = None
    ConnectionClosed = Exception


class WebSocketClient:
    """Client asyncio con reconnect, backoff e ring buffer limitato."""

    def __init__(
        self,
        uri: str,
        on_message: Optional[Callable[[dict], None]] = None,
        max_queue: int = 16,
        max_size: int = 64 * 1024,
    ):
        self.uri = uri
        self.on_message = on_message
        self.max_queue = max_queue
        self.max_size = max_size
        self.running = False
        self.connected = False
        self._last_msg_time = 0.0
        self._ring = []
        self._ring_max = 32

    async def _handle_message(self, raw):
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return

        self._last_msg_time = time.time()
        self._ring.append(data)
        if len(self._ring) > self._ring_max:
            self._ring.pop(0)

        if self.on_message is not None:
            self.on_message(data)

    async def connect_with_backoff(self):
        delay = 1.0

        while self.running:
            try:
                async with websockets.connect(
                    self.uri,
                    max_size=self.max_size,
                    max_queue=self.max_queue,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    self.connected = True
                    delay = 1.0
                    print(f"[WS] connected to {self.uri}")

                    async for message in ws:
                        if not self.running:
                            break
                        await self._handle_message(message)

            except (ConnectionClosed, OSError, Exception) as exc:
                self.connected = False
                if not self.running:
                    break

                wait = min(delay + random.uniform(0, delay * 0.5), 30.0)
                print(f"[WS] disconnected ({exc}), retry in {wait:.1f}s")
                await asyncio.sleep(wait)
                delay = min(delay * 2, 30.0)

            finally:
                self.connected = False

    async def run(self):
        if websockets is None:
            raise RuntimeError("Installa il pacchetto richiesto: pip install websockets")
        self.running = True
        await self.connect_with_backoff()

    def stop(self):
        self.running = False

    def status(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "uri": self.uri,
            "last_msg": self._last_msg_time,
            "ring_len": len(self._ring),
        }


async def main():
    client = WebSocketClient(
        uri="ws://127.0.0.1:8765",
        on_message=lambda payload: print("received:", payload),
        max_queue=12,
        max_size=32 * 1024,
    )
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("WebSocket client stopped.")
```

## 5. Esempio di integrazione con NetworkCore e TouchDesigner

Questo è uno schema: `network`, `data_core` e gli operatori TouchDesigner devono essere definiti nel progetto.

```python
def on_ws_message(payload: dict):
    normalized = network.receive_data("WEBSOCKET", payload)
    if not normalized:
        return

    energy = normalized.get("value", normalized.get("bio_energy", 0.0))
    if energy > 1.0:
        energy = min(1.0, energy / 1000.0)

    environment = normalized.get("environment", 0.3)
    interaction = normalized.get("interaction", 0.2)
    complexity = min(
        1.0,
        energy * 0.5 + environment * 0.3 + interaction * 0.2,
    )

    data_core.update_state(energy, interaction, complexity)
    evolution = data_core.calculate_evolution()

    # Esempio di mapping TouchDesigner: adattare i path al proprio progetto.
    # op("/project1/INPUT/bio_constant").par.value0 = energy
    # op("/project1/INPUT/bio_constant").par.value1 = environment
    # op("/project1/INPUT/bio_constant").par.value2 = complexity
    # op("/project1/INPUT/bio_constant").par.value3 = evolution
```

## 6. Best practice WebSocket e memoria

- Usare `max_queue` contenuto, per esempio 8–16, e misurare latenza e throughput.
- Se vale la regola “l’ultimo valore vince”, scartare i dati ormai obsoleti invece di accumularli.
- Usare ping/pong per rilevare connessioni non più attive.
- Applicare jitter al backoff per distribuire i tentativi di riconnessione.
- Se il loop TouchDesigner non deve bloccarsi, valutare un thread o processo dedicato e definire con attenzione la comunicazione tra processi.
- In SAFE_MODE, fermare o ridurre la frequenza dei messaggi secondo le esigenze del sistema.
- Monitorare `last_msg` e `ring_len` per diagnosticare interruzioni o ritardi.

---

**LAST EON · Memory Optimization · WebSocket · 2026.1**