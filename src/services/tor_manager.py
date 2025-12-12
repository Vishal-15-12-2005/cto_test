import random
import string
from kivy.clock import Clock
from src.utils.event_bus import event_bus
from src.services.tor_settings_store import tor_settings_store


class TorManager:
    def __init__(self):
        self._service_running = False
        self._tick_event = None
        self._bootstrap_event = None
        self._reconnect_event = None

        settings = tor_settings_store.get_settings()
        self._state = {
            'daemon_status': 'stopped',
            'connection_state': 'stopped',
            'bootstrap_progress': 0,
            'bootstrap_status': 'Not started',
            'onion_address': '',
            'guard_node': '',
            'circuit_id': '',
            'circuit_path': [],
            'latency_ms': None,
            'tor_version': '0.4.8.0-mock',
            'auto_reconnect': bool(settings.get('auto_reconnect', True)),
            'retrying': False,
            'retry_count': 0,
            'busy_action': None,
            'last_error': '',
        }

        event_bus.bind(on_tor_settings_update=self._on_settings_update)

    def start_service(self):
        if self._service_running:
            return
        self._service_running = True
        event_bus.emit_tor_settings(tor_settings_store.get_settings())
        self._emit_state()
        self._tick_event = Clock.schedule_interval(self._tick, 1.0)

    def stop_service(self):
        self._service_running = False
        if self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None
        self._cancel_bootstrap()
        self._cancel_reconnect()

    def get_state(self):
        return dict(self._state)

    def apply_settings(self, **settings_patch):
        tor_settings_store.update_settings(**settings_patch)

    def start_tor(self):
        if self._state['daemon_status'] in {'starting', 'running', 'restarting'}:
            return
        self._begin_start(action='start')

    def stop_tor(self):
        if self._state['daemon_status'] in {'stopping', 'stopped'}:
            return
        self._cancel_bootstrap()
        self._cancel_reconnect()
        self._state.update(
            daemon_status='stopping',
            connection_state='stopping',
            bootstrap_progress=0,
            bootstrap_status='Stopping Tor…',
            busy_action='stop',
            retrying=False,
            last_error='',
        )
        self._emit_state()
        Clock.schedule_once(lambda dt: self._finish_stop(), 1.0)

    def restart_tor(self):
        if self._state['daemon_status'] in {'starting', 'stopping', 'restarting'}:
            return
        self._cancel_bootstrap()
        self._cancel_reconnect()
        self._state.update(
            daemon_status='restarting',
            connection_state='restarting',
            bootstrap_progress=0,
            bootstrap_status='Restarting Tor…',
            busy_action='restart',
            retrying=False,
            last_error='',
        )
        self._emit_state()
        Clock.schedule_once(lambda dt: self._do_restart(), 0.8)

    def force_new_circuit(self):
        if self._state['connection_state'] != 'connected':
            return
        self._state.update(busy_action='new_circuit')
        self._emit_state()
        Clock.schedule_once(lambda dt: self._set_new_circuit(), 0.7)

    def set_auto_reconnect(self, enabled: bool):
        self.apply_settings(auto_reconnect=bool(enabled))

    def _on_settings_update(self, instance, settings):
        self._state['auto_reconnect'] = bool(settings.get('auto_reconnect', True))
        self._emit_state()

    def _tick(self, dt):
        if not self._service_running:
            return

        if self._state['connection_state'] == 'connected':
            self._state['latency_ms'] = max(15, int(random.gauss(120, 35)))

            if random.random() < 0.02:
                self._state.update(
                    connection_state='disconnected',
                    bootstrap_status='Connection dropped (mock).',
                    last_error='Simulated network drop',
                )
                self._emit_state()

                if self._state['auto_reconnect']:
                    self._schedule_reconnect()
                return

            self._emit_state()

    def _emit_state(self):
        state = dict(self._state)
        event_bus.emit_tor_state(state)
        event_bus.emit_tor_status(self._format_status(state))

    def _format_status(self, state):
        cs = state.get('connection_state')
        if cs == 'connected':
            return f"Connected • Circuit {state.get('circuit_id', '')} • {state.get('latency_ms', '?')}ms"
        if cs == 'bootstrapping':
            return f"Bootstrapping • {state.get('bootstrap_progress', 0)}%"
        return cs.capitalize() if isinstance(cs, str) else 'Unknown'

    def _begin_start(self, action: str):
        self._cancel_bootstrap()
        self._cancel_reconnect()

        self._state.update(
            daemon_status='starting',
            connection_state='starting',
            bootstrap_progress=0,
            bootstrap_status='Launching Tor…',
            busy_action=action,
            retrying=False,
            last_error='',
        )
        self._emit_state()

        Clock.schedule_once(lambda dt: self._start_bootstrap(action=action), 0.9)

    def _start_bootstrap(self, action: str):
        self._cancel_bootstrap()
        self._state.update(
            daemon_status='running',
            connection_state='bootstrapping',
            bootstrap_progress=0,
            bootstrap_status='Bootstrapping 0%: Connecting to directory servers…',
            busy_action=action,
        )
        self._emit_state()
        self._bootstrap_event = Clock.schedule_interval(lambda dt: self._bootstrap_tick(action=action), 0.35)

    def _bootstrap_tick(self, action: str):
        inc = random.randint(4, 10)
        self._state['bootstrap_progress'] = min(100, int(self._state['bootstrap_progress']) + inc)
        p = self._state['bootstrap_progress']

        if p < 25:
            msg = 'Connecting to directory servers…'
        elif p < 50:
            msg = 'Loading network status…'
        elif p < 75:
            msg = 'Establishing circuits…'
        elif p < 100:
            msg = 'Finishing handshake…'
        else:
            msg = 'Done'

        self._state['bootstrap_status'] = f"Bootstrapping {p}%: {msg}"
        self._emit_state()

        if p >= 100:
            self._cancel_bootstrap()
            self._state.update(
                connection_state='connected',
                bootstrap_status='Connected.',
                onion_address=self._generate_onion(),
                latency_ms=max(15, int(random.gauss(120, 35))),
                busy_action=None,
                retrying=False,
            )
            self._set_new_circuit(emit=False)
            self._emit_state()

    def _finish_stop(self):
        self._state.update(
            daemon_status='stopped',
            connection_state='stopped',
            bootstrap_progress=0,
            bootstrap_status='Stopped.',
            onion_address='',
            guard_node='',
            circuit_id='',
            circuit_path=[],
            latency_ms=None,
            retrying=False,
            retry_count=0,
            busy_action=None,
            last_error='',
        )
        self._emit_state()

    def _do_restart(self):
        self._finish_stop()
        Clock.schedule_once(lambda dt: self._begin_start(action='restart'), 0.3)

    def _schedule_reconnect(self):
        if self._reconnect_event is not None:
            return

        self._state['retrying'] = True
        self._state['retry_count'] = int(self._state.get('retry_count', 0)) + 1
        delay = min(6.0, 1.5 + (self._state['retry_count'] * 0.75))
        self._state.update(connection_state='retrying', bootstrap_status=f"Auto-reconnect in {delay:.1f}s…")
        self._emit_state()

        self._reconnect_event = Clock.schedule_once(lambda dt: self._reconnect_now(), delay)

    def _reconnect_now(self):
        self._reconnect_event = None
        if not self._service_running:
            return

        if self._state['daemon_status'] == 'stopped':
            self._begin_start(action='reconnect')
            return

        self._start_bootstrap(action='reconnect')

    def _cancel_reconnect(self):
        if self._reconnect_event is None:
            return
        self._reconnect_event.cancel()
        self._reconnect_event = None

    def _cancel_bootstrap(self):
        if self._bootstrap_event is None:
            return
        self._bootstrap_event.cancel()
        self._bootstrap_event = None

    def _set_new_circuit(self, emit=True):
        self._state['circuit_id'] = str(random.randint(100, 999))
        self._state['guard_node'] = random.choice(['guard1', 'guard2', 'guard3']) + '.tor'
        self._state['circuit_path'] = [
            random.choice(['de', 'nl', 'se', 'fr', 'us']) + '1',
            random.choice(['de', 'nl', 'se', 'fr', 'us']) + '2',
            random.choice(['de', 'nl', 'se', 'fr', 'us']) + '3',
        ]
        self._state['busy_action'] = None
        self._state['bootstrap_status'] = 'Connected.'
        if emit:
            self._emit_state()

    def _generate_onion(self):
        return ''.join(random.choice(string.ascii_lowercase + '234567') for _ in range(56)) + '.onion'


tor_manager = TorManager()
