import threading
import time
from datetime import datetime

class HealthMonitor:

    def __init__(self, checker, storage, light_interval=600, deep_interval=86400):
        self.checker = checker
        self.storage = storage
        self.light_interval = light_interval
        self.deep_interval = deep_interval
        self._running = False
        self._last_light = 0
        self._last_deep = 0

    def _run_loop(self):
        import time

        while self._running:
            now = time.time()

            try:
                # Light
                if now - self._last_light >= self.light_interval:
                    report = self.checker.run_light()
                    self.storage.save(report)
                    self._last_light = now

                # Deep
                if now - self._last_deep >= self.deep_interval:
                    report = self.checker.run_deep()
                    self.storage.save(report)
                    self._last_deep = now

            except Exception as e:
                print(f"[HEALTH ERROR] {e}")

            time.sleep(5)

    def start(self):
        import threading
        self._running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def stop(self):
        self._running = False
