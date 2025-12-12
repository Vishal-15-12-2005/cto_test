from kivy.clock import Clock, mainthread
from src.utils.event_bus import event_bus
import random
from datetime import datetime, time
import random

from kivy.clock import Clock

from src.utils.event_bus import event_bus


class SmartAIAgent:
    def __init__(self):
        self.active = False
        self._update_event = None
        
        # Obfuscation mode: 'off', 'standard', 'maximum'
        self.mode = 'off'
        
        # Counters
        self.packets_obfuscated = 0
        self.data_generated_mb = 0.0
        
        # ML Model status
        self.ml_model_status = 'idle'  # 'idle', 'training', 'active', 'error'
        self.ml_model_version = 'v2.1.4'
        
        # Battery and network usage
        self.battery_impact = 0  # 0-100
        self.network_usage_mbps = 0.0
        
        # Always-on feature
        self.always_on = False
        
        # Standard AI controls
        self.standard_ai_enabled = False
        self.background_noise = False
        self.intensity = 50  # 0-100
        self.frequency_range = 'medium'  # 'low', 'medium', 'high'
        
        # Scheduling
        self.scheduling_enabled = False
        self.schedule_start = time(9, 0)
        self.schedule_end = time(17, 0)
        
        # Sample sites for preview
        self.sample_sites = [
            'news.example.com',
            'social.example.com',
            'video.example.com',
            'shopping.example.com'
        ]
        
        # Traffic rate data for graph
        self.traffic_rate_history = []
        
    def activate(self):
        self.active = True
        if self._update_event is None:
            self._update_event = Clock.schedule_interval(self._update_metrics, 1.5)
        
    def deactivate(self):
        self.active = False
        if self._update_event is not None:
            self._update_event.cancel()
            self._update_event = None
        
    def set_mode(self, mode):
        """Set obfuscation mode: 'off', 'standard', 'maximum'"""
        if mode in ['off', 'standard', 'maximum']:
            self.mode = mode
            if mode == 'off':
                self.ml_model_status = 'idle'
            else:
                self.ml_model_status = 'active'
            self._emit_state()
            
    def set_standard_ai(self, enabled):
        """Toggle Standard AI mode"""
        self.standard_ai_enabled = enabled
        if enabled:
            self.mode = 'standard'
            self.ml_model_status = 'active'
        else:
            self.mode = 'off'
            self.ml_model_status = 'idle'
        self._emit_state()
        
    def set_background_noise(self, enabled):
        """Toggle background noise"""
        self.background_noise = enabled
        self._emit_state()
        
    def set_intensity(self, value):
        """Set intensity level (0-100)"""
        self.intensity = max(0, min(100, value))
        self._recalculate_battery_impact()
        self._emit_state()
        
    def set_frequency_range(self, range_value):
        """Set frequency range: 'low', 'medium', 'high'"""
        if range_value in ['low', 'medium', 'high']:
            self.frequency_range = range_value
            self._recalculate_battery_impact()
            self._emit_state()
            
    def set_scheduling(self, enabled, start_time=None, end_time=None):
        """Configure scheduling"""
        self.scheduling_enabled = enabled
        if start_time:
            self.schedule_start = start_time
        if end_time:
            self.schedule_end = end_time
        self._emit_state()
        
    def set_always_on(self, enabled):
        """Toggle always-on feature"""
        self.always_on = enabled
        self._emit_state()
        
    def _recalculate_battery_impact(self):
        """Calculate battery impact based on settings"""
        base_impact = 10
        if self.standard_ai_enabled:
            base_impact = 20
            base_impact += (self.intensity / 100) * 30
            
            freq_multipliers = {'low': 0.8, 'medium': 1.0, 'high': 1.3}
            base_impact *= freq_multipliers.get(self.frequency_range, 1.0)
            
            if self.background_noise:
                base_impact += 15
                
        if self.always_on:
            base_impact += 10
            
        self.battery_impact = int(min(100, base_impact))
        
    @mainthread
    def _emit_state(self):
        """Emit current state to event bus"""
        state = {
            'mode': self.mode,
            'packets_obfuscated': self.packets_obfuscated,
            'data_generated_mb': self.data_generated_mb,
            'ml_model_status': self.ml_model_status,
            'ml_model_version': self.ml_model_version,
            'battery_impact': self.battery_impact,
            'network_usage_mbps': self.network_usage_mbps,
            'always_on': self.always_on,
            'standard_ai_enabled': self.standard_ai_enabled,
            'background_noise': self.background_noise,
            'intensity': self.intensity,
            'frequency_range': self.frequency_range,
            'scheduling_enabled': self.scheduling_enabled,
            'schedule_start': self.schedule_start,
            'schedule_end': self.schedule_end,
            'sample_sites': self.sample_sites,
            'traffic_rate_history': self.traffic_rate_history[-20:],  # Last 20 data points
        }
        event_bus.emit_traffic_obfuscation_update(state)
        
    def _update_metrics(self, dt):
        """Update metrics periodically (Clock-safe callback)"""
        if not self.active:
            return
            
        # Simulate traffic analysis
        if self.active:
            status = f"Traffic Normal - {random.randint(10, 50)} req/s"
            event_bus.emit_traffic_status(status)
        
        # Update counters based on mode
        if self.mode == 'standard':
            self.packets_obfuscated += random.randint(50, 200)
            self.data_generated_mb += random.uniform(0.5, 2.0)
            self.network_usage_mbps = random.uniform(0.5, 2.5)
        elif self.mode == 'maximum':
            self.packets_obfuscated += random.randint(200, 500)
            self.data_generated_mb += random.uniform(2.0, 5.0)
            self.network_usage_mbps = random.uniform(2.0, 5.0)
        else:
            self.network_usage_mbps = random.uniform(0.1, 0.5)
            
        # Update traffic rate history
        current_rate = random.uniform(10, 100) if self.mode != 'off' else random.uniform(1, 10)
        self.traffic_rate_history.append(current_rate)
        if len(self.traffic_rate_history) > 50:
            self.traffic_rate_history.pop(0)
            
        # Recalculate battery impact
        self._recalculate_battery_impact()
        
        # Emit updated state
        self._emit_state()
        
    def get_state(self):
        """Get current state synchronously"""
        return {
            'mode': self.mode,
            'packets_obfuscated': self.packets_obfuscated,
            'data_generated_mb': self.data_generated_mb,
            'ml_model_status': self.ml_model_status,
            'ml_model_version': self.ml_model_version,
            'battery_impact': self.battery_impact,
            'network_usage_mbps': self.network_usage_mbps,
            'always_on': self.always_on,
            'standard_ai_enabled': self.standard_ai_enabled,
            'background_noise': self.background_noise,
            'intensity': self.intensity,
            'frequency_range': self.frequency_range,
            'scheduling_enabled': self.scheduling_enabled,
            'schedule_start': self.schedule_start,
            'schedule_end': self.schedule_end,
            'sample_sites': self.sample_sites,
            'traffic_rate_history': self.traffic_rate_history[-20:],
        }
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
