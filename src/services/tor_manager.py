from kivy.clock import Clock
from src.utils.event_bus import event_bus
import random

class TorManager:
    def __init__(self):
        self.is_running = False
        
    def start_service(self):
        self.is_running = True
        # Simulate status updates
        Clock.schedule_interval(self._update_status, 5)
        
    def stop_service(self):
        self.is_running = False
        
    def _update_status(self, dt):
        if self.is_running:
            status = f"Connected - Circuit {random.randint(100, 999)}"
            event_bus.emit_tor_status(status)

tor_manager = TorManager()
