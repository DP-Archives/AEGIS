"""
Background service runner for Android AEGIS.
Provides run-in-backend capability: keeps Gemini Live session alive
when UI is not in foreground, processes wake word, handles proactive checks.
"""
import threading
import time

class BackgroundService:
    def __init__(self):
        self._running = False
        self._thread = None
        self._callbacks = []

    def register_callback(self, fn):
        self._callbacks.append(fn)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[BackgroundService] Started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[BackgroundService] Stopped")

    def _loop(self):
        while self._running:
            time.sleep(1)
            # Placeholder for background processing: wake word polling,
            # proactive engine, screen time monitoring
            for cb in self._callbacks:
                try:
                    cb()
                except Exception as e:
                    print(f"[BackgroundService] Callback error: {e}")

# Singleton instance
_service = BackgroundService()

def start_service():
    _service.start()

def stop_service():
    _service.stop()

def add_background_task(fn):
    _service.register_callback(fn)

__all__ = ["start_service", "stop_service", "add_background_task", "BackgroundService"]
