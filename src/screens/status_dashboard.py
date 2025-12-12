from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from src.widgets.cards import Card
from src.utils.event_bus import event_bus
from src.theming.theme_manager import theme_manager
from kivy.clock import mainthread

class StatusDashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dashboard'
        
        root = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Title
        self.title = Label(text="Status Dashboard", font_size=theme_manager.typography.H4, size_hint_y=None, height=dp(50), color=theme_manager.text_color)
        theme_manager.bind(text_color=self.title.setter('color'))
        root.add_widget(self.title)
        
        # Theme Toggle
        toggle_btn = Button(text="Toggle Theme", size_hint_y=None, height=dp(40), on_release=lambda x: theme_manager.toggle_theme())
        root.add_widget(toggle_btn)
        
        # Cards Area
        cards_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        
        self.tor_card = Card(title="Tor Status", content="Waiting for status...")
        self.traffic_card = Card(title="Traffic Status", content="Waiting for analysis...")
        
        cards_layout.add_widget(self.tor_card)
        cards_layout.add_widget(self.traffic_card)
        cards_layout.add_widget(BoxLayout()) # Spacer
        
        root.add_widget(cards_layout)
        self.add_widget(root)
        
        # Subscribe to events
        event_bus.bind(on_tor_status_update=self.update_tor_status)
        event_bus.bind(on_traffic_status_update=self.update_traffic_status)

    @mainthread
    def update_tor_status(self, instance, status):
        self.tor_card.update_content(status)

    @mainthread
    def update_traffic_status(self, instance, status):
        self.traffic_card.update_content(status)
