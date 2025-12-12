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

        # Messaging
        self.register_event_type('on_conversation_updated')
        self.register_event_type('on_message_batch')
        self.register_event_type('on_message_deleted')
        self.register_event_type('on_typing_state')
        self.register_event_type('on_receipt_update')

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

    # Messaging events
    def on_conversation_updated(self, conversation_id, conversation):
        pass

    def on_message_batch(self, conversation_id, messages):
        pass

    def on_message_deleted(self, conversation_id, message_id):
        pass

    def on_typing_state(self, conversation_id, peer_id, is_typing: bool):
        pass

    def on_receipt_update(self, conversation_id, message_id, status):
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

    # Messaging emit helpers
    def emit_conversation_updated(self, conversation_id, conversation):
        self.dispatch('on_conversation_updated', conversation_id, conversation)

    def emit_message_batch(self, conversation_id, messages):
        self.dispatch('on_message_batch', conversation_id, messages)

    def emit_message_deleted(self, conversation_id, message_id):
        self.dispatch('on_message_deleted', conversation_id, message_id)

    def emit_typing_state(self, conversation_id, peer_id, is_typing: bool):
        self.dispatch('on_typing_state', conversation_id, peer_id, bool(is_typing))

    def emit_receipt_update(self, conversation_id, message_id, status):
        self.dispatch('on_receipt_update', conversation_id, message_id, status)


event_bus = EventBus()
