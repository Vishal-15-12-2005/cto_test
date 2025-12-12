from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from src.screens.maximum_ai_control_panel import MaximumAIControlPanel
from src.screens.status_dashboard import StatusDashboard
from src.services.maximum_ai_manager import maximum_ai_manager
from src.services.smart_agent import smart_agent
from src.services.tor_manager import tor_manager
from src.widgets.shell import NavigationItem, ResponsiveShell

class PlaceholderScreen(Screen):
    def __init__(self, name, text, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.add_widget(Label(text=text))

class MainApp(App):
    def build(self):
        self.shell = ResponsiveShell()
        
        # Screens
        dashboard = StatusDashboard()
        max_ai_panel = MaximumAIControlPanel()

        # Add Navigation Items
        self.shell.add_nav_item(NavigationItem(
            name='dashboard',
            text='Dashboard',
            screen=dashboard,
        ))

        self.shell.add_nav_item(NavigationItem(
            name='maximum_ai',
            text='Maximum AI',
            screen=max_ai_panel,
        ))

        self.shell.add_nav_item(NavigationItem(
            name='settings',
            text='Settings',
            screen=PlaceholderScreen(name='settings', text="Settings Screen"),
        ))
        
        return self.shell

    def on_start(self):
        tor_manager.start_service()
        maximum_ai_manager.start_service()
        smart_agent.activate()

    def on_stop(self):
        tor_manager.stop_service()
        maximum_ai_manager.stop_service()
        smart_agent.deactivate()

if __name__ == '__main__':
    MainApp().run()
