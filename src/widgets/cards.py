from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from src.theming.theme_manager import theme_manager


class Card(BoxLayout):
    def __init__(self, title="", content="", body=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = theme_manager.spacing.M
        self.spacing = theme_manager.spacing.S
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))

        theme_manager.bind(surface_color=self.update_bg)
        self.bind(pos=self.update_rect, size=self.update_rect)

        with self.canvas.before:
            self.bg_color_instruction = Color(rgba=theme_manager.surface_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.title_label = Label(
            text=title,
            font_size=theme_manager.typography.H6,
            size_hint_y=None,
            height=30,
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
        )
        self.title_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title_label.setter('color'))

        self.content_label = None
        self.body = body

        if body is None:
            self.content_label = Label(
                text=content,
                font_size=theme_manager.typography.BODY1,
                halign='left',
                valign='top',
                color=theme_manager.text_color,
            )
            self.content_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            theme_manager.bind(text_color=self.content_label.setter('color'))

        self.add_widget(self.title_label)
        if self.body is not None:
            self.add_widget(self.body)
        else:
            self.add_widget(self.content_label)

    def update_bg(self, instance, value):
        self.bg_color_instruction.rgba = value

    def update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def update_content(self, text):
        if self.content_label is None:
            return
        self.content_label.text = text
