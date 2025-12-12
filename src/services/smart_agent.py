import random

from kivy.clock import Clock

from src.utils.event_bus import event_bus


class SmartAIAgent:
    def __init__(self):
        self.active = False
        self._sensitive_active = False
        self._clear_sensitive_event = None

    def activate(self):
        self.active = True
        Clock.schedule_interval(self._analyze_traffic, 3)

    def deactivate(self):
        self.active = False
        if self._clear_sensitive_event is not None:
            self._clear_sensitive_event.cancel()
            self._clear_sensitive_event = None

    def _analyze_traffic(self, dt):
        if not self.active:
            return

        status = f"Traffic Normal - {random.randint(10, 50)} req/s"
        event_bus.emit_traffic_status(status)

        if not self._sensitive_active and random.random() < 0.12:
            self._sensitive_active = True
            event_bus.emit_sensitive_comms(True, 'Sensitive communications detected (mock)')
            self._clear_sensitive_event = Clock.schedule_once(self._clear_sensitive, 7.0)

    def _clear_sensitive(self, dt):
        self._clear_sensitive_event = None
        if not self.active:
            return
        if not self._sensitive_active:
            return
        self._sensitive_active = False
        event_bus.emit_sensitive_comms(False, '')


smart_agent = SmartAIAgent()
