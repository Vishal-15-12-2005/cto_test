import os
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from src.utils.event_bus import event_bus


class TorSettingsStore:
    def __init__(self):
        self._store = JsonStore(self._get_store_path())

        if not self._store.exists('settings'):
            self._store.put(
                'settings',
                has_onboarded=False,
                tor_binary_mode='bundled',
                tor_binary_path='',
                bridge_mode='none',
                bridge_lines='',
                auto_reconnect=True,
            )

    def _get_store_path(self):
        app = App.get_running_app()
        if app is not None and getattr(app, 'user_data_dir', None):
            base_dir = app.user_data_dir
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.tor_dashboard')

        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'tor_settings.json')

    def get_settings(self):
        return dict(self._store.get('settings'))

    def update_settings(self, **patch):
        settings = self.get_settings()
        settings.update(patch)
        self._store.put('settings', **settings)
        event_bus.emit_tor_settings(settings)
        return settings


tor_settings_store = TorSettingsStore()
