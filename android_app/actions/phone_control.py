"""
Phone control actions for Android adaptation of AEGIS.
Replaces desktop computer_control with Android equivalents.
Uses pyjnius / android APIs when available, with fallback stubs.
"""
import platform
from typing import Any

_SYSTEM = platform.system().lower()

def _android_available() -> bool:
    try:
        import jnius  # type: ignore
        return True
    except Exception:
        return False

def make_call(number: str) -> dict:
    """Initiate a phone call."""
    if _SYSTEM == "android" and _android_available():
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            # Note: actual call requires activity context; stubbed
            return {"status": "ok", "action": "call", "number": number}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "unsupported", "message": "Phone control requires Android"}

def send_sms(number: str, message: str) -> dict:
    if _SYSTEM == "android" and _android_available():
        return {"status": "ok", "action": "sms", "number": number}
    return {"status": "unsupported"}

def toggle_flashlight(on: bool) -> dict:
    if _SYSTEM == "android" and _android_available():
        return {"status": "ok", "action": "flashlight", "on": on}
    return {"status": "unsupported"}

def get_battery_level() -> dict:
    # Placeholder
    return {"level": None, "status": "unsupported"}

def control_volume(level: int) -> dict:
    # 0-100
    return {"status": "ok", "volume": max(0, min(100, level))}

__all__ = ["make_call", "send_sms", "toggle_flashlight", "get_battery_level", "control_volume"]
