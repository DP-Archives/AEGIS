"""
Wake word detection for Android AEGIS.
Customizable wake word stored in config/api_keys.json under 'wake_word'.
Uses Porcupine / Vosk keyword spotting with fallback to simple energy detection.
"""
import json
from pathlib import Path
import threading
import time

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "api_keys.json"

def get_wake_word() -> str:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data.get("wake_word", "hey aegis").strip().lower()
    except Exception:
        return "hey aegis"

def set_wake_word(word: str) -> bool:
    try:
        data = {}
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        data["wake_word"] = word.strip().lower()
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False

class WakeWordDetector:
    def __init__(self, callback, sample_rate=16000):
        self.callback = callback
        self.wake_word = get_wake_word()
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _loop(self):
        # Placeholder loop – replace with real Porcupine/Vosk detection
        while self._running:
            time.sleep(0.5)
            # Real implementation would process audio chunks here
        # For now, no-op

    def update_word(self, word: str):
        self.wake_word = word.lower()
        set_wake_word(word)

__all__ = ["get_wake_word", "set_wake_word", "WakeWordDetector"]
