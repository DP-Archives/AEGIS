"""
Android entry point for AEGIS.
Adapted from main.py for Android/Kivy.
Supports wake word, background service, phone control, screen time limiter.
"""
import platform
import sys
from pathlib import Path

# Detect Android
IS_ANDROID = platform.system().lower() == "android" or "android" in sys.platform.lower()

# Basic imports
import asyncio
import threading

# Core modules
from memory.config_manager import get_gemini_key, is_configured, get_voice
from core.wake_word import WakeWordDetector, get_wake_word
from core.background_service import start_service, add_background_task
from actions.screen_time_limiter import start_monitor, start_session, end_session, enable_limit
from actions.phone_control import control_volume

BASE_DIR = Path(__file__).resolve().parent

def init_android_app():
    print("[AEGIS Android] Initialising...")
    if not is_configured():
        print("[AEGIS Android] Not configured – please set Gemini API key in config/api_keys.json")
        return False
    
    # Start background service
    start_service()
    start_monitor()
    start_session()
    
    # Wake word detector
    def on_wake():
        print(f"[WakeWord] Detected wake word: {get_wake_word()}")
        # Trigger listening
    
    detector = WakeWordDetector(callback=on_wake)
    detector.start()
    
    print("[AEGIS Android] Ready")
    return True

if __name__ == "__main__":
    # On Android, this would be launched by the foreground service
    init_android_app()
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        end_session()
