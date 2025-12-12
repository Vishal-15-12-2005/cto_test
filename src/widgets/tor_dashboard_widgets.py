from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from src.theming.theme_manager import theme_manager
from src.widgets.cards import Card


def _state_color(connection_state: str):
    if connection_state in {'connected'}:
        return [0.2, 0.75, 0.35, 1]
    if connection_state in {'bootstrapping', 'starting', 'restarting'}:
        return [0.95, 0.7, 0.2, 1]
    if connection_state in {'retrying'}:
        return [0.4, 0.65, 0.95, 1]
    if connection_state in {'disconnected', 'error'}:
        return [0.9, 0.25, 0.25, 1]
    return [0.6, 0.6, 0.6, 1]


class Dot(Widget):
    rgba = ListProperty([0.6, 0.6, 0.6, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(10), dp(10))
        with self.canvas:
            self._c = Color(rgba=self.rgba)
            self._e = Ellipse(pos=self.pos, size=self.size)

        self.bind(pos=self._update, size=self._update, rgba=self._update_rgba)

    def _update(self, *_):
        self._e.pos = self.pos
        self._e.size = self.size

    def _update_rgba(self, *_):
        self._c.rgba = self.rgba


class ConnectionStateIndicator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(22)

        self.dot = Dot()
        self.label = Label(text='Stopped', halign='left', valign='middle', color=theme_manager.text_color)
        self.label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.label.setter('color'))

        self.add_widget(self.dot)
        self.add_widget(self.label)

    def apply_state(self, state):
        cs = state.get('connection_state', 'unknown')
        self.dot.rgba = _state_color(cs)
        self.label.text = cs.replace('_', ' ').title()


class BusyBar(ProgressBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max = 100
        self.value = 0
        self.size_hint_y = None
        self.height = dp(4)
        self.opacity = 0
        self._anim = None

    def set_busy(self, busy: bool):
        if busy:
            self.opacity = 1
            if self._anim is None:
                self._anim = Clock.schedule_interval(self._tick, 0.05)
        else:
            self.opacity = 0
            self.value = 0
            if self._anim is not None:
                self._anim.cancel()
                self._anim = None

    def _tick(self, dt):
        self.value = (self.value + 5) % 100


class DaemonStatusCard(Card):
    def __init__(self, on_start=None, on_stop=None, on_restart=None, **kwargs):
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_restart = on_restart

        body = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.status_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24))
        self.connection_indicator = ConnectionStateIndicator()
        self.status_row.add_widget(self.connection_indicator)
        self.status_row.add_widget(BoxLayout())

        self.busy_bar = BusyBar()

        btn_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.start_btn = Button(text='Start', on_release=lambda *_: self._on_start and self._on_start())
        self.stop_btn = Button(text='Stop', on_release=lambda *_: self._on_stop and self._on_stop())
        self.restart_btn = Button(text='Restart', on_release=lambda *_: self._on_restart and self._on_restart())

        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.stop_btn)
        btn_row.add_widget(self.restart_btn)

        self.detail = Label(text='—', halign='left', valign='top', color=theme_manager.text_color)
        self.detail.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.detail.setter('color'))

        body.add_widget(self.status_row)
        body.add_widget(self.busy_bar)
        body.add_widget(btn_row)
        body.add_widget(self.detail)

        super().__init__(title='Tor Daemon', body=body, **kwargs)

    def apply_state(self, state):
        daemon_status = state.get('daemon_status', 'unknown')
        connection_state = state.get('connection_state', 'unknown')
        busy_action = state.get('busy_action')

        self.connection_indicator.apply_state(state)
        self.detail.text = state.get('bootstrap_status', '—')

        busy = busy_action in {'start', 'stop', 'restart', 'reconnect', 'new_circuit'} or daemon_status in {
            'starting',
            'stopping',
            'restarting',
        }
        self.busy_bar.set_busy(bool(busy))

        self.start_btn.disabled = daemon_status in {'starting', 'running', 'restarting', 'stopping'}
        self.stop_btn.disabled = daemon_status in {'stopping', 'stopped'}
        self.restart_btn.disabled = daemon_status in {'starting', 'stopping', 'restarting'}


class OnionAddressCard(Card):
    def __init__(self, **kwargs):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.address = TextInput(text='', readonly=True, multiline=False)
        self.copy_btn = Button(text='Copy', size_hint_x=None, width=dp(90), on_release=lambda *_: self._copy())
        row.add_widget(self.address)
        row.add_widget(self.copy_btn)

        self.hint = Label(text='—', halign='left', valign='top', color=theme_manager.text_color, font_size=theme_manager.typography.CAPTION)
        self.hint.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.hint.setter('color'))

        body.add_widget(row)
        body.add_widget(self.hint)

        super().__init__(title='Onion Address', body=body, **kwargs)

    def _copy(self):
        addr = self.address.text.strip()
        if not addr:
            self.hint.text = 'No onion address yet.'
            return
        Clipboard.copy(addr)
        self.hint.text = 'Copied to clipboard.'
        Clock.schedule_once(lambda dt: setattr(self.hint, 'text', '—'), 1.2)

    def apply_state(self, state):
        addr = state.get('onion_address', '') or ''
        self.address.text = addr
        self.copy_btn.disabled = not bool(addr)


class CircuitInfoCard(Card):
    def __init__(self, on_new_circuit=None, **kwargs):
        self._on_new_circuit = on_new_circuit

        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.info = Label(text='—', halign='left', valign='top', color=theme_manager.text_color)
        self.info.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.info.setter('color'))

        self.refresh_btn = Button(text='Force New Circuit', size_hint_y=None, height=dp(40), on_release=lambda *_: self._on_new_circuit and self._on_new_circuit())

        body.add_widget(self.info)
        body.add_widget(self.refresh_btn)

        super().__init__(title='Circuit / Guard', body=body, **kwargs)

    def apply_state(self, state):
        circuit_id = state.get('circuit_id') or '—'
        guard = state.get('guard_node') or '—'
        path = state.get('circuit_path') or []
        path_text = ' → '.join(path) if path else '—'

        self.info.text = f"Guard: {guard}\nCircuit: {circuit_id}\nPath: {path_text}"
        self.refresh_btn.disabled = state.get('connection_state') != 'connected'


class LatencyCard(Card):
    def __init__(self, **kwargs):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.value_label = Label(text='—', halign='left', valign='middle', color=theme_manager.text_color)
        self.value_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.value_label.setter('color'))

        self.bar = ProgressBar(max=500, value=0, size_hint_y=None, height=dp(10))

        body.add_widget(self.value_label)
        body.add_widget(self.bar)

        super().__init__(title='Latency', body=body, **kwargs)

    def apply_state(self, state):
        latency = state.get('latency_ms')
        if latency is None:
            self.value_label.text = '—'
            self.bar.value = 0
            return
        self.value_label.text = f"{int(latency)} ms"
        self.bar.value = min(int(latency), 500)


class TorVersionCard(Card):
    def __init__(self, **kwargs):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.value_label = Label(text='—', halign='left', valign='middle', color=theme_manager.text_color)
        self.value_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.value_label.setter('color'))

        body.add_widget(self.value_label)
        super().__init__(title='Tor Version', body=body, **kwargs)

    def apply_state(self, state):
        self.value_label.text = state.get('tor_version', '—')


class AutoReconnectCard(Card):
    def __init__(self, on_toggle=None, **kwargs):
        self._on_toggle = on_toggle
        self._updating_switch = False

        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.switch = Switch(active=True)
        self.switch.bind(active=self._handle_toggle)

        self.label = Label(text='Auto-reconnect', halign='left', valign='middle', color=theme_manager.text_color)
        self.label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.label.setter('color'))

        row.add_widget(self.label)
        row.add_widget(BoxLayout())
        row.add_widget(self.switch)

        self.status = Label(text='—', halign='left', valign='top', color=theme_manager.text_color, font_size=theme_manager.typography.CAPTION)
        self.status.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.status.setter('color'))

        body.add_widget(row)
        body.add_widget(self.status)

        super().__init__(title='Reconnect', body=body, **kwargs)

    def _handle_toggle(self, instance, enabled):
        if self._updating_switch:
            return
        if self._on_toggle is not None:
            self._on_toggle(bool(enabled))

    def apply_state(self, state):
        self._updating_switch = True
        self.switch.active = bool(state.get('auto_reconnect', True))
        self._updating_switch = False

        if state.get('connection_state') == 'retrying':
            self.status.text = f"Retrying… attempt {state.get('retry_count', 0)}"
        elif state.get('connection_state') == 'disconnected':
            self.status.text = state.get('last_error', 'Disconnected.')
        else:
            self.status.text = '—'
