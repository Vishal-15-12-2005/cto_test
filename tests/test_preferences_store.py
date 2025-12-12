import unittest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from kivy.app import App

from src.services.preferences_store import preferences_store


class TestPreferencesStore(unittest.TestCase):
    """Test suite for PreferencesStore encryption, persistence, and event emissions."""

    def setUp(self):
        """Set up test environment."""
        # Mock App to provide user_data_dir
        self.mock_app = Mock()
        self.mock_app.user_data_dir = tempfile.mkdtemp()
        
        # Mock App.get_running_app
        self.app_patcher = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.app_patcher.start()
        
        # Mock EventBus
        self.event_bus_patcher = patch('src.services.preferences_store.event_bus')
        self.mock_event_bus = self.event_bus_patcher.start()
        
        # Store original values to restore later
        self.original_values = {}
        self._store_original_values()
        
        # Reset preferences store to clean state
        self._reset_store()

    def tearDown(self):
        """Clean up test environment."""
        self.app_patcher.stop()
        self.event_bus_patcher.stop()
        self._restore_original_values()

    def _store_original_values(self):
        """Store original values of preferences store."""
        self.original_values = {
            'data_retention_days': preferences_store.data_retention_days,
            'file_retention_days': preferences_store.file_retention_days,
            'enforce_max_security': preferences_store.enforce_max_security,
            'metadata_pruning': preferences_store.metadata_pruning,
            'auto_cleanup_enabled': preferences_store.auto_cleanup_enabled,
            'show_connection_status': preferences_store.show_connection_status,
            'encryption_level': preferences_store.encryption_level,
            'notifications_enabled': preferences_store.notifications_enabled,
            'sound_enabled': preferences_store.sound_enabled,
            'vibration_enabled': preferences_store.vibration_enabled,
            'quiet_hours_enabled': preferences_store.quiet_hours_enabled,
            'quiet_hours_start': preferences_store.quiet_hours_start,
            'quiet_hours_end': preferences_store.quiet_hours_end,
            'content_preview_enabled': preferences_store.content_preview_enabled,
            'theme_mode': preferences_store.theme_mode,
            'accent_color': preferences_store.accent_color,
            'font_size_scale': preferences_store.font_size_scale,
            'layout_density': preferences_store.layout_density,
            'username': preferences_store.username,
            'auto_backup_enabled': preferences_store.auto_backup_enabled,
            'session_management_enabled': preferences_store.session_management_enabled,
        }

    def _restore_original_values(self):
        """Restore original values."""
        for key, value in self.original_values.items():
            setattr(preferences_store, key, value)

    def _reset_store(self):
        """Reset store to default values."""
        preferences_store.reset_to_defaults()

    def test_store_initialization(self):
        """Test that store initializes with correct default values."""
        self.assertEqual(preferences_store.data_retention_days, 30)
        self.assertEqual(preferences_store.file_retention_days, 7)
        self.assertFalse(preferences_store.enforce_max_security)
        self.assertTrue(preferences_store.metadata_pruning)
        self.assertTrue(preferences_store.auto_cleanup_enabled)
        self.assertTrue(preferences_store.show_connection_status)
        self.assertEqual(preferences_store.encryption_level, 'standard')
        
        # Notification defaults
        self.assertTrue(preferences_store.notifications_enabled)
        self.assertTrue(preferences_store.sound_enabled)
        self.assertTrue(preferences_store.vibration_enabled)
        self.assertFalse(preferences_store.quiet_hours_enabled)
        self.assertEqual(preferences_store.quiet_hours_start, '22:00')
        self.assertEqual(preferences_store.quiet_hours_end, '08:00')
        self.assertTrue(preferences_store.content_preview_enabled)
        
        # Appearance defaults
        self.assertEqual(preferences_store.theme_mode, 'light')
        self.assertEqual(preferences_store.accent_color, '#4CAF50')
        self.assertEqual(preferences_store.font_size_scale, 1.0)
        self.assertEqual(preferences_store.layout_density, 'comfortable')
        
        # Account defaults
        self.assertEqual(preferences_store.username, '')
        self.assertTrue(preferences_store.auto_backup_enabled)
        self.assertTrue(preferences_store.session_management_enabled)

    def test_encryption_decryption_cycle(self):
        """Test that data can be encrypted and decrypted correctly."""
        test_data = {
            'data_retention_days': 45,
            'file_retention_days': 14,
            'notifications_enabled': False,
            'theme_mode': 'dark'
        }
        
        # Encrypt data
        encrypted = preferences_store._encrypt_data(test_data)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, '')
        
        # Decrypt data
        decrypted = preferences_store._decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)

    def test_empty_data_encryption(self):
        """Test encryption of empty data."""
        encrypted = preferences_store._encrypt_data({})
        self.assertEqual(encrypted, '')
        
        decrypted = preferences_store._decrypt_data(encrypted)
        self.assertEqual(decrypted, {})

    def test_invalid_encryption_handling(self):
        """Test handling of invalid encrypted data."""
        # Test with invalid base64
        result = preferences_store._decrypt_data('invalid_base64!')
        self.assertEqual(result, {})
        
        # Test with valid base64 but invalid encrypted data
        result = preferences_store._decrypt_data('Y2JhbmdlZHN0cmluZw==')  # "bangedstring" in base64
        self.assertEqual(result, {})

    def test_preferences_persistence(self):
        """Test that preferences are persisted to disk."""
        # Set some preferences
        preferences_store.data_retention_days = 60
        preferences_store.notifications_enabled = False
        preferences_store.theme_mode = 'dark'
        
        # Force save
        preferences_store._save_preferences()
        
        # Verify the file exists
        store_path = preferences_store._get_store_path()
        self.assertTrue(os.path.exists(store_path))
        
        # Test by reading the encrypted data and verifying it contains our values
        encrypted_data = preferences_store._store.get('preferences')['encrypted_data']
        decrypted_data = preferences_store._decrypt_data(encrypted_data)
        
        # Verify the persisted data
        self.assertEqual(decrypted_data['data_retention_days'], 60)
        self.assertFalse(decrypted_data['notifications_enabled'])
        self.assertEqual(decrypted_data['theme_mode'], 'dark')

    def test_set_get_preference(self):
        """Test setting and getting individual preferences."""
        # Test setting and getting
        preferences_store.set_preference('data_retention_days', 90)
        result = preferences_store.get_preference('data_retention_days')
        self.assertEqual(result, 90)
        
        # Test with invalid preference
        result = preferences_store.get_preference('nonexistent_preference', 'default')
        self.assertEqual(result, 'default')
        
        # Test setting invalid preference
        preferences_store.set_preference('nonexistent_preference', 'value')  # Should not crash
        result = preferences_store.get_preference('nonexistent_preference')  # Should return None
        self.assertIsNone(result)

    def test_bind_to_property(self):
        """Test property binding functionality."""
        callback_mock = Mock()
        
        # Bind to a property
        preferences_store.bind_to_property('data_retention_days', callback_mock)
        
        # Change the property
        preferences_store.data_retention_days = 45
        
        # Verify callback was called
        callback_mock.assert_called_once()

    def test_export_import_preferences(self):
        """Test exporting and importing encrypted preferences."""
        # Set some test data
        preferences_store.data_retention_days = 75
        preferences_store.notifications_enabled = False
        
        # Export preferences
        exported_data = preferences_store.export_preferences()
        self.assertIsInstance(exported_data, str)
        
        # Reset preferences
        preferences_store.reset_to_defaults()
        self.assertEqual(preferences_store.data_retention_days, 30)
        self.assertTrue(preferences_store.notifications_enabled)
        
        # Import preferences
        success = preferences_store.import_preferences(exported_data)
        self.assertTrue(success)
        
        # Verify imported data
        self.assertEqual(preferences_store.data_retention_days, 75)
        self.assertFalse(preferences_store.notifications_enabled)

    def test_export_invalid_data(self):
        """Test importing invalid data."""
        # Reset store first
        self._reset_store()
        
        # Test with various types of invalid data
        success1 = preferences_store.import_preferences('invalid_data')
        self.assertFalse(success1)
        
        success2 = preferences_store.import_preferences('')
        self.assertFalse(success2)
        
        success3 = preferences_store.import_preferences('not_base64!@#$%')
        self.assertFalse(success3)

    def test_reset_to_defaults(self):
        """Test resetting all preferences to defaults."""
        # Change some values
        preferences_store.data_retention_days = 999
        preferences_store.notifications_enabled = False
        preferences_store.theme_mode = 'dark'
        
        # Reset to defaults
        preferences_store.reset_to_defaults()
        
        # Verify all values are back to defaults
        self.assertEqual(preferences_store.data_retention_days, 30)
        self.assertEqual(preferences_store.file_retention_days, 7)
        self.assertFalse(preferences_store.enforce_max_security)
        self.assertTrue(preferences_store.metadata_pruning)
        self.assertTrue(preferences_store.auto_cleanup_enabled)
        self.assertTrue(preferences_store.show_connection_status)
        self.assertEqual(preferences_store.encryption_level, 'standard')
        
        self.assertTrue(preferences_store.notifications_enabled)
        self.assertTrue(preferences_store.sound_enabled)
        self.assertTrue(preferences_store.vibration_enabled)
        self.assertFalse(preferences_store.quiet_hours_enabled)
        self.assertEqual(preferences_store.quiet_hours_start, '22:00')
        self.assertEqual(preferences_store.quiet_hours_end, '08:00')
        self.assertTrue(preferences_store.content_preview_enabled)
        
        self.assertEqual(preferences_store.theme_mode, 'light')
        self.assertEqual(preferences_store.accent_color, '#4CAF50')
        self.assertEqual(preferences_store.font_size_scale, 1.0)
        self.assertEqual(preferences_store.layout_density, 'comfortable')
        
        self.assertEqual(preferences_store.username, '')
        self.assertTrue(preferences_store.auto_backup_enabled)
        self.assertTrue(preferences_store.session_management_enabled)

    def test_event_emission_on_save(self):
        """Test that events are emitted when preferences are saved."""
        # Clear previous calls
        self.mock_event_bus.reset_mock()
        
        # Set a preference
        preferences_store.set_preference('data_retention_days', 100)
        
        # Verify event was emitted
        self.mock_event_bus.emit_preferences_updated.assert_called_once()
        
        # Get the preferences that were emitted
        call_args = self.mock_event_bus.emit_preferences_updated.call_args
        emitted_preferences = call_args[0][0]  # First positional argument
        
        # Verify the changed preference is in the emitted data
        self.assertEqual(emitted_preferences['data_retention_days'], 100)

    def test_get_all_preferences(self):
        """Test getting all preferences as a dictionary."""
        all_prefs = preferences_store._get_all_preferences()
        
        # Verify it contains all expected keys
        expected_keys = [
            'data_retention_days', 'file_retention_days', 'enforce_max_security',
            'metadata_pruning', 'auto_cleanup_enabled', 'show_connection_status',
            'encryption_level', 'notifications_enabled', 'sound_enabled',
            'vibration_enabled', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'content_preview_enabled', 'theme_mode',
            'accent_color', 'font_size_scale', 'layout_density', 'username',
            'auto_backup_enabled', 'session_management_enabled'
        ]
        
        for key in expected_keys:
            self.assertIn(key, all_prefs)

    def test_apply_preferences(self):
        """Test applying preferences from a dictionary."""
        test_prefs = {
            'data_retention_days': 120,
            'notifications_enabled': False,
            'theme_mode': 'dark'
        }
        
        # Apply preferences
        preferences_store._apply_preferences(test_prefs)
        
        # Verify preferences were applied
        self.assertEqual(preferences_store.data_retention_days, 120)
        self.assertFalse(preferences_store.notifications_enabled)
        self.assertEqual(preferences_store.theme_mode, 'dark')

    def test_store_path_creation(self):
        """Test that store creates directory path correctly."""
        store_path = preferences_store._get_store_path()
        
        # Verify path is within the app's user data directory
        self.assertTrue(store_path.startswith(self.mock_app.user_data_dir))
        
        # Verify file has expected name
        self.assertTrue(store_path.endswith('preferences.enc'))

    def test_singleton_pattern(self):
        """Test that PreferencesStore follows singleton pattern."""
        # Get another reference to the same store
        from src.services.preferences_store import PreferencesStore
        store2 = PreferencesStore()
        
        # Both should be the same instance
        self.assertIs(preferences_store, store2)


if __name__ == '__main__':
    unittest.main()