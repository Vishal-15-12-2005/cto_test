from kivy.event import EventDispatcher


class EventBus(EventDispatcher):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self, **kwargs):
        if hasattr(self, '_initialized'):
            return
        super().__init__(**kwargs)

        self.register_event_type('on_tor_status_update')
        self.register_event_type('on_tor_state_update')
        self.register_event_type('on_tor_settings_update')
        self.register_event_type('on_traffic_status_update')
        self.register_event_type('on_traffic_obfuscation_update')
        self.register_event_type('on_sensitive_comms_update')
        self.register_event_type('on_max_ai_state_update')
        self.register_event_type('on_theme_changed')
        self.register_event_type('on_obfuscation_settings_update')
        self.register_event_type('on_obfuscation_monitor_update')
        self.register_event_type('on_obfuscation_warning')

        self.register_event_type('on_app_onboarding_progress')
        self.register_event_type('on_app_onboarding_complete')
        self.register_event_type('on_identity_ready')

        self._initialized = True

    def on_tor_status_update(self, status):
        pass

    def on_tor_state_update(self, state):
        pass

    def on_tor_settings_update(self, settings):
        pass

    def on_traffic_status_update(self, status):
        pass

    def on_traffic_obfuscation_update(self, state):
        pass

    def on_sensitive_comms_update(self, active: bool, reason: str = ''):
        pass

    def on_max_ai_state_update(self, state):
        pass

    def on_theme_changed(self, theme_name):
        pass

    def on_obfuscation_settings_update(self, settings):
        pass

    def on_obfuscation_monitor_update(self, state):
        pass

    def on_obfuscation_warning(self, warning_type, message):
        pass

    def on_app_onboarding_progress(self, state):
        pass

    def on_app_onboarding_complete(self, payload):
        pass

    def on_identity_ready(self, payload):
        pass

    def emit_tor_status(self, status):
        self.dispatch('on_tor_status_update', status)

    def emit_tor_state(self, state):
        self.dispatch('on_tor_state_update', state)

    def emit_tor_settings(self, settings):
        self.dispatch('on_tor_settings_update', settings)

    def emit_traffic_status(self, status):
        self.dispatch('on_traffic_status_update', status)

    def emit_traffic_obfuscation_update(self, state):
        self.dispatch('on_traffic_obfuscation_update', state)

    def emit_sensitive_comms(self, active: bool, reason: str = ''):
        self.dispatch('on_sensitive_comms_update', bool(active), reason)

    def emit_max_ai_state(self, state):
        self.dispatch('on_max_ai_state_update', state)

    def emit_theme_changed(self, theme_name):
        self.dispatch('on_theme_changed', theme_name)

    def emit_obfuscation_settings(self, settings):
        self.dispatch('on_obfuscation_settings_update', settings)

    def emit_obfuscation_monitor(self, state):
        self.dispatch('on_obfuscation_monitor_update', state)

    def emit_obfuscation_warning(self, warning_type, message):
        self.dispatch('on_obfuscation_warning', warning_type, message)

    def emit_app_onboarding_progress(self, state):
        self.dispatch('on_app_onboarding_progress', state)

    def emit_app_onboarding_complete(self, payload):
        self.dispatch('on_app_onboarding_complete', payload)

    def emit_identity_ready(self, payload):
        self.dispatch('on_identity_ready', payload)


event_bus = EventBus()
