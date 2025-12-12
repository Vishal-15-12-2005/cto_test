import os
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from src.utils.event_bus import event_bus


class ObfuscationConfigService:
    def __init__(self):
        self._store = JsonStore(self._get_store_path())

        if not self._store.exists('settings'):
            self._store.put(
                'settings',
                standard_mode_enabled=False,
                maximum_mode_enabled=False,
                auto_switch_enabled=False,
                auto_switch_threshold=80,
                schedule_mode='24/7',
                schedule_start_hour=9,
                schedule_start_minute=0,
                schedule_end_hour=17,
                schedule_end_minute=0,
                battery_saver_enabled=True,
                battery_saver_threshold=20,
                network_quality_awareness=True,
                data_cap_enabled=False,
                data_cap_mb=1000,
                data_cap_warning_percent=80,
            )

        if not self._store.exists('history'):
            self._store.put(
                'history',
                session_packets=0,
                session_data_mb=0.0,
                session_start_time=0,
                today_packets=0,
                today_data_mb=0.0,
                week_packets=0,
                week_data_mb=0.0,
                error_count=0,
            )

    def _get_store_path(self):
        app = App.get_running_app()
        if app is not None and getattr(app, 'user_data_dir', None):
            base_dir = app.user_data_dir
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.tor_dashboard')

        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'obfuscation_config.json')

    def get_settings(self):
        return dict(self._store.get('settings'))

    def update_settings(self, **patch):
        settings = self.get_settings()
        settings.update(patch)
        self._store.put('settings', **settings)
        event_bus.emit_obfuscation_settings(settings)
        return settings

    def get_history(self):
        return dict(self._store.get('history'))

    def update_history(self, **patch):
        history = self.get_history()
        history.update(patch)
        self._store.put('history', **history)
        return history

    def reset_session_history(self):
        import time
        return self.update_history(
            session_packets=0,
            session_data_mb=0.0,
            session_start_time=time.time()
        )


obfuscation_config_service = ObfuscationConfigService()
