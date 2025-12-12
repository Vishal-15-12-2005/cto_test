from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup

from src.theming.theme_manager import theme_manager
from src.widgets.cards import Card
from src.widgets.tor_dashboard_widgets import Dot


class TrafficModeIndicator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(32)

        self.dot = Dot()
        self.label = Label(
            text='Off',
            font_size=theme_manager.typography.H6,
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.label.setter('color'))

        self.add_widget(self.dot)
        self.add_widget(self.label)

    def update_mode(self, mode):
        mode_colors = {
            'off': [0.6, 0.6, 0.6, 1],
            'standard': [0.2, 0.75, 0.35, 1],
            'maximum': [0.9, 0.25, 0.25, 1]
        }
        self.dot.rgba = mode_colors.get(mode, [0.6, 0.6, 0.6, 1])
        self.label.text = mode.title()


class MetricDisplay(BoxLayout):
    def __init__(self, label_text, value_text='—', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.size_hint_y = None
        self.height = dp(50)

        self.title = Label(
            text=label_text,
            font_size=theme_manager.typography.CAPTION,
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))

        self.value = Label(
            text=value_text,
            font_size=theme_manager.typography.H5,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        self.value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.value.setter('color'))

        self.add_widget(self.title)
        self.add_widget(self.value)

    def update_value(self, text):
        self.value.text = str(text)


class TrafficRateGraph(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(150)
        self.data = []
        self.bind(pos=self._redraw, size=self._redraw)

        with self.canvas.before:
            Color(rgba=theme_manager.surface_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def update_data(self, data):
        self.data = data[-20:] if len(data) > 20 else data
        self._redraw()

    def _redraw(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.canvas.after.clear()

        if not self.data or len(self.data) < 2:
            return

        with self.canvas.after:
            Color(0.2, 0.75, 0.35, 1)
            points = []
            max_val = max(self.data) if self.data else 1
            width = self.width
            height = self.height - dp(20)

            for i, val in enumerate(self.data):
                x = self.x + (i / max(len(self.data) - 1, 1)) * width
                y = self.y + dp(10) + (val / max_val) * height
                points.extend([x, y])

            if len(points) >= 4:
                Line(points=points, width=dp(2))


class SchedulingModal(Popup):
    def __init__(self, on_save=None, start_time=None, end_time=None, **kwargs):
        self.on_save_callback = on_save
        self.start_time = start_time or (9, 0)
        self.end_time = end_time or (17, 0)

        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))

        content.add_widget(Label(
            text='Schedule Standard AI',
            font_size=theme_manager.typography.H6,
            size_hint_y=None,
            height=dp(30)
        ))

        start_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        start_row.add_widget(Label(text='Start Time:', size_hint_x=0.3))
        self.start_hour = Spinner(
            text=str(self.start_time[0]),
            values=[str(i) for i in range(24)],
            size_hint_x=0.35
        )
        self.start_minute = Spinner(
            text=str(self.start_time[1]).zfill(2),
            values=[str(i).zfill(2) for i in range(0, 60, 15)],
            size_hint_x=0.35
        )
        start_row.add_widget(self.start_hour)
        start_row.add_widget(self.start_minute)

        end_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        end_row.add_widget(Label(text='End Time:', size_hint_x=0.3))
        self.end_hour = Spinner(
            text=str(self.end_time[0]),
            values=[str(i) for i in range(24)],
            size_hint_x=0.35
        )
        self.end_minute = Spinner(
            text=str(self.end_time[1]).zfill(2),
            values=[str(i).zfill(2) for i in range(0, 60, 15)],
            size_hint_x=0.35
        )
        end_row.add_widget(self.end_hour)
        end_row.add_widget(self.end_minute)

        btn_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        cancel_btn = Button(text='Cancel', on_release=lambda *_: self.dismiss())
        save_btn = Button(text='Save', on_release=lambda *_: self._save())
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)

        content.add_widget(start_row)
        content.add_widget(end_row)
        content.add_widget(btn_row)

        super().__init__(
            title='Configure Schedule',
            content=content,
            size_hint=(0.9, 0.5),
            **kwargs
        )

    def _save(self):
        if self.on_save_callback:
            start = (int(self.start_hour.text), int(self.start_minute.text))
            end = (int(self.end_hour.text), int(self.end_minute.text))
            self.on_save_callback(start, end)
        self.dismiss()


class StandardAIControlsCard(Card):
    def __init__(self, on_toggle=None, on_settings_change=None, **kwargs):
        self._on_toggle = on_toggle
        self._on_settings_change = on_settings_change
        self._updating = False

        body = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        toggle_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        self.toggle_label = Label(
            text='Standard AI',
            font_size=theme_manager.typography.SUBTITLE1,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        self.toggle_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.toggle_label.setter('color'))

        self.toggle_switch = Switch(active=False)
        self.toggle_switch.bind(active=self._handle_toggle)

        toggle_row.add_widget(self.toggle_label)
        toggle_row.add_widget(BoxLayout())
        toggle_row.add_widget(self.toggle_switch)

        noise_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.noise_label = Label(
            text='Background Noise',
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.noise_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.noise_label.setter('color'))

        self.noise_switch = Switch(active=False)
        self.noise_switch.bind(active=self._handle_noise_change)

        noise_row.add_widget(self.noise_label)
        noise_row.add_widget(BoxLayout())
        noise_row.add_widget(self.noise_switch)

        intensity_label = Label(
            text='Intensity',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        intensity_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=intensity_label.setter('color'))

        intensity_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        self.intensity_slider = Slider(min=0, max=100, value=50, step=1)
        self.intensity_slider.bind(value=self._handle_intensity_change)
        self.intensity_value = Label(text='50%', size_hint_x=None, width=dp(50))
        intensity_row.add_widget(self.intensity_slider)
        intensity_row.add_widget(self.intensity_value)

        freq_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        freq_label = Label(text='Frequency Range:', size_hint_x=0.4)
        self.freq_spinner = Spinner(
            text='Medium',
            values=['Low', 'Medium', 'High'],
            size_hint_x=0.6
        )
        self.freq_spinner.bind(text=self._handle_freq_change)
        freq_row.add_widget(freq_label)
        freq_row.add_widget(self.freq_spinner)

        schedule_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        self.schedule_label = Label(
            text='Schedule',
            halign='left',
            valign='middle',
            color=theme_manager.text_color
        )
        self.schedule_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.schedule_label.setter('color'))

        self.schedule_switch = Switch(active=False)
        self.schedule_switch.bind(active=self._handle_schedule_toggle)

        self.schedule_btn = Button(
            text='Configure',
            size_hint_x=None,
            width=dp(100),
            on_release=lambda *_: self._open_schedule_modal()
        )

        schedule_row.add_widget(self.schedule_label)
        schedule_row.add_widget(BoxLayout())
        schedule_row.add_widget(self.schedule_switch)
        schedule_row.add_widget(self.schedule_btn)

        sites_label = Label(
            text='Sample Sites Preview',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(24)
        )
        sites_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=sites_label.setter('color'))

        self.sites_container = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
            height=dp(80)
        )

        self.battery_banner = Label(
            text='Battery Impact: Low',
            font_size=theme_manager.typography.CAPTION,
            halign='center',
            valign='middle',
            color=[1, 1, 1, 1],
            size_hint_y=None,
            height=dp(28)
        )
        self.battery_banner.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        with self.battery_banner.canvas.before:
            self.banner_color = Color(rgba=[0.2, 0.75, 0.35, 1])
            self.banner_rect = Rectangle(pos=self.battery_banner.pos, size=self.battery_banner.size)

        self.battery_banner.bind(pos=self._update_banner_rect, size=self._update_banner_rect)

        body.add_widget(toggle_row)
        body.add_widget(noise_row)
        body.add_widget(intensity_label)
        body.add_widget(intensity_row)
        body.add_widget(freq_row)
        body.add_widget(schedule_row)
        body.add_widget(sites_label)
        body.add_widget(self.sites_container)
        body.add_widget(self.battery_banner)

        super().__init__(title='Standard AI Controls', body=body, **kwargs)

        self.schedule_config = {'start': (9, 0), 'end': (17, 0)}

    def _update_banner_rect(self, *args):
        self.banner_rect.pos = self.battery_banner.pos
        self.banner_rect.size = self.battery_banner.size

    def _handle_toggle(self, instance, value):
        if self._updating:
            return
        if self._on_toggle:
            self._on_toggle(bool(value))

    def _handle_noise_change(self, instance, value):
        if self._updating:
            return
        if self._on_settings_change:
            self._on_settings_change('background_noise', bool(value))

    def _handle_intensity_change(self, instance, value):
        self.intensity_value.text = f'{int(value)}%'
        if self._updating:
            return
        if self._on_settings_change:
            self._on_settings_change('intensity', int(value))

    def _handle_freq_change(self, instance, value):
        if self._updating:
            return
        if self._on_settings_change:
            self._on_settings_change('frequency_range', value.lower())

    def _handle_schedule_toggle(self, instance, value):
        if self._updating:
            return
        if self._on_settings_change:
            self._on_settings_change('scheduling_enabled', bool(value))

    def _open_schedule_modal(self):
        from datetime import time
        start = time(*self.schedule_config['start'])
        end = time(*self.schedule_config['end'])

        modal = SchedulingModal(
            on_save=self._save_schedule,
            start_time=self.schedule_config['start'],
            end_time=self.schedule_config['end']
        )
        modal.open()

    def _save_schedule(self, start, end):
        self.schedule_config['start'] = start
        self.schedule_config['end'] = end
        if self._on_settings_change:
            self._on_settings_change('schedule', (start, end))

    def update_sites(self, sites):
        self.sites_container.clear_widgets()
        for site in sites[:4]:
            lbl = Label(
                text=f'• {site}',
                font_size=theme_manager.typography.CAPTION,
                halign='left',
                valign='middle',
                color=theme_manager.text_color,
                size_hint_y=None,
                height=dp(18)
            )
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            theme_manager.bind(text_color=lbl.setter('color'))
            self.sites_container.add_widget(lbl)

    def update_battery_impact(self, impact):
        if impact < 30:
            self.battery_banner.text = f'Battery Impact: Low ({impact}%)'
            self.banner_color.rgba = [0.2, 0.75, 0.35, 1]
        elif impact < 60:
            self.battery_banner.text = f'Battery Impact: Medium ({impact}%)'
            self.banner_color.rgba = [0.95, 0.7, 0.2, 1]
        else:
            self.battery_banner.text = f'Battery Impact: High ({impact}%)'
            self.banner_color.rgba = [0.9, 0.25, 0.25, 1]

    def apply_state(self, state):
        self._updating = True

        self.toggle_switch.active = state.get('standard_ai_enabled', False)
        self.noise_switch.active = state.get('background_noise', False)
        
        intensity = state.get('intensity', 50)
        self.intensity_slider.value = intensity
        self.intensity_value.text = f'{int(intensity)}%'

        freq = state.get('frequency_range', 'medium')
        self.freq_spinner.text = freq.title()

        self.schedule_switch.active = state.get('scheduling_enabled', False)

        sites = state.get('sample_sites', [])
        self.update_sites(sites)

        battery_impact = state.get('battery_impact', 0)
        self.update_battery_impact(battery_impact)

        self._updating = False
