from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from src.screens.maximum_ai_control_panel import MaximumAIControlPanel
from src.screens.status_dashboard import StatusDashboard
from src.screens.traffic_dashboard import TrafficDashboard
from src.screens.obfuscation_settings_screen import ObfuscationSettingsScreen
from src.screens.contacts_screen import ContactsScreen
from src.screens.messaging_screen import MessagingScreen
from src.services.tor_manager import tor_manager
from src.services.maximum_ai_manager import maximum_ai_manager
from src.services.smart_agent import smart_agent
from src.services.obfuscation_monitor_service import obfuscation_monitor_service
from src.services.contact_service import contact_service
from src.services.messaging_service import messaging_service
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
        contacts_screen = ContactsScreen()
        
        # Traffic Dashboard Screen
        traffic_dashboard = TrafficDashboard()
        
        max_ai_panel = MaximumAIControlPanel()
        
        # Obfuscation Settings & Monitoring Screen
        obfuscation_settings = ObfuscationSettingsScreen()
        
        # Messaging Screen
        messaging = MessagingScreen()

        # Add Navigation Items
        self.shell.add_nav_item(NavigationItem(
            name='dashboard',
            text='Dashboard',
            screen=dashboard,
        ))

        self.shell.add_nav_item(NavigationItem(
            name='contacts',
            text='Contacts',
            screen=contacts_screen,
        ))

        self.shell.add_nav_item(NavigationItem(
            name='maximum_ai',
            text='Maximum AI',
            screen=max_ai_panel,
        ))

        self.shell.add_nav_item(NavigationItem(
            name='traffic', 
            text='Traffic', 
            screen=traffic_dashboard
        ))
        
        self.shell.add_nav_item(NavigationItem(
            name='obfuscation',
            text='Obfuscation',
            screen=obfuscation_settings
        ))
        
        self.shell.add_nav_item(NavigationItem(
            name='messages',
            text='Messages',
            screen=messaging
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
        obfuscation_monitor_service.start_service()
        messaging_service.start_service()

    def on_stop(self):
        tor_manager.stop_service()
        maximum_ai_manager.stop_service()
        smart_agent.deactivate()
        obfuscation_monitor_service.stop_service()
        messaging_service.stop_service()

if __name__ == '__main__':
    MainApp().run()
