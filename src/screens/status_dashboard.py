from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from src.services.tor_manager import tor_manager
from src.services.tor_settings_store import tor_settings_store
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.cards import Card
from src.widgets.tor_dashboard_widgets import (
    AutoReconnectCard,
    CircuitInfoCard,
    DaemonStatusCard,
    LatencyCard,
    OnionAddressCard,
    TorVersionCard,
)
from src.widgets.tor_onboarding_wizard import TorOnboardingWizard


class StatusDashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dashboard'

        root = BoxLayout(orientation='vertical')

        header = BoxLayout(orientation='horizontal', padding=[dp(20), dp(16)], spacing=dp(12), size_hint_y=None, height=dp(64))
        self.title = Label(
            text='Tor Connection Status',
            font_size=theme_manager.typography.H4,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))

        self.onboarding_btn = Button(text='Tor Setup', size_hint_x=None, width=dp(120), on_release=lambda *_: self.open_onboarding())

        header.add_widget(self.title)
        header.add_widget(BoxLayout())
        header.add_widget(self.onboarding_btn)
        root.add_widget(header)

        self.scroll = ScrollView(do_scroll_x=False)
        self.cards = GridLayout(cols=1, spacing=dp(12), padding=[dp(20), dp(12)], size_hint_y=None)
        self.cards.bind(minimum_height=self.cards.setter('height'))
        self.scroll.add_widget(self.cards)
        root.add_widget(self.scroll)

        self.add_widget(root)

        self.daemon_card = DaemonStatusCard(
            on_start=lambda: tor_manager.start_tor(),
            on_stop=lambda: tor_manager.stop_tor(),
            on_restart=lambda: tor_manager.restart_tor(),
        )
        self.auto_reconnect_card = AutoReconnectCard(on_toggle=lambda enabled: tor_manager.set_auto_reconnect(enabled))
        self.onion_card = OnionAddressCard()
        self.circuit_card = CircuitInfoCard(on_new_circuit=lambda: tor_manager.force_new_circuit())
        self.latency_card = LatencyCard()
        self.version_card = TorVersionCard()
        self.traffic_card = Card(title='Traffic Status', content='Waiting for analysis…')

        for w in [
            self.daemon_card,
            self.auto_reconnect_card,
            self.onion_card,
            self.circuit_card,
            self.latency_card,
            self.version_card,
            self.traffic_card,
        ]:
            self.cards.add_widget(w)

        Window.bind(size=lambda *_: self._update_cols())
        self._update_cols()

        event_bus.bind(on_tor_state_update=self._on_tor_state)
        event_bus.bind(on_traffic_status_update=self._on_traffic_status)

        Clock.schedule_once(lambda dt: self._bootstrap_initial_state(), 0)

    def _bootstrap_initial_state(self):
        self._on_tor_state(self, tor_manager.get_state())
        settings = tor_settings_store.get_settings()
        if not settings.get('has_onboarded', False):
            Clock.schedule_once(lambda dt: self.open_onboarding(), 0.15)

    def _update_cols(self):
        width, _ = Window.size
        self.cards.cols = 1 if width < dp(900) else 2

    def open_onboarding(self):
        wizard = TorOnboardingWizard(tor_manager=tor_manager)
        wizard.open()

    @mainthread
    def _on_tor_state(self, instance, state):
        self.daemon_card.apply_state(state)
        self.auto_reconnect_card.apply_state(state)
        self.onion_card.apply_state(state)
        self.circuit_card.apply_state(state)
        self.latency_card.apply_state(state)
        self.version_card.apply_state(state)

    @mainthread
    def _on_traffic_status(self, instance, status):
        self.traffic_card.update_content(status)
