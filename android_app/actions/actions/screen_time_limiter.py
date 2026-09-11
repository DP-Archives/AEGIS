"""
Screen Time Limiter / Focus Period for Android AEGIS.
Manages daily screen time caps for students to reduce distractions.
Persists settings in config/api_keys.json.
On Android, integrates with UsageStatsManager; here we provide a portable timer.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "api_keys.json"
STATE_PATH = Path(__file__).resolve().parents[1] / "memory" / "screen_time_state.json"

def _load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_config(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def is_enabled() -> bool:
    cfg = _load_config()
    return bool(cfg.get("screen_time_limit_enabled", False))

def get_limit_minutes() -> int:
    cfg = _load_config()
    return int(cfg.get("screen_time_limit_minutes", 120))

def enable_limit(enabled: bool, minutes: int | None = None) -> bool:
    cfg = _load_config()
    cfg["screen_time_limit_enabled"] = bool(enabled)
    if minutes is not None:
        cfg["screen_time_limit_minutes"] = max(5, int(minutes))
    _save_config(cfg)
    reset_daily_usage()
    return True

def _load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"date": "", "used_seconds": 0, "session_start": None}

def _save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def reset_daily_usage():
    state = _load_state()
    today = datetime.now().date().isoformat()
    if state.get("date") != today:
        state = {"date": today, "used_seconds": 0, "session_start": None}
    _save_state(state)

def start_session():
    if not is_enabled():
        return
    reset_daily_usage()
    state = _load_state()
    if state.get("session_start") is None:
        state["session_start"] = time.time()
        _save_state(state)

def end_session():
    state = _load_state()
    start = state.get("session_start")
    if start:
        used = int(time.time() - start)
        state["used_seconds"] = state.get("used_seconds", 0) + used
        state["session_start"] = None
        _save_state(state)

def get_remaining_seconds() -> int | None:
    if not is_enabled():
        return None
    reset_daily_usage()
    state = _load_state()
    used = state.get("used_seconds", 0)
    # add current session
    start = state.get("session_start")
    if start:
        used += int(time.time() - start)
    limit = get_limit_minutes() * 60
    remaining = limit - used
    return max(0, remaining)

def check_limit() -> bool:
    remaining = get_remaining_seconds()
    if remaining is None:
        return False
    return remaining <= 0

# Background monitor thread
_monitor_thread = None
_monitor_stop = threading.Event()

def _monitor_loop():
    while not _monitor_stop.is_set():
        if is_enabled() and check_limit():
            # Trigger focus lock – in real Android would show overlay/notification
            # Here we just log
            print("[ScreenTime] Focus period limit reached! Locking usage.")
        time.sleep(30)

def start_monitor():
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        return
    _monitor_stop.clear()
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()

def stop_monitor():
    _monitor_stop.set()

__all__ = ["is_enabled", "get_limit_minutes", "enable_limit", "start_session", "end_session", "get_remaining_seconds", "check_limit", "start_monitor", "stop_monitor"]
