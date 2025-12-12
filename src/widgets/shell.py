from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from src.theming.theme_manager import theme_manager

class NavigationItem:
    def __init__(self, name, text, icon=None, screen=None):
        self.name = name
        self.text = text
        self.screen = screen

class ResponsiveShell(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.nav_items = []
        
        # Screen Manager area
        self.screen_manager = ScreenManager()
        
        # Navigation bars (will be added/removed based on layout)
        self.bottom_nav = BoxLayout(size_hint_y=None, height=dp(56))
        self.side_nav = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(200))
        self.top_bar = BoxLayout(size_hint_y=None, height=dp(56))
        
        # Bind to window size
        Window.bind(size=self.on_window_resize)
        
        # Initial layout
        self.current_layout = None
        self.update_layout()
        
        # Bind theme
        theme_manager.bind(background_color=self.update_bg)
        with self.canvas.before:
            self.bg_color = Color(rgba=theme_manager.background_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_bg(self, instance, value):
        self.bg_color.rgba = value

    def update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def add_nav_item(self, item):
        self.nav_items.append(item)
        self.screen_manager.add_widget(item.screen)
        self.rebuild_nav_ui()

    def rebuild_nav_ui(self):
        self.bottom_nav.clear_widgets()
        self.side_nav.clear_widgets()
        
        for item in self.nav_items:
            # Bottom Nav Button
            btn_bottom = Button(text=item.text, on_release=lambda x, n=item.name: self.switch_screen(n))
            self.bottom_nav.add_widget(btn_bottom)
            
            # Side Nav Button
            btn_side = Button(text=item.text, size_hint_y=None, height=dp(48), on_release=lambda x, n=item.name: self.switch_screen(n))
            self.side_nav.add_widget(btn_side)

    def switch_screen(self, name):
        self.screen_manager.current = name

    def on_window_resize(self, window, size):
        self.update_layout()

    def update_layout(self):
        width, height = Window.size
        new_layout = 'mobile' if width < dp(600) else 'desktop'
        
        if self.current_layout == new_layout:
            return
            
        self.current_layout = new_layout
        self.clear_widgets()
        
        # Ensure screen_manager is removed from any previous parent
        if self.screen_manager.parent:
            self.screen_manager.parent.remove_widget(self.screen_manager)
        
        if new_layout == 'mobile':
            # Mobile: ScreenManager on top, BottomNav on bottom
            self.orientation = 'vertical'
            self.add_widget(self.screen_manager)
            self.add_widget(self.bottom_nav)
        else:
            # Desktop: Sidebar on left, (TopBar + ScreenManager) on right
            self.orientation = 'horizontal'
            self.add_widget(self.side_nav)
            
            content_area = BoxLayout(orientation='vertical')
            # Top Bar content
            self.top_bar.clear_widgets()
            title = Button(text="App Title", size_hint_x=None, width=dp(100), background_color=(0,0,0,0), color=theme_manager.text_color)
            theme_switch = Button(text="Toggle Theme", size_hint_x=None, width=dp(120), on_release=lambda x: theme_manager.toggle_theme())
            self.top_bar.add_widget(title)
            self.top_bar.add_widget(BoxLayout()) # Spacer
            self.top_bar.add_widget(theme_switch)
            
            content_area.add_widget(self.top_bar)
            content_area.add_widget(self.screen_manager)
            self.add_widget(content_area)
            
    def get_root_widget(self):
        return self
