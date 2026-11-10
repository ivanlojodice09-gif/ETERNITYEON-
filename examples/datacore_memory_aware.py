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
        """Differenza media tra gli estremi della finestra di trend."""
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