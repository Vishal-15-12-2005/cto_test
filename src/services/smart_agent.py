from kivy.clock import Clock
from src.utils.event_bus import event_bus
import random

class SmartAIAgent:
    def __init__(self):
        self.active = False
        
    def activate(self):
        self.active = True
        Clock.schedule_interval(self._analyze_traffic, 3)
        
    def deactivate(self):
        self.active = False
        
    def _analyze_traffic(self, dt):
        if self.active:
            status = f"Traffic Normal - {random.randint(10, 50)} req/s"
            event_bus.emit_traffic_status(status)

smart_agent = SmartAIAgent()
