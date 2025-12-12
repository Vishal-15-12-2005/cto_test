from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch

from src.services.smart_agent import smart_agent
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.cards import Card
from src.widgets.traffic_widgets import (
    TrafficModeIndicator,
    MetricDisplay,
    TrafficRateGraph,
    StandardAIControlsCard
)
from datetime import time


class TrafficDashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'traffic'

        root = BoxLayout(orientation='vertical')

        header = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(64)
        )
        
        title = Label(
            text='Traffic Obfuscation Dashboard',
            font_size=theme_manager.typography.H4,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=title.setter('color'))

        header.add_widget(title)
        header.add_widget(BoxLayout())
        root.add_widget(header)

        self.scroll = ScrollView(do_scroll_x=False)
        self.cards = GridLayout(cols=1, spacing=dp(12), padding=[dp(20), dp(12)], size_hint_y=None)
        self.cards.bind(minimum_height=self.cards.setter('height'))
        self.scroll.add_widget(self.cards)
        root.add_widget(self.scroll)

        self.add_widget(root)

        self.status_card = self._build_status_card()
        self.metrics_card = self._build_metrics_card()
        self.graph_card = self._build_graph_card()
        self.controls_card = StandardAIControlsCard(
            on_toggle=self._handle_ai_toggle,
            on_settings_change=self._handle_settings_change
        )

        for w in [self.status_card, self.metrics_card, self.graph_card, self.controls_card]:
            self.cards.add_widget(w)

        Window.bind(size=lambda *_: self._update_cols())
        self._update_cols()

        event_bus.bind(on_traffic_obfuscation_update=self._on_traffic_update)

        Clock.schedule_once(lambda dt: self._bootstrap_initial_state(), 0)

    def _build_status_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        mode_row = BoxLayout(orientation='horizontal', spacing=dp(16), size_hint_y=None, height=dp(40))
        mode_label = Label(
            text='Mode:',
            font_size=theme_manager.typography.BODY1,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=0.3
        )
        mode_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=mode_label.setter('color'))

        self.mode_indicator = TrafficModeIndicator()
        mode_row.add_widget(mode_label)
        mode_row.add_widget(self.mode_indicator)

        ml_row = BoxLayout(orientation='horizontal', spacing=dp(16), size_hint_y=None, height=dp(32))
        ml_label = Label(
            text='ML Model:',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=0.3
        )
        ml_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=ml_label.setter('color'))

        self.ml_status_label = Label(
            text='Idle',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.ml_status_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.ml_status_label.setter('color'))

        ml_row.add_widget(ml_label)
        ml_row.add_widget(self.ml_status_label)

        always_on_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.always_on_label = Label(
            text='Always-On Protection',
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.always_on_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.always_on_label.setter('color'))

        self.always_on_switch = Switch(active=False)
        self.always_on_switch.bind(active=self._handle_always_on)

        always_on_row.add_widget(self.always_on_label)
        always_on_row.add_widget(BoxLayout())
        always_on_row.add_widget(self.always_on_switch)

        body.add_widget(mode_row)
        body.add_widget(ml_row)
        body.add_widget(always_on_row)

        return Card(title='Obfuscation Status', body=body)

    def _build_metrics_card(self):
        body = GridLayout(cols=2, spacing=dp(16), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.packets_metric = MetricDisplay('Packets Obfuscated', '0')
        self.data_metric = MetricDisplay('Data Generated', '0 MB')
        self.battery_metric = MetricDisplay('Battery Impact', '0%')
        self.network_metric = MetricDisplay('Network Usage', '0 Mbps')

        body.add_widget(self.packets_metric)
        body.add_widget(self.data_metric)
        body.add_widget(self.battery_metric)
        body.add_widget(self.network_metric)

        return Card(title='Real-Time Metrics', body=body)

    def _build_graph_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.traffic_graph = TrafficRateGraph()
        
        legend = Label(
            text='Live traffic rate visualization (packets/sec)',
            font_size=theme_manager.typography.CAPTION,
            halign='center',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(20)
        )
        legend.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=legend.setter('color'))

        body.add_widget(self.traffic_graph)
        body.add_widget(legend)

        return Card(title='Traffic Rate', body=body)

    def _update_cols(self):
        width, _ = Window.size
        self.cards.cols = 1 if width < dp(900) else 2

    def _bootstrap_initial_state(self):
        state = smart_agent.get_state()
        self._on_traffic_update(self, state)

    def _handle_ai_toggle(self, enabled):
        smart_agent.set_standard_ai(enabled)

    def _handle_always_on(self, instance, value):
        smart_agent.set_always_on(bool(value))

    def _handle_settings_change(self, setting_name, value):
        if setting_name == 'background_noise':
            smart_agent.set_background_noise(value)
        elif setting_name == 'intensity':
            smart_agent.set_intensity(value)
        elif setting_name == 'frequency_range':
            smart_agent.set_frequency_range(value)
        elif setting_name == 'scheduling_enabled':
            smart_agent.set_scheduling(value)
        elif setting_name == 'schedule':
            start, end = value
            start_time = time(*start)
            end_time = time(*end)
            smart_agent.set_scheduling(smart_agent.scheduling_enabled, start_time, end_time)

    @mainthread
    def _on_traffic_update(self, instance, state):
        mode = state.get('mode', 'off')
        self.mode_indicator.update_mode(mode)

        ml_status = state.get('ml_model_status', 'idle')
        ml_version = state.get('ml_model_version', '')
        self.ml_status_label.text = f'{ml_status.title()} ({ml_version})'

        self.always_on_switch.active = state.get('always_on', False)

        packets = state.get('packets_obfuscated', 0)
        self.packets_metric.update_value(f'{packets:,}')

        data_mb = state.get('data_generated_mb', 0)
        self.data_metric.update_value(f'{data_mb:.2f} MB')

        battery = state.get('battery_impact', 0)
        self.battery_metric.update_value(f'{battery}%')

        network = state.get('network_usage_mbps', 0)
        self.network_metric.update_value(f'{network:.2f} Mbps')

        traffic_history = state.get('traffic_rate_history', [])
        self.traffic_graph.update_data(traffic_history)

        self.controls_card.apply_state(state)
