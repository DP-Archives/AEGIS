"""AEGIS Android App — real assistant (Gemini chat + voice), same brain as PC."""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import platform
from pathlib import Path
import json
import threading

# ── Phone-shaped preview on PC ────────────────────────────────────────────────
if platform not in ("android", "ios"):
    Window.size = (405, 720)

# ── Paths: config/core live next to main.py (packed into the APK) ─────────────
HERE = Path(__file__).resolve().parent
LOGO = HERE / "assets" / "logo.png"
if not LOGO.exists():
    LOGO = HERE.parent / "logo.png"

def _load_config():
    paths = [HERE.parent / "config" / "api_keys.json", HERE / "config" / "api_keys.json"]
    if platform == "android":
        try:
            from jnius import autoclass
            files = autoclass("org.kivy.python.PythonActivity").mActivity.getFilesDir().getAbsolutePath()
            # saved key lives in the writable data dir — highest priority on Android
            paths.insert(0, Path(files) / "config" / "api_keys.json")
        except Exception:
            pass
    for p in paths:
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                return cfg, p
        except Exception:
            continue
    return {}, paths[0]

CONFIG, CONFIG_PATH = _load_config()

def _save_config_path():
    """Where the key can actually be written: data dir on Android, HERE on PC."""
    if platform == "android":
        try:
            from jnius import autoclass
            files = autoclass("org.kivy.python.PythonActivity").mActivity.getFilesDir().getAbsolutePath()
            return Path(files) / "config" / "api_keys.json"
        except Exception:
            pass
    return CONFIG_PATH

def _system_prompt():
    """Same personality as the PC app — reuse core/prompt.txt."""
    for p in (HERE / "core" / "prompt.txt", HERE.parent / "core" / "prompt.txt"):
        try:
            txt = p.read_text(encoding="utf-8").strip()
            if txt:
                return txt[:6000]
        except Exception:
            continue
    return ("You are AEGIS, a helpful, proactive AI assistant. Be concise, "
            "friendly and direct. The user is on their phone.")

# ── PC theme colors (ui.py palette) ───────────────────────────────────────────
BG      = (0, 0.024, 0.039, 1)        # #00060a
PANEL   = (0.004, 0.051, 0.078, 1)    # #010d14
BORDER  = (0.051, 0.2, 0.278, 1)      # #0d3347
CYAN    = (0, 0.831, 1, 1)            # #00d4ff
TEXT    = (0.561, 0.988, 1, 1)        # #8ffcff
WHITE   = (0.847, 0.973, 1, 1)        # #d8f8ff
DIM     = (0.227, 0.541, 0.604, 1)    # #3a8a9a
USER_BG = (0.051, 0.16, 0.28, 1)

# ── Gemini REST client (requests — works on PC and Android) ───────────────────
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
_working_model = CONFIG.get("gemini_model") or None

def gemini_chat(history, key):
    """Blocking network call. history = [{'role','text'},…] → (text, model, error)."""
    import requests
    global _working_model
    models = ([_working_model] if _working_model else []) + \
             [m for m in MODELS if m != _working_model]
    contents = [{"role": "user" if h["role"] == "user" else "model",
                 "parts": [{"text": h["text"]}]} for h in history]
    body = {
        "systemInstruction": {"parts": [{"text": _system_prompt()}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    last_err = "unknown error"
    for model in models:
        try:
            r = requests.post(API.format(model), params={"key": key}, json=body, timeout=45)
            if r.status_code == 200:
                _working_model = model
                data = r.json()
                parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    return text, model, None
                last_err = "empty response"
            elif r.status_code in (400, 403):
                try:
                    msg = r.json().get("error", {}).get("message", r.text[:200])
                except Exception:
                    msg = r.text[:200]
                return None, model, f"API key problem: {msg}"
            else:
                last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
    return None, None, last_err

# ── Android TTS (speaks replies on the phone; silent on PC) ───────────────────
_tts = {"obj": None}

def speak(text):
    if platform != "android":
        return
    try:
        from jnius import autoclass
        if _tts["obj"] is None:
            Locale = autoclass("java.util.Locale")
            TTS = autoclass("android.speech.tts.TextToSpeech")
            activity = autoclass("org.kivy.python.PythonActivity").mActivity
            _tts["obj"] = TTS(activity, None)
            _tts["obj"].setLanguage(Locale.US)
        _tts["obj"].speak(text[:600], _tts["obj"].QUEUE_ADD, None, None)
    except Exception as e:
        print(f"[TTS] {e}")


class RoundedCard(FloatLayout):
    """FloatLayout with a rounded background — children center reliably."""
    def __init__(self, bg=(1, 1, 1, 1), radius=14, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*bg)
            self._rr = RoundedRectangle(radius=[dp(radius)], pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size


class ChatBubble(AnchorLayout):
    """One message bubble. Background drawn on the label's own canvas → always aligned."""
    def __init__(self, text, is_user, row_w, **kw):
        super().__init__(anchor_x="right" if is_user else "left",
                         size_hint=(1, None), height=dp(40), **kw)
        self.lbl = Label(
            text=text, font_size="15sp", halign="left", valign="middle",
            color=WHITE if is_user else TEXT,
            size_hint=(None, None), padding=(dp(13), dp(9)), markup=False,
        )
        self.max_w = max(dp(60), row_w * 0.82)
        self.add_widget(self.lbl)
        with self.lbl.canvas.before:
            Color(*(USER_BG if is_user else PANEL))
            self.rr = RoundedRectangle(radius=[dp(14)], pos=self.lbl.pos, size=self.lbl.size)
        self.lbl.bind(pos=self._upd, size=self._upd)
        self.lbl.bind(texture_size=self._fit)
        self.lbl.text_size = (self.max_w, None)

    def _upd(self, *a):
        self.rr.pos = self.lbl.pos
        self.rr.size = self.lbl.size

    def _fit(self, inst, ts):
        inst.size = inst.texture_size
        self.height = inst.texture_size[1] + dp(8)


class LoadingScreen(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._upd, pos=self._upd)

        # Logo card — FloatLayout wrapper guarantees true centering
        card_zone = FloatLayout(size_hint=(1, 0.42), pos_hint={"center_y": 0.62})
        card = RoundedCard(bg=(1, 1, 1, 1), radius=16,
                           size=(dp(190), dp(190)),
                           pos_hint={"center_x": 0.5, "center_y": 0.5})
        if LOGO.exists():
            card.add_widget(Image(source=str(LOGO), fit_mode="contain",
                                  size_hint=(0.78, 0.78),
                                  pos_hint={"center_x": 0.5, "center_y": 0.5}))
        card_zone.add_widget(card)
        self.add_widget(card_zone)

        bottom = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(170),
                           pos_hint={"center_y": 0.18}, spacing=dp(14), padding=(dp(40), 0))
        bottom.add_widget(Label(text="AEGIS", font_size="34sp", bold=True, color=CYAN))
        bottom.add_widget(Label(text="Initializing AI Assistant…", font_size="14sp",
                                color=(0.58, 0.72, 0.8, 1)))
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        self.progress.background_color = (0.01, 0.07, 0.12, 1)
        self.progress.color = CYAN
        bottom.add_widget(self.progress)
        bottom.add_widget(Label(text="Powerful • Private • Yours", font_size="12sp", color=DIM))
        self.add_widget(bottom)

    def _upd(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ChatScreen(FloatLayout):
    """Real assistant: Gemini chat (same brain as PC) + mic + TTS on Android."""

    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.busy = False
        self.history = []
        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._upd, pos=self._upd)

        root = BoxLayout(orientation="vertical", spacing=dp(8),
                         padding=(dp(10), dp(10), dp(10), dp(10)))

        # ── Header ──
        header = BoxLayout(size_hint=(1, None), height=dp(46), spacing=dp(8))
        header.add_widget(Label(text="AEGIS", font_size="20sp", bold=True,
                                color=CYAN, size_hint_x=None, width=dp(88)))
        self.status = Label(text="ready", font_size="11sp", color=DIM)
        header.add_widget(self.status)
        gear = Button(text="⚙", font_size="18sp", size_hint_x=None, width=dp(46),
                      background_normal="", background_down="",
                      background_color=PANEL, color=DIM, bold=True)
        gear.bind(on_press=self._show_setup)
        header.add_widget(gear)
        mic = Button(text="🎤", font_size="17sp", size_hint_x=None, width=dp(46),
                     background_normal="", background_down="",
                     background_color=PANEL, color=CYAN, bold=True)
        mic.bind(on_press=self.on_mic)
        header.add_widget(mic)
        root.add_widget(header)
        root.add_widget(self._hline())

        # ── Chat feed ──
        self.feed = GridLayout(cols=1, size_hint=(1, None), height=dp(1),
                               padding=(0, dp(6)), spacing=dp(10))
        self.feed.bind(minimum_height=self.feed.setter("height"))
        scroll = ScrollView(bar_width=dp(3), do_scroll_x=False)
        scroll.add_widget(self.feed)
        root.add_widget(scroll)

        # ── Input bar ──
        bar = BoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(8))
        self.input = TextInput(
            multiline=False, font_size="15sp", background_normal="",
            background_active="", background_color=PANEL,
            foreground_color=WHITE, cursor_color=CYAN,
            hint_text="Ask AEGIS anything…", hint_text_color=DIM,
            padding=(dp(12), dp(13)), size_hint_x=0.78,
        )
        self.input.bind(on_text_validate=lambda *a: self.send())
        bar.add_widget(self.input)
        send = Button(text="➤", font_size="18sp", bold=True, size_hint_x=None,
                      width=dp(52), background_normal="", background_down="",
                      background_color=(0, 0.25, 0.35, 1), color=CYAN)
        send.bind(on_press=lambda *a: self.send())
        bar.add_widget(send)
        root.add_widget(bar)
        self.add_widget(root)

        # ── Startup message ──
        key = CONFIG.get("gemini_api_key", "").strip()
        if key:
            self.set_status("GEMINI • READY", CYAN)
            self.add_bubble("AEGIS online. Ask me anything.", is_user=False)
        else:
            self.set_status("SETUP NEEDED", (1, 0.55, 0.2, 1))
            self.add_bubble(
                "Welcome to AEGIS!\n\nAdd your Gemini API key to activate "
                "the assistant:\n" + str(CONFIG_PATH) +
                "\n\n\"gemini_api_key\": \"YOUR_KEY\"\n\n"
                "Free key: aistudio.google.com/apikey\nThen restart the app.",
                is_user=False)

    def _upd(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _hline(self):
        line = BoxLayout(size_hint=(1, None), height=dp(1))
        with line.canvas.before:
            Color(*BORDER)
            Rectangle(pos=line.pos, size=line.size)
        return line

    # ── UI helpers (main thread) ──
    def set_status(self, txt, color):
        self.status.text, self.status.color = txt, color

    def add_bubble(self, text, is_user):
        b = ChatBubble(text, is_user, self.width)
        self.feed.add_widget(b)
        Clock.schedule_once(lambda dt: self._autoscroll(), 0.05)

    def _autoscroll(self):
        parent = self.feed.parent
        if parent:
            parent.scroll_y = 0

    # ── Sending ──
    def send(self, *a):
        txt = self.input.text.strip()
        if not txt or self.busy:
            return
        self.input.text = ""
        self.add_bubble(txt, True)
        self.history.append({"role": "user", "text": txt})
        key = CONFIG.get("gemini_api_key", "").strip()
        if not key:
            self.add_bubble("No API key yet — see the setup message above.", False)
            return
        self.busy = True
        self.set_status("thinking…", DIM)
        threading.Thread(target=self._worker, args=(key,), daemon=True).start()

    def _worker(self, key):
        text, model, err = gemini_chat(list(self.history[-20:]), key)
        Clock.schedule_once(lambda dt: self._reply(text, model, err), 0)

    def _reply(self, text, model, err):
        self.busy = False
        if err:
            self.set_status("ERROR", (1, 0.2, 0.33, 1))
            self.add_bubble(f"⚠ {err}", False)
        else:
            self.set_status(f"GEMINI • {model.split('-')[1].upper()}", CYAN)
            self.history.append({"role": "model", "text": text})
            self.add_bubble(text, False)
            speak(text)

    # ── Mic (Android speech recognition) ──
    def on_mic(self, *a):
        if platform != "android":
            self.add_bubble("🎤 Voice input runs on the phone. On PC, just type.", False)
            return
        self.set_status("listening…", (0, 1, 0.53, 1))
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        def heard(text):
            Clock.schedule_once(lambda dt: self._heard(text), 0)

        def failed(err):
            Clock.schedule_once(
                lambda dt: (self.set_status("GEMINI • READY", CYAN),
                            self.add_bubble(f"🎤 {err}", False)), 0)
        try:
            from android_mic import listen
            listen(on_result=heard, on_error=failed)
        except Exception as e:
            Clock.schedule_once(lambda dt: failed(f"mic unavailable: {e}"), 0)

    def _heard(self, text):
        self.input.text = text
        self.send()

    # ── API key setup overlay ──
    def _show_setup(self, *a):
        if getattr(self, "_setup", None):
            self.remove_widget(self._setup)
        self._setup = box = BoxLayout(orientation="vertical", size_hint=(0.92, None),
                                      height=dp(230), pos_hint={"center_x": 0.5, "center_y": 0.5},
                                      spacing=dp(10), padding=dp(16))
        with box.canvas.before:
            Color(0.004, 0.055, 0.094, 1)
            box.rr = RoundedRectangle(radius=[dp(16)], pos=box.pos, size=box.size)
        box.bind(pos=lambda w, p: setattr(box.rr, "pos", p),
                 size=lambda w, s: setattr(box.rr, "size", s))
        box.add_widget(Label(text="⚙  AEGIS Setup", font_size="18sp", bold=True,
                             color=CYAN, size_hint_y=None, height=dp(30)))
        box.add_widget(Label(text="Paste your free Gemini API key\n"
                                 "(aistudio.google.com/apikey)",
                             font_size="13sp", color=(0.58, 0.72, 0.8, 1),
                             size_hint_y=None, height=dp(44)))
        self.key_input = TextInput(multiline=False, font_size="14sp",
                                   background_color=(0, 0.02, 0.04, 1),
                                   foreground_color=WHITE, cursor_color=CYAN,
                                   hint_text="AIza…", hint_text_color=DIM,
                                   size_hint_y=None, height=dp(44))
        self.key_input.text = CONFIG.get("gemini_api_key", "") or ""
        box.add_widget(self.key_input)
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        save = Button(text="SAVE", bold=True, background_normal="", background_down="",
                      background_color=(0, 0.25, 0.35, 1), color=CYAN)
        save.bind(on_press=lambda *a: self._save_key())
        cancel = Button(text="CLOSE", background_normal="", background_down="",
                        background_color=PANEL, color=DIM)
        cancel.bind(on_press=lambda *a: self.remove_widget(box))
        btns.add_widget(save)
        btns.add_widget(cancel)
        box.add_widget(btns)
        self.add_widget(box)

    def _save_key(self, *a):
        key = self.key_input.text.strip()
        if not key:
            return
        try:
            CONFIG["gemini_api_key"] = key
            path = _save_config_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
            self.set_status("GEMINI • READY", CYAN)
            self.add_bubble("✓ Key saved — AEGIS is live. Ask me anything!", False)
        except Exception as e:
            self.add_bubble(f"⚠ Could not save key: {e}\n\n"
                            "On Android, put the key in android_app/config/api_keys.json "
                            "before building the APK.", False)
        if self._setup:
            self.remove_widget(self._setup)
            self._setup = None


class AEGISApp(App):
    def build(self):
        self.title = "AEGIS"
        self.loading = LoadingScreen()
        Clock.schedule_interval(self._load_step, 0.04)
        return self.loading

    def _load_step(self, dt):
        if self.loading.progress.value >= 100:
            Clock.unschedule(self._load_step)
            Clock.schedule_once(self._show_chat, 0.5)
            return False
        self.loading.progress.value += 2
        return True

    def _show_chat(self, dt):
        self.chat = ChatScreen(self)
        self.root.clear_widgets()
        self.root.add_widget(self.chat)


if __name__ == "__main__":
    AEGISApp().run()

