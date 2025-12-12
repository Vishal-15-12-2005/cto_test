from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty

class EventBus(EventDispatcher):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self, **kwargs):
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        super().__init__(**kwargs)
        self.register_event_type('on_tor_status_update')
        self.register_event_type('on_traffic_status_update')
        self.register_event_type('on_theme_changed')
        self._initialized = True

    def on_tor_status_update(self, status):
        pass

    def on_traffic_status_update(self, status):
        pass

    def on_theme_changed(self, theme_name):
        pass

    def emit_tor_status(self, status):
        self.dispatch('on_tor_status_update', status)

    def emit_traffic_status(self, status):
        self.dispatch('on_traffic_status_update', status)
    
    def emit_theme_changed(self, theme_name):
        self.dispatch('on_theme_changed', theme_name)

event_bus = EventBus()
