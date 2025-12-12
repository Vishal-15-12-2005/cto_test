from kivy.event import EventDispatcher
from kivy.properties import ColorProperty, OptionProperty, ObjectProperty
from src.theming.tokens import ColorPalette, Typography, Spacing
from src.utils.event_bus import event_bus

class ThemeManager(EventDispatcher):
    _instance = None
    theme_mode = OptionProperty('light', options=['light', 'dark'])
    
    # Bindable Color Properties
    primary_color = ColorProperty(ColorPalette.PRIMARY)
    background_color = ColorProperty(ColorPalette.LIGHT_BACKGROUND)
    surface_color = ColorProperty(ColorPalette.LIGHT_SURFACE)
    text_color = ColorProperty(ColorPalette.LIGHT_ON_BACKGROUND)
    
    # Access to tokens
    typography = ObjectProperty(Typography)
    spacing = ObjectProperty(Spacing)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self, **kwargs):
        if hasattr(self, '_initialized'):
            return
        super().__init__(**kwargs)
        self.bind(theme_mode=self.update_theme_colors)
        self.update_theme_colors(self, self.theme_mode)
        self._initialized = True

    def update_theme_colors(self, instance, value):
        if value == 'light':
            self.background_color = ColorPalette.LIGHT_BACKGROUND
            self.surface_color = ColorPalette.LIGHT_SURFACE
            self.text_color = ColorPalette.LIGHT_ON_BACKGROUND
        else:
            self.background_color = ColorPalette.DARK_BACKGROUND
            self.surface_color = ColorPalette.DARK_SURFACE
            self.text_color = ColorPalette.DARK_ON_BACKGROUND
        
        event_bus.emit_theme_changed(value)

    def toggle_theme(self):
        if self.theme_mode == 'light':
            self.theme_mode = 'dark'
        else:
            self.theme_mode = 'light'

theme_manager = ThemeManager()
