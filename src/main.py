from kivy.app import App
from src.widgets.shell import ResponsiveShell, NavigationItem
from src.screens.status_dashboard import StatusDashboard
from src.services.tor_manager import tor_manager
from src.services.smart_agent import smart_agent
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label

class PlaceholderScreen(Screen):
    def __init__(self, name, text, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.add_widget(Label(text=text))

class MainApp(App):
    def build(self):
        self.shell = ResponsiveShell()
        
        # Dashboard Screen
        dashboard = StatusDashboard()
        
        # Add Navigation Items
        self.shell.add_nav_item(NavigationItem(
            name='dashboard', 
            text='Dashboard', 
            screen=dashboard
        ))
        
        self.shell.add_nav_item(NavigationItem(
            name='settings', 
            text='Settings', 
            screen=PlaceholderScreen(name='settings', text="Settings Screen")
        ))
        
        return self.shell

    def on_start(self):
        # Start Services
        tor_manager.start_service()
        smart_agent.activate()

    def on_stop(self):
        tor_manager.stop_service()
        smart_agent.deactivate()

if __name__ == '__main__':
    MainApp().run()
