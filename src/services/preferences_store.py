import os
import json
import base64
from typing import Any, Dict, Optional
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.event import EventDispatcher

from src.utils.event_bus import event_bus
from src.theming.theme_manager import theme_manager

# Optional cryptography import - fall back to unencrypted storage if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    # Fallback encryption using built-in base64 (less secure but functional)
    CRYPTO_AVAILABLE = False


class PreferencesStore(EventDispatcher):
    """
    Encrypted preferences store with reactive properties and event bus integration.
    Provides secure storage for user preferences across Privacy, Notifications, Appearance, and Account settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PreferencesStore, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self, **kwargs):
        if hasattr(self, '_initialized'):
            return
        super().__init__(**kwargs)
        
        self._store = JsonStore(self._get_store_path())
        self._encryption_key = None
        self._salt = b'preferences_store_salt_2024'  # In production, this should be more secure
        
        self._initialize_defaults()
        self._setup_encryption()
        self._load_preferences()
        
        # Register event types
        self.register_event_type('on_preferences_updated')
        self.register_event_type('on_preferences_changed')
        
        # Bind to theme changes
        self.bind(
            theme_mode=self._on_theme_mode_change,
            font_size_scale=self._on_font_scale_change,
            layout_density=self._on_layout_density_change,
            accent_color=self._on_accent_color_change
        )
        
        theme_manager.bind(theme_mode=self._on_theme_manager_change)
        
        self._initialized = True

    # Privacy Settings
    data_retention_days = NumericProperty(30)
    file_retention_days = NumericProperty(7)
    enforce_max_security = BooleanProperty(False)
    metadata_pruning = BooleanProperty(True)
    auto_cleanup_enabled = BooleanProperty(True)
    show_connection_status = BooleanProperty(True)
    encryption_level = StringProperty('standard')  # standard, maximum

    # Notification Settings  
    notifications_enabled = BooleanProperty(True)
    sound_enabled = BooleanProperty(True)
    vibration_enabled = BooleanProperty(True)
    quiet_hours_enabled = BooleanProperty(False)
    quiet_hours_start = StringProperty('22:00')
    quiet_hours_end = StringProperty('08:00')
    content_preview_enabled = BooleanProperty(True)

    # Appearance Settings
    theme_mode = StringProperty('light')  # light, dark, system
    accent_color = StringProperty('#4CAF50')
    font_size_scale = NumericProperty(1.0)
    layout_density = StringProperty('comfortable')  # compact, comfortable

    # Account Settings
    username = StringProperty('')
    auto_backup_enabled = BooleanProperty(True)
    session_management_enabled = BooleanProperty(True)

    def _initialize_defaults(self):
        """Set up default values for all preferences."""
        if not self._store.exists('preferences'):
            self._store.put('preferences', encrypted_data='')

    def _get_store_path(self) -> str:
        """Get the path to the preferences store file."""
        app = App.get_running_app()
        if app is not None and getattr(app, 'user_data_dir', None):
            base_dir = app.user_data_dir
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.tor_dashboard')

        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'preferences.enc')

    def _setup_encryption(self):
        """Set up encryption key for the preferences store."""
        if not CRYPTO_AVAILABLE:
            self._encryption_key = None
            return
            
        # In a real app, you'd derive this from a user passphrase
        # For now, we'll use a deterministic key based on the app directory
        app = App.get_running_app()
        if app is not None:
            base_dir = os.path.dirname(self._get_store_path())
            password = base_dir.encode()
        else:
            password = b'default_password'

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._encryption_key = Fernet(key)

    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt preferences data."""
        if not data:
            return ''
        
        json_data = json.dumps(data)
        
        if CRYPTO_AVAILABLE and self._encryption_key:
            encrypted_data = self._encryption_key.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        else:
            # Fallback to basic encoding (not secure but functional)
            return base64.b64encode(json_data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt preferences data."""
        if not encrypted_data:
            return {}
        
        try:
            if CRYPTO_AVAILABLE and self._encryption_key:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
                decrypted_bytes = self._encryption_key.decrypt(encrypted_bytes)
                return json.loads(decrypted_bytes.decode())
            else:
                # Fallback to basic decoding
                decoded_bytes = base64.b64decode(encrypted_data.encode())
                return json.loads(decoded_bytes.decode())
        except Exception:
            # If decryption fails, return defaults
            return {}

    def _load_preferences(self):
        """Load preferences from encrypted store."""
        if self._store.exists('preferences'):
            store_data = self._store.get('preferences')
            encrypted_data = store_data.get('encrypted_data', '')
            preferences = self._decrypt_data(encrypted_data)
            self._apply_preferences(preferences)

    def _save_preferences(self):
        """Save preferences to encrypted store."""
        preferences = self._get_all_preferences()
        encrypted_data = self._encrypt_data(preferences)
        self._store.put('preferences', encrypted_data=encrypted_data)
        
        # Emit event for other services
        event_bus.emit_preferences_updated(preferences)

    def _apply_preferences(self, preferences: Dict[str, Any]):
        """Apply loaded preferences to properties."""
        property_mapping = {
            'data_retention_days': 'data_retention_days',
            'file_retention_days': 'file_retention_days',
            'enforce_max_security': 'enforce_max_security',
            'metadata_pruning': 'metadata_pruning',
            'auto_cleanup_enabled': 'auto_cleanup_enabled',
            'show_connection_status': 'show_connection_status',
            'encryption_level': 'encryption_level',
            'notifications_enabled': 'notifications_enabled',
            'sound_enabled': 'sound_enabled',
            'vibration_enabled': 'vibration_enabled',
            'quiet_hours_enabled': 'quiet_hours_enabled',
            'quiet_hours_start': 'quiet_hours_start',
            'quiet_hours_end': 'quiet_hours_end',
            'content_preview_enabled': 'content_preview_enabled',
            'theme_mode': 'theme_mode',
            'accent_color': 'accent_color',
            'font_size_scale': 'font_size_scale',
            'layout_density': 'layout_density',
            'username': 'username',
            'auto_backup_enabled': 'auto_backup_enabled',
            'session_management_enabled': 'session_management_enabled',
        }

        for key, value in preferences.items():
            if key in property_mapping:
                prop_name = property_mapping[key]
                if hasattr(self, prop_name):
                    setattr(self, prop_name, value)

    def _get_all_preferences(self) -> Dict[str, Any]:
        """Get all current preferences as a dictionary."""
        return {
            'data_retention_days': self.data_retention_days,
            'file_retention_days': self.file_retention_days,
            'enforce_max_security': self.enforce_max_security,
            'metadata_pruning': self.metadata_pruning,
            'auto_cleanup_enabled': self.auto_cleanup_enabled,
            'show_connection_status': self.show_connection_status,
            'encryption_level': self.encryption_level,
            'notifications_enabled': self.notifications_enabled,
            'sound_enabled': self.sound_enabled,
            'vibration_enabled': self.vibration_enabled,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'content_preview_enabled': self.content_preview_enabled,
            'theme_mode': self.theme_mode,
            'accent_color': self.accent_color,
            'font_size_scale': self.font_size_scale,
            'layout_density': self.layout_density,
            'username': self.username,
            'auto_backup_enabled': self.auto_backup_enabled,
            'session_management_enabled': self.session_management_enabled,
        }

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a specific preference value."""
        prop_mapping = {
            'data_retention_days': 'data_retention_days',
            'file_retention_days': 'file_retention_days',
            'enforce_max_security': 'enforce_max_security',
            'metadata_pruning': 'metadata_pruning',
            'auto_cleanup_enabled': 'auto_cleanup_enabled',
            'show_connection_status': 'show_connection_status',
            'encryption_level': 'encryption_level',
            'notifications_enabled': 'notifications_enabled',
            'sound_enabled': 'sound_enabled',
            'vibration_enabled': 'vibration_enabled',
            'quiet_hours_enabled': 'quiet_hours_enabled',
            'quiet_hours_start': 'quiet_hours_start',
            'quiet_hours_end': 'quiet_hours_end',
            'content_preview_enabled': 'content_preview_enabled',
            'theme_mode': 'theme_mode',
            'accent_color': 'accent_color',
            'font_size_scale': 'font_size_scale',
            'layout_density': 'layout_density',
            'username': 'username',
            'auto_backup_enabled': 'auto_backup_enabled',
            'session_management_enabled': 'session_management_enabled',
        }

        if key in prop_mapping and hasattr(self, prop_mapping[key]):
            return getattr(self, prop_mapping[key])
        return default

    def set_preference(self, key: str, value: Any):
        """Set a specific preference value and persist it."""
        prop_mapping = {
            'data_retention_days': 'data_retention_days',
            'file_retention_days': 'file_retention_days',
            'enforce_max_security': 'enforce_max_security',
            'metadata_pruning': 'metadata_pruning',
            'auto_cleanup_enabled': 'auto_cleanup_enabled',
            'show_connection_status': 'show_connection_status',
            'encryption_level': 'encryption_level',
            'notifications_enabled': 'notifications_enabled',
            'sound_enabled': 'sound_enabled',
            'vibration_enabled': 'vibration_enabled',
            'quiet_hours_enabled': 'quiet_hours_enabled',
            'quiet_hours_start': 'quiet_hours_start',
            'quiet_hours_end': 'quiet_hours_end',
            'content_preview_enabled': 'content_preview_enabled',
            'theme_mode': 'theme_mode',
            'accent_color': 'accent_color',
            'font_size_scale': 'font_size_scale',
            'layout_density': 'layout_density',
            'username': 'username',
            'auto_backup_enabled': 'auto_backup_enabled',
            'session_management_enabled': 'session_management_enabled',
        }

        if key in prop_mapping and hasattr(self, prop_mapping[key]):
            setattr(self, prop_mapping[key], value)
            self._save_preferences()

    def bind_to_property(self, property_name: str, callback):
        """Bind a callback to a preference property changes."""
        if hasattr(self, property_name):
            self.bind(**{property_name: callback})

    def on_preferences_updated(self, preferences):
        """Default handler for preferences updated event."""
        pass

    def on_preferences_changed(self, *args):
        """Default handler for preferences changed event."""
        pass

    def export_preferences(self) -> str:
        """Export preferences as encrypted JSON string."""
        return self._encrypt_data(self._get_all_preferences())

    def import_preferences(self, encrypted_data: str) -> bool:
        """Import preferences from encrypted data."""
        try:
            preferences = self._decrypt_data(encrypted_data)
            if not preferences:  # Check if decryption actually worked
                return False
            self._apply_preferences(preferences)
            self._save_preferences()
            return True
        except Exception:
            return False

    def _on_theme_manager_change(self, instance, value):
        """Handle theme manager changes."""
        if value in ['light', 'dark']:
            self.theme_mode = value

    def _on_theme_mode_change(self, instance, value):
        """Handle theme mode preference changes."""
        if value in ['light', 'dark']:
            theme_manager.theme_mode = value

    def _on_font_scale_change(self, instance, value):
        """Handle font scale preference changes."""
        # This would be used to scale fonts across the app
        pass

    def _on_layout_density_change(self, instance, value):
        """Handle layout density preference changes."""
        # This would update spacing tokens and layout measurements
        if value == 'compact':
            # Update theme spacing tokens to be more compact
            pass
        else:
            # Use comfortable spacing
            pass

    def _on_accent_color_change(self, instance, value):
        """Handle accent color preference changes."""
        # This would update the primary color in theme manager
        pass

    def reset_to_defaults(self):
        """Reset all preferences to default values."""
        self.data_retention_days = 30
        self.file_retention_days = 7
        self.enforce_max_security = False
        self.metadata_pruning = True
        self.auto_cleanup_enabled = True
        self.show_connection_status = True
        self.encryption_level = 'standard'
        self.notifications_enabled = True
        self.sound_enabled = True
        self.vibration_enabled = True
        self.quiet_hours_enabled = False
        self.quiet_hours_start = '22:00'
        self.quiet_hours_end = '08:00'
        self.content_preview_enabled = True
        self.theme_mode = 'light'
        self.accent_color = '#4CAF50'
        self.font_size_scale = 1.0
        self.layout_density = 'comfortable'
        self.username = ''
        self.auto_backup_enabled = True
        self.session_management_enabled = True
        
        self._save_preferences()


# Global instance
preferences_store = PreferencesStore()