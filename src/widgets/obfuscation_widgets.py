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
from kivy.uix.scrollview import ScrollView

from src.theming.theme_manager import theme_manager
from src.widgets.cards import Card


class ResourceBar(BoxLayout):
    def __init__(self, label_text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.size_hint_y = None
        self.height = dp(50)

        self.label = Label(
            text=label_text,
            font_size=theme_manager.typography.CAPTION,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(16)
        )
        self.label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.label.setter('color'))

        bar_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        
        self.bar_widget = Widget(size_hint_y=None, height=dp(20))
        self.bar_widget.bind(pos=self._redraw, size=self._redraw)
        
        with self.bar_widget.canvas.before:
            Color(rgba=[0.3, 0.3, 0.3, 1])
            self.bg_rect = Rectangle(pos=self.bar_widget.pos, size=self.bar_widget.size)

        self.value_label = Label(
            text='0%',
            font_size=theme_manager.typography.CAPTION,
            halign='right',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=None,
            width=dp(50)
        )
        theme_manager.bind(text_color=self.value_label.setter('color'))

        bar_container.add_widget(self.bar_widget)
        bar_container.add_widget(self.value_label)

        self.add_widget(self.label)
        self.add_widget(bar_container)

        self._value = 0

    def update_value(self, value):
        self._value = max(0, min(100, value))
        self.value_label.text = f'{int(self._value)}%'
        self._redraw()

    def _redraw(self, *args):
        self.bg_rect.pos = self.bar_widget.pos
        self.bg_rect.size = self.bar_widget.size
        
        self.bar_widget.canvas.after.clear()
        with self.bar_widget.canvas.after:
            if self._value < 40:
                Color(0.2, 0.75, 0.35, 1)
            elif self._value < 70:
                Color(0.95, 0.7, 0.2, 1)
            else:
                Color(0.9, 0.25, 0.25, 1)
            
            bar_width = (self._value / 100) * self.bar_widget.width
            Rectangle(pos=self.bar_widget.pos, size=[bar_width, self.bar_widget.height])


class PacketsGraph(Widget):
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
        self.data = data[-30:] if len(data) > 30 else data
        self._redraw()

    def _redraw(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.canvas.after.clear()

        if not self.data or len(self.data) < 2:
            return

        with self.canvas.after:
            Color(0.3, 0.6, 0.9, 1)
            points = []
            max_val = max(self.data) if self.data else 1
            width = self.width
            height = self.height - dp(20)

            for i, val in enumerate(self.data):
                x = self.x + (i / max(len(self.data) - 1, 1)) * width
                y = self.y + dp(10) + (val / max(max_val, 1)) * height
                points.extend([x, y])

            if len(points) >= 4:
                Line(points=points, width=dp(2))


class BandwidthVisualization(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(100)

        self.in_bar = self._create_bandwidth_bar('Inbound', [0.2, 0.75, 0.35, 1])
        self.out_bar = self._create_bandwidth_bar('Outbound', [0.3, 0.6, 0.9, 1])

        self.add_widget(self.in_bar['container'])
        self.add_widget(self.out_bar['container'])

    def _create_bandwidth_bar(self, label_text, color):
        container = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        
        label = Label(
            text=label_text,
            font_size=theme_manager.typography.CAPTION,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=0.25
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=label.setter('color'))

        bar_widget = Widget()
        bar_widget.bind(pos=lambda *args: self._redraw_bar(bar_widget, color, 0), 
                       size=lambda *args: self._redraw_bar(bar_widget, color, 0))
        
        with bar_widget.canvas.before:
            Color(rgba=[0.3, 0.3, 0.3, 1])
            bg_rect = Rectangle(pos=bar_widget.pos, size=bar_widget.size)
        
        value_label = Label(
            text='0.0 Mbps',
            font_size=theme_manager.typography.CAPTION,
            halign='right',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=None,
            width=dp(80)
        )
        theme_manager.bind(text_color=value_label.setter('color'))

        container.add_widget(label)
        container.add_widget(bar_widget)
        container.add_widget(value_label)

        return {
            'container': container,
            'widget': bar_widget,
            'label': value_label,
            'color': color,
            'bg_rect': bg_rect,
            'value': 0
        }

    def _redraw_bar(self, bar_widget, color, value):
        pass

    def update_bandwidth(self, bandwidth_in, bandwidth_out):
        self.in_bar['value'] = bandwidth_in
        self.in_bar['label'].text = f'{bandwidth_in:.2f} Mbps'
        self._update_bar(self.in_bar)

        self.out_bar['value'] = bandwidth_out
        self.out_bar['label'].text = f'{bandwidth_out:.2f} Mbps'
        self._update_bar(self.out_bar)

    def _update_bar(self, bar_info):
        widget = bar_info['widget']
        color = bar_info['color']
        value = bar_info['value']
        max_val = 10.0

        bar_info['bg_rect'].pos = widget.pos
        bar_info['bg_rect'].size = widget.size

        widget.canvas.after.clear()
        with widget.canvas.after:
            Color(*color)
            bar_width = min((value / max_val) * widget.width, widget.width)
            Rectangle(pos=widget.pos, size=[bar_width, widget.height])


class ErrorLogList(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(150)

        scroll = ScrollView(do_scroll_x=False, size_hint_y=None, height=dp(150))
        self.log_container = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None)
        self.log_container.bind(minimum_height=self.log_container.setter('height'))
        scroll.add_widget(self.log_container)
        self.add_widget(scroll)

    def update_logs(self, error_log):
        self.log_container.clear_widgets()
        
        if not error_log:
            placeholder = Label(
                text='No errors logged',
                font_size=theme_manager.typography.CAPTION,
                halign='left',
                valign='middle',
                color=theme_manager.text_color,
                size_hint_y=None,
                height=dp(30)
            )
            placeholder.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            theme_manager.bind(text_color=placeholder.setter('color'))
            self.log_container.add_widget(placeholder)
            return

        import time
        for entry in error_log[:10]:
            timestamp = entry.get('timestamp', 0)
            message = entry.get('message', '')
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            
            log_entry = Label(
                text=f'[{time_str}] {message}',
                font_size=theme_manager.typography.CAPTION,
                halign='left',
                valign='middle',
                color=[0.9, 0.6, 0.2, 1],
                size_hint_y=None,
                height=dp(24)
            )
            log_entry.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            self.log_container.add_widget(log_entry)


class CircuitStatusWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(16)
        self.size_hint_y = None
        self.height = dp(60)

        left_col = BoxLayout(orientation='vertical', spacing=dp(4))
        
        label = Label(
            text='Active Tor Circuits',
            font_size=theme_manager.typography.CAPTION,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(16)
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=label.setter('color'))

        self.circuit_value = Label(
            text='0',
            font_size=theme_manager.typography.H4,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        self.circuit_value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.circuit_value.setter('color'))

        left_col.add_widget(label)
        left_col.add_widget(self.circuit_value)

        self.add_widget(left_col)

    def update_circuits(self, count):
        self.circuit_value.text = str(count)


class ModelPerformanceWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(80)

        accuracy_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(32))
        accuracy_label = Label(
            text='Model Accuracy:',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=0.5
        )
        accuracy_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=accuracy_label.setter('color'))

        self.accuracy_value = Label(
            text='0%',
            font_size=theme_manager.typography.BODY2,
            halign='right',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        self.accuracy_value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.accuracy_value.setter('color'))

        accuracy_row.add_widget(accuracy_label)
        accuracy_row.add_widget(self.accuracy_value)

        latency_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(32))
        latency_label = Label(
            text='Model Latency:',
            font_size=theme_manager.typography.BODY2,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
            size_hint_x=0.5
        )
        latency_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=latency_label.setter('color'))

        self.latency_value = Label(
            text='0ms',
            font_size=theme_manager.typography.BODY2,
            halign='right',
            valign='middle',
            color=theme_manager.text_color,
            bold=True
        )
        self.latency_value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.latency_value.setter('color'))

        latency_row.add_widget(latency_label)
        latency_row.add_widget(self.latency_value)

        self.add_widget(accuracy_row)
        self.add_widget(latency_row)

    def update_performance(self, accuracy, latency):
        self.accuracy_value.text = f'{accuracy:.1f}%'
        self.latency_value.text = f'{latency}ms'
