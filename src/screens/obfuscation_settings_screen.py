from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button

from src.services.obfuscation_config_service import obfuscation_config_service
from src.services.obfuscation_monitor_service import obfuscation_monitor_service
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.cards import Card
from src.widgets.obfuscation_widgets import (
    ResourceBar,
    PacketsGraph,
    BandwidthVisualization,
    ErrorLogList,
    CircuitStatusWidget,
    ModelPerformanceWidget
)


class ObfuscationSettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'obfuscation_settings'

        root = BoxLayout(orientation='vertical')

        header = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(64)
        )
        
        title = Label(
            text='Traffic Obfuscation Settings & Monitoring',
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

        # Build cards
        self.mode_card = self._build_mode_card()
        self.schedule_card = self._build_schedule_card()
        self.thresholds_card = self._build_thresholds_card()
        self.history_card = self._build_history_card()
        
        # Monitoring cards
        self.packets_graph_card = self._build_packets_graph_card()
        self.resources_card = self._build_resources_card()
        self.bandwidth_card = self._build_bandwidth_card()
        self.performance_card = self._build_performance_card()
        self.circuits_card = self._build_circuits_card()
        self.errors_card = self._build_errors_card()

        for w in [
            self.mode_card, 
            self.schedule_card, 
            self.thresholds_card,
            self.history_card,
            self.packets_graph_card,
            self.resources_card,
            self.bandwidth_card,
            self.performance_card,
            self.circuits_card,
            self.errors_card
        ]:
            self.cards.add_widget(w)

        Window.bind(size=lambda *_: self._update_cols())
        self._update_cols()

        event_bus.bind(on_obfuscation_settings_update=self._on_settings_update)
        event_bus.bind(on_obfuscation_monitor_update=self._on_monitor_update)
        event_bus.bind(on_obfuscation_warning=self._on_warning)

        Clock.schedule_once(lambda dt: self._bootstrap_initial_state(), 0)

    def _build_mode_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        standard_row = self._create_switch_row('Standard Mode', False)
        self.standard_switch = standard_row['switch']
        self.standard_switch.bind(active=lambda inst, val: self._handle_mode_change('standard', val))

        maximum_row = self._create_switch_row('Maximum Mode', False)
        self.maximum_switch = maximum_row['switch']
        self.maximum_switch.bind(active=lambda inst, val: self._handle_mode_change('maximum', val))

        auto_switch_row = self._create_switch_row('Auto-Switch (based on network load)', False)
        self.auto_switch = auto_switch_row['switch']
        self.auto_switch.bind(active=lambda inst, val: self._save_setting('auto_switch_enabled', val))

        threshold_label = Label(
            text='Auto-Switch Threshold (%)',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        threshold_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=threshold_label.setter('color'))

        threshold_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.threshold_slider = Slider(min=50, max=100, value=80, step=5)
        self.threshold_slider.bind(value=lambda inst, val: self._handle_threshold_change(val))
        self.threshold_value = Label(
            text='80%', 
            size_hint_x=None, 
            width=dp(50),
            color=theme_manager.text_color
        )
        theme_manager.bind(text_color=self.threshold_value.setter('color'))
        threshold_row.add_widget(self.threshold_slider)
        threshold_row.add_widget(self.threshold_value)

        body.add_widget(standard_row['container'])
        body.add_widget(maximum_row['container'])
        body.add_widget(auto_switch_row['container'])
        body.add_widget(threshold_label)
        body.add_widget(threshold_row)

        return Card(title='Obfuscation Modes', body=body)

    def _build_schedule_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        schedule_label = Label(
            text='Schedule Mode',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        schedule_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=schedule_label.setter('color'))

        self.schedule_spinner = Spinner(
            text='24/7',
            values=['24/7', 'Specific Hours', 'Business Hours (9-5)', 'Night Mode (22-6)'],
            size_hint_y=None,
            height=dp(40)
        )
        self.schedule_spinner.bind(text=self._handle_schedule_mode_change)

        time_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        time_row.add_widget(Label(text='Start:', size_hint_x=0.2, color=theme_manager.text_color))
        
        self.start_hour_spinner = Spinner(
            text='9',
            values=[str(i) for i in range(24)],
            size_hint_x=0.35
        )
        self.start_hour_spinner.bind(text=self._handle_time_change)
        
        self.start_minute_spinner = Spinner(
            text='00',
            values=[str(i).zfill(2) for i in range(0, 60, 15)],
            size_hint_x=0.35
        )
        self.start_minute_spinner.bind(text=self._handle_time_change)
        
        time_row.add_widget(self.start_hour_spinner)
        time_row.add_widget(self.start_minute_spinner)

        time_row2 = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        time_row2.add_widget(Label(text='End:', size_hint_x=0.2, color=theme_manager.text_color))
        
        self.end_hour_spinner = Spinner(
            text='17',
            values=[str(i) for i in range(24)],
            size_hint_x=0.35
        )
        self.end_hour_spinner.bind(text=self._handle_time_change)
        
        self.end_minute_spinner = Spinner(
            text='00',
            values=[str(i).zfill(2) for i in range(0, 60, 15)],
            size_hint_x=0.35
        )
        self.end_minute_spinner.bind(text=self._handle_time_change)
        
        time_row2.add_widget(self.end_hour_spinner)
        time_row2.add_widget(self.end_minute_spinner)

        body.add_widget(schedule_label)
        body.add_widget(self.schedule_spinner)
        body.add_widget(time_row)
        body.add_widget(time_row2)

        return Card(title='Schedule Settings', body=body)

    def _build_thresholds_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        battery_row = self._create_switch_row('Battery Saver (pause at low battery)', True)
        self.battery_saver_switch = battery_row['switch']
        self.battery_saver_switch.bind(active=lambda inst, val: self._save_setting('battery_saver_enabled', val))

        battery_threshold_label = Label(
            text='Battery Threshold (%)',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        battery_threshold_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=battery_threshold_label.setter('color'))

        battery_threshold_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.battery_threshold_slider = Slider(min=10, max=50, value=20, step=5)
        self.battery_threshold_slider.bind(value=lambda inst, val: self._handle_battery_threshold_change(val))
        self.battery_threshold_value = Label(
            text='20%', 
            size_hint_x=None, 
            width=dp(50),
            color=theme_manager.text_color
        )
        theme_manager.bind(text_color=self.battery_threshold_value.setter('color'))
        battery_threshold_row.add_widget(self.battery_threshold_slider)
        battery_threshold_row.add_widget(self.battery_threshold_value)

        network_row = self._create_switch_row('Network Quality Awareness', True)
        self.network_quality_switch = network_row['switch']
        self.network_quality_switch.bind(active=lambda inst, val: self._save_setting('network_quality_awareness', val))

        data_cap_row = self._create_switch_row('Data Cap Warnings', False)
        self.data_cap_switch = data_cap_row['switch']
        self.data_cap_switch.bind(active=lambda inst, val: self._save_setting('data_cap_enabled', val))

        data_cap_label = Label(
            text='Data Cap (MB)',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        data_cap_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=data_cap_label.setter('color'))

        data_cap_row_input = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.data_cap_slider = Slider(min=100, max=10000, value=1000, step=100)
        self.data_cap_slider.bind(value=lambda inst, val: self._handle_data_cap_change(val))
        self.data_cap_value = Label(
            text='1000 MB', 
            size_hint_x=None, 
            width=dp(80),
            color=theme_manager.text_color
        )
        theme_manager.bind(text_color=self.data_cap_value.setter('color'))
        data_cap_row_input.add_widget(self.data_cap_slider)
        data_cap_row_input.add_widget(self.data_cap_value)

        body.add_widget(battery_row['container'])
        body.add_widget(battery_threshold_label)
        body.add_widget(battery_threshold_row)
        body.add_widget(network_row['container'])
        body.add_widget(data_cap_row['container'])
        body.add_widget(data_cap_label)
        body.add_widget(data_cap_row_input)

        return Card(title='Thresholds & Warnings', body=body)

    def _build_history_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        session_box = self._create_stat_box('Session', '0 packets', '0.00 MB')
        today_box = self._create_stat_box('Today', '0 packets', '0.00 MB')
        week_box = self._create_stat_box('Week', '0 packets', '0.00 MB')

        self.session_packets_label = session_box['value1']
        self.session_data_label = session_box['value2']
        self.today_packets_label = today_box['value1']
        self.today_data_label = today_box['value2']
        self.week_packets_label = week_box['value1']
        self.week_data_label = week_box['value2']

        stats_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(80))
        stats_row.add_widget(session_box['container'])
        stats_row.add_widget(today_box['container'])
        stats_row.add_widget(week_box['container'])

        reset_btn = Button(
            text='Reset Session Stats',
            size_hint_y=None,
            height=dp(40),
            on_release=lambda *_: self._reset_session()
        )

        body.add_widget(stats_row)
        body.add_widget(reset_btn)

        return Card(title='Historical Statistics', body=body)

    def _build_packets_graph_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.packets_graph = PacketsGraph()
        
        legend = Label(
            text='Live traffic rate (packets/sec) - Updates every 2.5s',
            font_size=theme_manager.typography.CAPTION,
            halign='center',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(20)
        )
        legend.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=legend.setter('color'))

        body.add_widget(self.packets_graph)
        body.add_widget(legend)

        return Card(title='[MONITORING] Live Traffic Rate', body=body)

    def _build_resources_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.cpu_bar = ResourceBar('CPU Usage')
        self.memory_bar = ResourceBar('Memory Usage')
        self.battery_bar = ResourceBar('Battery Drain Rate')

        body.add_widget(self.cpu_bar)
        body.add_widget(self.memory_bar)
        body.add_widget(self.battery_bar)

        return Card(title='[MONITORING] Resource Usage', body=body)

    def _build_bandwidth_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.bandwidth_viz = BandwidthVisualization()
        body.add_widget(self.bandwidth_viz)

        return Card(title='[MONITORING] Bandwidth Ratio', body=body)

    def _build_performance_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.performance_widget = ModelPerformanceWidget()
        body.add_widget(self.performance_widget)

        return Card(title='[MONITORING] Model Performance', body=body)

    def _build_circuits_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.circuit_widget = CircuitStatusWidget()
        body.add_widget(self.circuit_widget)

        return Card(title='[MONITORING] Tor Connection Pool', body=body)

    def _build_errors_card(self):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.error_list = ErrorLogList()
        body.add_widget(self.error_list)

        return Card(title='[MONITORING] Error Log', body=body)

    def _create_switch_row(self, label_text, default_value):
        row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        
        label = Label(
            text=label_text,
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=label.setter('color'))

        switch = Switch(active=default_value)

        row.add_widget(label)
        row.add_widget(BoxLayout())
        row.add_widget(switch)

        return {'container': row, 'label': label, 'switch': switch}

    def _create_stat_box(self, title, value1, value2):
        container = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None, height=dp(80))
        
        title_label = Label(
            text=title,
            font_size=theme_manager.typography.CAPTION,
            halign='center',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(16)
        )
        title_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=title_label.setter('color'))

        value1_label = Label(
            text=value1,
            font_size=theme_manager.typography.BODY2,
            halign='center',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        value1_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=value1_label.setter('color'))

        value2_label = Label(
            text=value2,
            font_size=theme_manager.typography.BODY2,
            halign='center',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        value2_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=value2_label.setter('color'))

        container.add_widget(title_label)
        container.add_widget(value1_label)
        container.add_widget(value2_label)

        return {'container': container, 'value1': value1_label, 'value2': value2_label}

    def _update_cols(self):
        width, _ = Window.size
        self.cards.cols = 1 if width < dp(900) else 2

    def _bootstrap_initial_state(self):
        settings = obfuscation_config_service.get_settings()
        self._apply_settings(settings)
        self._update_history()
        
        monitor_state = obfuscation_monitor_service.get_state()
        self._on_monitor_update(self, monitor_state)

    def _handle_mode_change(self, mode, enabled):
        if mode == 'standard':
            if enabled:
                self.maximum_switch.active = False
            self._save_setting('standard_mode_enabled', enabled)
        elif mode == 'maximum':
            if enabled:
                self.standard_switch.active = False
            self._save_setting('maximum_mode_enabled', enabled)

    def _handle_threshold_change(self, value):
        self.threshold_value.text = f'{int(value)}%'
        self._save_setting('auto_switch_threshold', int(value))

    def _handle_battery_threshold_change(self, value):
        self.battery_threshold_value.text = f'{int(value)}%'
        self._save_setting('battery_saver_threshold', int(value))

    def _handle_data_cap_change(self, value):
        self.data_cap_value.text = f'{int(value)} MB'
        self._save_setting('data_cap_mb', int(value))

    def _handle_schedule_mode_change(self, instance, text):
        mode_map = {
            '24/7': '24/7',
            'Specific Hours': 'specific',
            'Business Hours (9-5)': 'business',
            'Night Mode (22-6)': 'night'
        }
        
        mode = mode_map.get(text, '24/7')
        self._save_setting('schedule_mode', mode)

        if mode == 'business':
            self.start_hour_spinner.text = '9'
            self.end_hour_spinner.text = '17'
        elif mode == 'night':
            self.start_hour_spinner.text = '22'
            self.end_hour_spinner.text = '6'

    def _handle_time_change(self, instance, text):
        self._save_setting('schedule_start_hour', int(self.start_hour_spinner.text))
        self._save_setting('schedule_start_minute', int(self.start_minute_spinner.text))
        self._save_setting('schedule_end_hour', int(self.end_hour_spinner.text))
        self._save_setting('schedule_end_minute', int(self.end_minute_spinner.text))

    def _save_setting(self, key, value):
        obfuscation_config_service.update_settings(**{key: value})

    def _reset_session(self):
        obfuscation_config_service.reset_session_history()
        self._update_history()

    def _update_history(self):
        history = obfuscation_config_service.get_history()
        
        self.session_packets_label.text = f"{history.get('session_packets', 0):,} packets"
        self.session_data_label.text = f"{history.get('session_data_mb', 0):.2f} MB"
        
        self.today_packets_label.text = f"{history.get('today_packets', 0):,} packets"
        self.today_data_label.text = f"{history.get('today_data_mb', 0):.2f} MB"
        
        self.week_packets_label.text = f"{history.get('week_packets', 0):,} packets"
        self.week_data_label.text = f"{history.get('week_data_mb', 0):.2f} MB"

    @mainthread
    def _on_settings_update(self, instance, settings):
        self._apply_settings(settings)

    def _apply_settings(self, settings):
        self.standard_switch.active = settings.get('standard_mode_enabled', False)
        self.maximum_switch.active = settings.get('maximum_mode_enabled', False)
        self.auto_switch.active = settings.get('auto_switch_enabled', False)
        
        threshold = settings.get('auto_switch_threshold', 80)
        self.threshold_slider.value = threshold
        self.threshold_value.text = f'{threshold}%'

        battery_threshold = settings.get('battery_saver_threshold', 20)
        self.battery_threshold_slider.value = battery_threshold
        self.battery_threshold_value.text = f'{battery_threshold}%'

        data_cap = settings.get('data_cap_mb', 1000)
        self.data_cap_slider.value = data_cap
        self.data_cap_value.text = f'{data_cap} MB'

        self.battery_saver_switch.active = settings.get('battery_saver_enabled', True)
        self.network_quality_switch.active = settings.get('network_quality_awareness', True)
        self.data_cap_switch.active = settings.get('data_cap_enabled', False)

        self.start_hour_spinner.text = str(settings.get('schedule_start_hour', 9))
        self.start_minute_spinner.text = str(settings.get('schedule_start_minute', 0)).zfill(2)
        self.end_hour_spinner.text = str(settings.get('schedule_end_hour', 17))
        self.end_minute_spinner.text = str(settings.get('schedule_end_minute', 0)).zfill(2)

    @mainthread
    def _on_monitor_update(self, instance, state):
        self.packets_graph.update_data(state.get('packets_per_sec_history', []))
        
        self.cpu_bar.update_value(state.get('cpu_usage', 0))
        self.memory_bar.update_value(state.get('memory_usage', 0))
        self.battery_bar.update_value(state.get('battery_drain', 0))
        
        self.bandwidth_viz.update_bandwidth(
            state.get('bandwidth_in', 0),
            state.get('bandwidth_out', 0)
        )
        
        self.performance_widget.update_performance(
            state.get('model_accuracy', 0),
            state.get('model_latency', 0)
        )
        
        self.circuit_widget.update_circuits(state.get('active_circuits', 0))
        self.error_list.update_logs(state.get('error_log', []))

        self._update_history()

    @mainthread
    def _on_warning(self, instance, warning_type, message):
        print(f"[WARNING] {warning_type}: {message}")
