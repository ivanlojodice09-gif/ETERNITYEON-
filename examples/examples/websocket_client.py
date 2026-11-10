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