"""AEGIS Android Kivy App with loading screen"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, LinearGradient, StencilPush, StencilUnpop
from kivy.graphics import RoundedRectangle
from kivy.properties import NumericProperty
from pathlib import Path
import threading
import time

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "logo.png"

class LoadingScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # AEGIS dark vibe background
        with self.canvas.before:
            Color(0.0, 0.038, 0.063, 1)  # #00060a
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Subtle glow overlay
        with self.canvas.after:
            Color(0.0, 0.5, 0.8, 0.08)
            self.glow = Rectangle(pos=self.pos, size=self.size)

        # Central card
        self.add_widget(BoxLayout(
            orientation='vertical',
            size_hint=(0.85, 0.6),
            pos_hint={'center_x':0.5, 'center_y':0.5},
            padding=30,
            spacing=20
        ))

        # Build central content via a child layout
        central = self.children[0]
        # Dark panel background
        with central.canvas.before:
            Color(0.004, 0.055, 0.094, 0.85)
            self.panel = RoundedRectangle(radius=[18], pos=central.pos, size=central.size)
        central.bind(pos=self._update_panel, size=self._update_panel)

        # Logo with white background card
        logo_wrap = BoxLayout(size_hint_y=0.45)
        logo_card = BoxLayout(size_hint=(0.7,1), pos_hint={'center_x':0.5})
        with logo_card.canvas.before:
            Color(1,1,1,1)
            self.logo_bg = RoundedRectangle(radius=[14], pos=logo_card.pos, size=logo_card.size)
        logo_card.bind(pos=self._update_logo_bg, size=self._update_logo_bg)

        if LOGO_PATH.exists():
            logo_img = Image(source=str(LOGO_PATH), allow_stretch=True, keep_ratio=True)
        else:
            logo_img = Label(text="[AEGIS]", font_size='56sp', color=(0,0.2,0.3,1))
        logo_card.add_widget(logo_img)
        logo_wrap.add_widget(logo_card)
        central.add_widget(logo_wrap)

        # Title
        title = Label(text='AEGIS', font_size='34sp', bold=True, color=(0.0, 0.82, 1, 1), size_hint_y=0.15)
        central.add_widget(title)

        subtitle = Label(text='Initializing AI Assistant…', font_size='15sp', color=(0.58,0.72,0.8,1), size_hint_y=0.1)
        central.add_widget(subtitle)

        # Progress bar styled
        self.progress = ProgressBar(max=100, value=0, size_hint_y=0.12)
        self.progress.background_color = (0.01,0.07,0.12,1)
        self.progress.color = (0.0,0.82,1,1)
        central.add_widget(self.progress)

        # Tagline
        tag = Label(text='Powerful • Private • Yours', font_size='13sp', color=(0.4,0.6,0.7,1), size_hint_y=0.1)
        central.add_widget(tag)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.glow.pos = self.pos
        self.glow.size = self.size

    def _update_panel(self, *args):
        obj = self.children[0]
        self.panel.pos = obj.pos
        self.panel.size = obj.size

    def _update_logo_bg(self, *args):
        # logo_card is nested, update via traverse
        pass

    def update_progress(self, value):
        self.progress.value = value

    def update_progress(self, value):
        self.progress.value = value

class AEGISApp(App):
    def build(self):
        self.loading = LoadingScreen()
        # Simulate init
        Clock.schedule_interval(self._simulate_load, 0.05)
        return self.loading

    def _simulate_load(self, dt):
        if self.loading.progress.value >= 100:
            # Switch to main screen
            Clock.unschedule(self._simulate_load)
            self.stop()
            return True
        self.loading.update_progress(self.loading.progress.value + 1)
        return True

if __name__ == '__main__':
    AEGISApp().run()
