from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from src.theming.theme_manager import theme_manager

class Card(BoxLayout):
    def __init__(self, title="", content="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = theme_manager.spacing.M
        self.spacing = theme_manager.spacing.S
        
        # Bind to theme changes
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
            color=theme_manager.text_color
        )
        theme_manager.bind(text_color=self.title_label.setter('color'))
        
        self.content_label = Label(
            text=content,
            font_size=theme_manager.typography.BODY1,
            color=theme_manager.text_color
        )
        theme_manager.bind(text_color=self.content_label.setter('color'))
        
        self.add_widget(self.title_label)
        self.add_widget(self.content_label)

    def update_bg(self, instance, value):
        self.bg_color_instruction.rgba = value

    def update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
    def update_content(self, text):
        self.content_label.text = text
