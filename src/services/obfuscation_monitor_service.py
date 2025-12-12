import random
from kivy.clock import Clock, mainthread
from src.utils.event_bus import event_bus
from src.services.tor_manager import tor_manager
from src.services.smart_agent import smart_agent
from src.services.obfuscation_config_service import obfuscation_config_service


class ObfuscationMonitorService:
    def __init__(self):
        self._service_running = False
        self._update_event = None
        
        # Monitoring data
        self._packets_per_sec_history = []
        self._cpu_usage = 0
        self._memory_usage = 0
        self._battery_drain = 0
        self._bandwidth_in = 0.0
        self._bandwidth_out = 0.0
        self._model_accuracy = 0.0
        self._model_latency = 0
        self._active_circuits = 0
        self._error_log = []
        
        # Bind to tor and traffic events
        event_bus.bind(on_tor_state_update=self._on_tor_state_update)
        event_bus.bind(on_traffic_obfuscation_update=self._on_traffic_update)

    def start_service(self):
        if self._service_running:
            return
        self._service_running = True
        self._update_event = Clock.schedule_interval(self._update_metrics, 2.5)

    def stop_service(self):
        self._service_running = False
        if self._update_event is not None:
            self._update_event.cancel()
            self._update_event = None

    def _on_tor_state_update(self, instance, state):
        if state.get('connection_state') == 'connected':
            self._active_circuits = random.randint(3, 8)
        else:
            self._active_circuits = 0

    def _on_traffic_update(self, instance, state):
        pass

    def _update_metrics(self, dt):
        if not self._service_running:
            return

        # Get current traffic state
        traffic_state = smart_agent.get_state()
        mode = traffic_state.get('mode', 'off')

        # Simulate packets per second
        if mode == 'standard':
            pps = random.uniform(20, 80)
        elif mode == 'maximum':
            pps = random.uniform(100, 300)
        else:
            pps = random.uniform(0, 10)

        self._packets_per_sec_history.append(pps)
        if len(self._packets_per_sec_history) > 50:
            self._packets_per_sec_history.pop(0)

        # Simulate resource usage
        if mode == 'standard':
            self._cpu_usage = random.uniform(15, 35)
            self._memory_usage = random.uniform(20, 40)
            self._battery_drain = random.uniform(10, 25)
        elif mode == 'maximum':
            self._cpu_usage = random.uniform(40, 70)
            self._memory_usage = random.uniform(45, 75)
            self._battery_drain = random.uniform(30, 60)
        else:
            self._cpu_usage = random.uniform(2, 8)
            self._memory_usage = random.uniform(5, 15)
            self._battery_drain = random.uniform(1, 5)

        # Simulate bandwidth
        if mode == 'standard':
            self._bandwidth_in = random.uniform(0.5, 2.0)
            self._bandwidth_out = random.uniform(1.0, 3.0)
        elif mode == 'maximum':
            self._bandwidth_in = random.uniform(2.0, 5.0)
            self._bandwidth_out = random.uniform(3.0, 8.0)
        else:
            self._bandwidth_in = random.uniform(0.1, 0.5)
            self._bandwidth_out = random.uniform(0.1, 0.5)

        # Model performance metrics
        if mode != 'off':
            self._model_accuracy = random.uniform(92, 99)
            self._model_latency = random.randint(5, 25)
        else:
            self._model_accuracy = 0
            self._model_latency = 0

        # Randomly add errors
        if random.random() < 0.05 and mode != 'off':
            self._add_error(f"Warning: High latency detected ({random.randint(50, 150)}ms)")

        # Update history stats
        history = obfuscation_config_service.get_history()
        if mode != 'off':
            packets_delta = int(pps * 2.5)
            data_delta = (self._bandwidth_in + self._bandwidth_out) * 2.5 / 8.0

            obfuscation_config_service.update_history(
                session_packets=history.get('session_packets', 0) + packets_delta,
                session_data_mb=history.get('session_data_mb', 0) + data_delta,
                today_packets=history.get('today_packets', 0) + packets_delta,
                today_data_mb=history.get('today_data_mb', 0) + data_delta,
                week_packets=history.get('week_packets', 0) + packets_delta,
                week_data_mb=history.get('week_data_mb', 0) + data_delta,
            )

        # Check thresholds and emit warnings
        self._check_thresholds()

        # Emit monitoring update
        self._emit_state()

    def _add_error(self, message):
        import time
        self._error_log.insert(0, {
            'timestamp': time.time(),
            'message': message
        })
        if len(self._error_log) > 20:
            self._error_log.pop()

        history = obfuscation_config_service.get_history()
        obfuscation_config_service.update_history(
            error_count=history.get('error_count', 0) + 1
        )

    def _check_thresholds(self):
        settings = obfuscation_config_service.get_settings()
        
        # Check data cap
        if settings.get('data_cap_enabled'):
            history = obfuscation_config_service.get_history()
            data_used = history.get('today_data_mb', 0)
            data_cap = settings.get('data_cap_mb', 1000)
            warning_threshold = settings.get('data_cap_warning_percent', 80)
            
            usage_percent = (data_used / data_cap) * 100 if data_cap > 0 else 0
            if usage_percent >= warning_threshold:
                event_bus.emit_obfuscation_warning('data_cap', 
                    f"Data usage at {usage_percent:.1f}% of cap ({data_used:.1f}/{data_cap} MB)")

    @mainthread
    def _emit_state(self):
        state = {
            'packets_per_sec_history': self._packets_per_sec_history[-30:],
            'cpu_usage': self._cpu_usage,
            'memory_usage': self._memory_usage,
            'battery_drain': self._battery_drain,
            'bandwidth_in': self._bandwidth_in,
            'bandwidth_out': self._bandwidth_out,
            'model_accuracy': self._model_accuracy,
            'model_latency': self._model_latency,
            'active_circuits': self._active_circuits,
            'error_log': self._error_log[:10],
        }
        event_bus.emit_obfuscation_monitor(state)

    def get_state(self):
        return {
            'packets_per_sec_history': self._packets_per_sec_history[-30:],
            'cpu_usage': self._cpu_usage,
            'memory_usage': self._memory_usage,
            'battery_drain': self._battery_drain,
            'bandwidth_in': self._bandwidth_in,
            'bandwidth_out': self._bandwidth_out,
            'model_accuracy': self._model_accuracy,
            'model_latency': self._model_latency,
            'active_circuits': self._active_circuits,
            'error_log': self._error_log[:10],
        }


obfuscation_monitor_service = ObfuscationMonitorService()
