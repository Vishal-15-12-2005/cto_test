from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from src.services.preferences_store import preferences_store
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.cards import Card


class PrivacySettingsTab(BoxLayout):
    """Privacy settings section with data retention and encryption controls."""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(16), padding=[dp(20), dp(16)], **kwargs)
        
        # Data Retention Controls
        retention_card = Card(title='Data Retention')
        retention_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(120))
        
        # Message TTL
        message_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        message_label = Label(text='Message TTL (days)', size_hint_x=0.4, color=theme_manager.text_color)
        self.message_slider = Slider(min=1, max=365, value=preferences_store.data_retention_days, size_hint_x=0.4)
        self.message_value_label = Label(text=str(preferences_store.data_retention_days), size_hint_x=0.2, color=theme_manager.text_color)
        
        self.message_slider.bind(value=lambda inst, val: self._update_message_value(val))
        message_row.extend([message_label, self.message_slider, self.message_value_label])
        
        # File TTL  
        file_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        file_label = Label(text='File TTL (days)', size_hint_x=0.4, color=theme_manager.text_color)
        self.file_slider = Slider(min=1, max=90, value=preferences_store.file_retention_days, size_hint_x=0.4)
        self.file_value_label = Label(text=str(preferences_store.file_retention_days), size_hint_x=0.2, color=theme_manager.text_color)
        
        self.file_slider.bind(value=lambda inst, val: self._update_file_value(val))
        file_row.extend([file_label, self.file_slider, self.file_value_label])
        
        retention_layout.extend([message_row, file_row])
        retention_card.add_widget(retention_layout)
        self.add_widget(retention_card)
        
        # Encryption & Security Controls
        security_card = Card(title='Encryption & Security')
        security_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        
        # Enforce maximum security
        max_security_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        max_security_label = Label(text='Enforce Maximum Security', size_hint_x=0.6, color=theme_manager.text_color)
        self.max_security_switch = Switch(active=preferences_store.enforce_max_security, size_hint_x=0.4)
        self.max_security_switch.bind(active=lambda inst, val: preferences_store.set_preference('enforce_max_security', val))
        max_security_row.extend([max_security_label, self.max_security_switch])
        
        # Metadata pruning
        metadata_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        metadata_label = Label(text='Metadata Pruning', size_hint_x=0.6, color=theme_manager.text_color)
        self.metadata_switch = Switch(active=preferences_store.metadata_pruning, size_hint_x=0.4)
        self.metadata_switch.bind(active=lambda inst, val: preferences_store.set_preference('metadata_pruning', val))
        metadata_row.extend([metadata_label, self.metadata_switch])
        
        # Auto cleanup
        cleanup_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        cleanup_label = Label(text='Automatic Cleanup', size_hint_x=0.6, color=theme_manager.text_color)
        self.cleanup_switch = Switch(active=preferences_store.auto_cleanup_enabled, size_hint_x=0.4)
        self.cleanup_switch.bind(active=lambda inst, val: preferences_store.set_preference('auto_cleanup_enabled', val))
        cleanup_row.extend([cleanup_label, self.cleanup_switch])
        
        security_layout.extend([max_security_row, metadata_row, cleanup_row])
        security_card.add_widget(security_layout)
        self.add_widget(security_card)
        
        # Privacy Indicators
        privacy_card = Card(title='Privacy Indicators')
        privacy_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(80))
        
        # Show connection status
        connection_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        connection_label = Label(text='Show Connection Status', size_hint_x=0.6, color=theme_manager.text_color)
        self.connection_switch = Switch(active=preferences_store.show_connection_status, size_hint_x=0.4)
        self.connection_switch.bind(active=lambda inst, val: preferences_store.set_preference('show_connection_status', val))
        connection_row.extend([connection_label, self.connection_switch])
        
        privacy_layout.add_widget(connection_row)
        privacy_card.add_widget(privacy_layout)
        self.add_widget(privacy_card)

    def _update_message_value(self, value):
        self.message_value_label.text = str(int(value))
        preferences_store.set_preference('data_retention_days', int(value))

    def _update_file_value(self, value):
        self.file_value_label.text = str(int(value))
        preferences_store.set_preference('file_retention_days', int(value))


class NotificationsSettingsTab(BoxLayout):
    """Notifications settings section with toggles and quiet hours controls."""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(16), padding=[dp(20), dp(16)], **kwargs)
        
        # General Notification Controls
        general_card = Card(title='General Notifications')
        general_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        
        # Notifications enabled
        enabled_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        enabled_label = Label(text='Enable Notifications', size_hint_x=0.6, color=theme_manager.text_color)
        self.enabled_switch = Switch(active=preferences_store.notifications_enabled, size_hint_x=0.4)
        self.enabled_switch.bind(active=lambda inst, val: preferences_store.set_preference('notifications_enabled', val))
        enabled_row.extend([enabled_label, self.enabled_switch])
        
        # Sound enabled
        sound_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        sound_label = Label(text='Sound Notifications', size_hint_x=0.6, color=theme_manager.text_color)
        self.sound_switch = Switch(active=preferences_store.sound_enabled, size_hint_x=0.4)
        self.sound_switch.bind(active=lambda inst, val: preferences_store.set_preference('sound_enabled', val))
        sound_row.extend([sound_label, self.sound_switch])
        
        # Vibration enabled
        vibration_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        vibration_label = Label(text='Vibration/Haptics', size_hint_x=0.6, color=theme_manager.text_color)
        self.vibration_switch = Switch(active=preferences_store.vibration_enabled, size_hint_x=0.4)
        self.vibration_switch.bind(active=lambda inst, val: preferences_store.set_preference('vibration_enabled', val))
        vibration_row.extend([vibration_label, self.vibration_switch])
        
        general_layout.extend([enabled_row, sound_row, vibration_row])
        general_card.add_widget(general_layout)
        self.add_widget(general_card)
        
        # Quiet Hours
        quiet_card = Card(title='Quiet Hours')
        quiet_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        
        # Quiet hours enabled
        quiet_enabled_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        quiet_enabled_label = Label(text='Enable Quiet Hours', size_hint_x=0.6, color=theme_manager.text_color)
        self.quiet_enabled_switch = Switch(active=preferences_store.quiet_hours_enabled, size_hint_x=0.4)
        self.quiet_enabled_switch.bind(active=lambda inst, val: preferences_store.set_preference('quiet_hours_enabled', val))
        quiet_enabled_row.extend([quiet_enabled_label, self.quiet_enabled_switch])
        
        # Time inputs
        time_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(60))
        
        # Start time
        start_layout = BoxLayout(orientation='vertical', size_hint_x=0.4)
        start_label = Label(text='Start Time', size_hint_y=0.4, color=theme_manager.text_color)
        self.start_time_input = TextInput(
            text=preferences_store.quiet_hours_start, 
            multiline=False, 
            size_hint_y=0.6,
            halign='center'
        )
        self.start_time_input.bind(text=lambda inst, val: preferences_store.set_preference('quiet_hours_start', val))
        start_layout.extend([start_label, self.start_time_input])
        
        # End time  
        end_layout = BoxLayout(orientation='vertical', size_hint_x=0.4)
        end_label = Label(text='End Time', size_hint_y=0.4, color=theme_manager.text_color)
        self.end_time_input = TextInput(
            text=preferences_store.quiet_hours_end, 
            multiline=False, 
            size_hint_y=0.6,
            halign='center'
        )
        self.end_time_input.bind(text=lambda inst, val: preferences_store.set_preference('quiet_hours_end', val))
        end_layout.extend([end_label, self.end_time_input])
        
        time_row.extend([BoxLayout(), start_layout, end_layout, BoxLayout()])
        
        quiet_layout.extend([quiet_enabled_row, time_row])
        quiet_card.add_widget(quiet_layout)
        self.add_widget(quiet_card)
        
        # Content Behavior
        content_card = Card(title='Content Behavior')
        content_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(80))
        
        # Content preview
        preview_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        preview_label = Label(text='Show Content Preview', size_hint_x=0.6, color=theme_manager.text_color)
        self.preview_switch = Switch(active=preferences_store.content_preview_enabled, size_hint_x=0.4)
        self.preview_switch.bind(active=lambda inst, val: preferences_store.set_preference('content_preview_enabled', val))
        preview_row.extend([preview_label, self.preview_switch])
        
        content_layout.add_widget(preview_row)
        content_card.add_widget(content_layout)
        self.add_widget(content_card)


class AppearanceSettingsTab(BoxLayout):
    """Appearance settings section with theme and styling controls."""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(16), padding=[dp(20), dp(16)], **kwargs)
        
        # Theme Controls
        theme_card = Card(title='Theme')
        theme_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        
        # Theme mode selection
        mode_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))
        mode_label = Label(text='Theme Mode', size_hint_x=0.4, color=theme_manager.text_color)
        
        theme_buttons = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_x=0.6)
        
        self.light_btn = Button(
            text='Light',
            size_hint_x=0.33,
            on_release=lambda *_: self._set_theme_mode('light')
        )
        self.dark_btn = Button(
            text='Dark', 
            size_hint_x=0.33,
            on_release=lambda *_: self._set_theme_mode('dark')
        )
        self.system_btn = Button(
            text='System',
            size_hint_x=0.33,
            on_release=lambda *_: self._set_theme_mode('system')
        )
        
        theme_buttons.extend([self.light_btn, self.dark_btn, self.system_btn])
        mode_row.extend([mode_label, theme_buttons])
        
        # Accent color
        color_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))
        color_label = Label(text='Accent Color', size_hint_x=0.4, color=theme_manager.text_color)
        self.color_input = TextInput(
            text=preferences_store.accent_color,
            multiline=False,
            size_hint_x=0.4
        )
        self.color_input.bind(text=lambda inst, val: self._update_accent_color(val))
        color_preview = Button(text='Preview', size_hint_x=0.2)
        color_preview.background_color = self._hex_to_rgba(preferences_store.accent_color)
        color_preview.bind(on_release=lambda *_: self._apply_accent_color())
        
        color_row.extend([color_label, self.color_input, color_preview])
        
        theme_layout.extend([mode_row, color_row])
        theme_card.add_widget(theme_layout)
        self.add_widget(theme_card)
        
        # Display Settings
        display_card = Card(title='Display')
        display_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        
        # Font size
        font_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))
        font_label = Label(text=f'Font Size ({preferences_store.font_size_scale:.1f}x)', size_hint_x=0.4, color=theme_manager.text_color)
        self.font_slider = Slider(min=0.8, max=1.5, value=preferences_store.font_size_scale, size_hint_x=0.4)
        self.font_slider.bind(value=lambda inst, val: self._update_font_scale(val))
        font_row.extend([font_label, self.font_slider, BoxLayout(size_hint_x=0.2)])
        
        # Layout density
        density_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))
        density_label = Label(text='Layout Density', size_hint_x=0.4, color=theme_manager.text_color)
        
        density_buttons = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_x=0.6)
        self.compact_btn = Button(
            text='Compact',
            size_hint_x=0.5,
            on_release=lambda *_: self._set_layout_density('compact')
        )
        self.comfortable_btn = Button(
            text='Comfortable',
            size_hint_x=0.5, 
            on_release=lambda *_: self._set_layout_density('comfortable')
        )
        
        density_buttons.extend([self.compact_btn, self.comfortable_btn])
        density_row.extend([density_label, density_buttons])
        
        display_layout.extend([font_row, density_row])
        display_card.add_widget(display_layout)
        self.add_widget(display_card)
        
        # Update button states
        Clock.schedule_once(lambda dt: self._update_theme_buttons(), 0)

    def _set_theme_mode(self, mode):
        preferences_store.set_preference('theme_mode', mode)
        # Apply theme change immediately
        if mode in ['light', 'dark']:
            theme_manager.theme_mode = mode
        self._update_theme_buttons()

    def _update_accent_color(self, color):
        preferences_store.set_preference('accent_color', color)

    def _apply_accent_color(self):
        color = self.color_input.text
        if self._is_valid_hex_color(color):
            # This would update theme colors - for now just preview
            pass

    def _update_font_scale(self, scale):
        font_label = self.font_slider.parent.children[2]  # Label is first child in horizontal layout
        font_label.text = f'Font Size ({scale:.1f}x)'
        preferences_store.set_preference('font_size_scale', scale)

    def _set_layout_density(self, density):
        preferences_store.set_preference('layout_density', density)
        self._update_density_buttons()

    def _update_theme_buttons(self):
        current_mode = preferences_store.theme_mode
        
        # Reset all buttons
        for btn in [self.light_btn, self.dark_btn, self.system_btn]:
            btn.background_color = [0.2, 0.2, 0.2, 1]
        
        # Highlight current mode
        if current_mode == 'light':
            self.light_btn.background_color = [0.3, 0.6, 1, 1]
        elif current_mode == 'dark':
            self.dark_btn.background_color = [0.3, 0.6, 1, 1]
        elif current_mode == 'system':
            self.system_btn.background_color = [0.3, 0.6, 1, 1]

    def _update_density_buttons(self):
        current_density = preferences_store.layout_density
        
        # Reset all buttons
        self.compact_btn.background_color = [0.2, 0.2, 0.2, 1]
        self.comfortable_btn.background_color = [0.2, 0.2, 0.2, 1]
        
        # Highlight current density
        if current_density == 'compact':
            self.compact_btn.background_color = [0.3, 0.6, 1, 1]
        else:
            self.comfortable_btn.background_color = [0.3, 0.6, 1, 1]

    def _hex_to_rgba(self, hex_color):
        """Convert hex color to RGBA tuple for Kivy."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return [r/255.0, g/255.0, b/255.0, 1.0]
        return [0.3, 0.6, 1, 1]  # Default blue

    def _is_valid_hex_color(self, color):
        """Check if color is a valid hex color."""
        try:
            int(color.lstrip('#'), 16)
            return len(color.lstrip('#')) == 6
        except ValueError:
            return False


class AccountSettingsTab(BoxLayout):
    """Account settings section with username, sessions, and data management."""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(16), padding=[dp(20), dp(16)], **kwargs)
        
        # Account Info
        account_card = Card(title='Account Information')
        account_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(120))
        
        # Username
        username_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))
        username_label = Label(text='Username', size_hint_x=0.3, color=theme_manager.text_color)
        self.username_input = TextInput(
            text=preferences_store.username,
            multiline=False,
            size_hint_x=0.7
        )
        self.username_input.bind(text=lambda inst, val: preferences_store.set_preference('username', val))
        username_row.extend([username_label, self.username_input])
        
        account_layout.add_widget(username_row)
        account_card.add_widget(account_layout)
        self.add_widget(account_card)
        
        # Data Management
        data_card = Card(title='Data Management')
        data_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(200))
        
        # Auto backup
        backup_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        backup_label = Label(text='Automatic Backup', size_hint_x=0.6, color=theme_manager.text_color)
        self.backup_switch = Switch(active=preferences_store.auto_backup_enabled, size_hint_x=0.4)
        self.backup_switch.bind(active=lambda inst, val: preferences_store.set_preference('auto_backup_enabled', val))
        backup_row.extend([backup_label, self.backup_switch])
        
        # Export/Import buttons
        export_import_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(60))
        
        export_btn = Button(
            text='Export Contacts',
            size_hint_x=0.5,
            on_release=lambda *_: self._export_contacts()
        )
        import_btn = Button(
            text='Import Contacts', 
            size_hint_x=0.5,
            on_release=lambda *_: self._import_contacts()
        )
        
        export_import_row.extend([export_btn, import_btn])
        
        data_layout.extend([backup_row, export_import_row])
        data_card.add_widget(data_layout)
        self.add_widget(data_card)
        
        # Session Management
        session_card = Card(title='Session Management')
        session_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(200))
        
        # Session management toggle
        session_toggle_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(40))
        session_toggle_label = Label(text='Enable Session Management', size_hint_x=0.6, color=theme_manager.text_color)
        self.session_switch = Switch(active=preferences_store.session_management_enabled, size_hint_x=0.4)
        self.session_switch.bind(active=lambda inst, val: preferences_store.set_preference('session_management_enabled', val))
        session_toggle_row.extend([session_toggle_label, self.session_switch])
        
        # Sessions list placeholder
        sessions_list = Label(
            text='Active Sessions:\n• Current session (Web)\n• Mobile app (iOS)',
            size_hint_y=None,
            height=dp(100),
            color=theme_manager.text_color,
            halign='left',
            valign='top'
        )
        sessions_list.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        session_layout.extend([session_toggle_row, sessions_list])
        session_card.add_widget(session_layout)
        self.add_widget(session_card)
        
        # Danger Zone
        danger_card = Card(title='Danger Zone', title_color=[1, 0.3, 0.3, 1])
        danger_layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(100))
        
        delete_btn = Button(
            text='Delete Account',
            background_color=[1, 0.2, 0.2, 1],
            on_release=lambda *_: self._delete_account()
        )
        
        danger_layout.add_widget(delete_btn)
        danger_card.add_widget(danger_layout)
        self.add_widget(danger_card)

    def _export_contacts(self):
        """Export contacts - placeholder implementation."""
        popup = Popup(
            title='Export Contacts',
            content=Label(text='Export functionality would be implemented here.\nThis would connect to ContactService backup.'),
            size_hint=(None, None),
            size=(dp(400), dp(200))
        )
        popup.open()

    def _import_contacts(self):
        """Import contacts - placeholder implementation."""
        popup = Popup(
            title='Import Contacts',
            content=Label(text='Import functionality would be implemented here.\nThis would connect to ContactService backup.'),
            size_hint=(None, None),
            size=(dp(400), dp(200))
        )
        popup.open()

    def _delete_account(self):
        """Delete account with multi-step confirmation."""
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(20))
        content.add_widget(Label(text='This action cannot be undone.\nAll your data will be permanently deleted.', 
                                color=[1, 0.3, 0.3, 1]))
        
        confirm_btn = Button(text='Yes, Delete Everything', background_color=[1, 0.2, 0.2, 1])
        cancel_btn = Button(text='Cancel')
        
        button_row = BoxLayout(spacing=dp(12))
        button_row.add_widget(cancel_btn)
        button_row.add_widget(confirm_btn)
        
        content.add_widget(button_row)
        
        popup = Popup(
            title='Delete Account Confirmation',
            content=content,
            size_hint=(None, None),
            size=(dp(400), dp(250))
        )
        
        def on_confirm(*args):
            # In a real implementation, this would call identity manager
            popup.dismiss()
            # Show final confirmation
            final_popup = Popup(
                title='Account Deleted',
                content=Label(text='Account has been permanently deleted.\nThank you for using our service.'),
                size_hint=(None, None),
                size=(dp(400), dp(150))
            )
            final_popup.open()
        
        confirm_btn.bind(on_release=on_confirm)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()


class SettingsScreen(Screen):
    """Main settings screen with tabbed interface for Privacy, Notifications, Appearance, and Account."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        
        root = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(64),
        )
        self.title = Label(
            text='Settings',
            font_size=theme_manager.typography.H4,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))
        
        header.add_widget(self.title)
        root.add_widget(header)
        
        # Tabbed Panel
        self.tab_panel = TabbedPanel(do_default_tab=False, tab_pos='top')
        
        # Privacy Tab
        privacy_tab = TabbedPanelItem(text='Privacy')
        privacy_content = ScrollView(do_scroll_x=False)
        privacy_scroll = PrivacySettingsTab()
        privacy_content.add_widget(privacy_scroll)
        privacy_tab.add_widget(privacy_content)
        
        # Notifications Tab
        notifications_tab = TabbedPanelItem(text='Notifications')
        notifications_content = ScrollView(do_scroll_x=False)
        notifications_scroll = NotificationsSettingsTab()
        notifications_content.add_widget(notifications_scroll)
        notifications_tab.add_widget(notifications_content)
        
        # Appearance Tab
        appearance_tab = TabbedPanelItem(text='Appearance')
        appearance_content = ScrollView(do_scroll_x=False)
        appearance_scroll = AppearanceSettingsTab()
        appearance_content.add_widget(appearance_scroll)
        appearance_tab.add_widget(appearance_content)
        
        # Account Tab
        account_tab = TabbedPanelItem(text='Account')
        account_content = ScrollView(do_scroll_x=False)
        account_scroll = AccountSettingsTab()
        account_content.add_widget(account_scroll)
        account_tab.add_widget(account_content)
        
        # Add tabs to panel
        self.tab_panel.add_widget(privacy_tab)
        self.tab_panel.add_widget(notifications_tab)
        self.tab_panel.add_widget(appearance_tab)
        self.tab_panel.add_widget(account_tab)
        
        # Make first tab active
        self.tab_panel.default_tab = privacy_tab
        
        root.add_widget(self.tab_panel)
        self.add_widget(root)
        
        # Bind to window resize for responsive design
        Window.bind(size=lambda *_: self._update_layout())
        self._update_layout()

    def _update_layout(self):
        """Update layout based on window size."""
        width, _ = Window.size
        if width < dp(900):
            self.tab_panel.tab_pos = 'top'
        else:
            self.tab_panel.tab_pos = 'left'