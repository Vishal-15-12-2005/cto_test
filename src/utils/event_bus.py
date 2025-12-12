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
        self.register_event_type('on_contacts_updated')
        self.register_event_type('on_contact_added')
        self.register_event_type('on_contact_deleted')
        self.register_event_type('on_contact_updated')
        self.register_event_type('on_contact_favorited')
        self.register_event_type('on_contact_blocked')
        self.register_event_type('on_contact_muted')
        self.register_event_type('on_contact_archived')
        self.register_event_type('on_contact_verified')
        self.register_event_type('on_contact_presence_updated')
        self.register_event_type('on_contact_request_created')
        self.register_event_type('on_contact_request_accepted')
        self.register_event_type('on_contact_request_declined')
        self.register_event_type('on_contact_imported')
        self.register_event_type('on_backup_imported')
        self.register_event_type('on_message_received')
        self.register_event_type('on_typing_indicator')
        self.register_event_type('on_read_receipt')
        self.register_event_type('on_message_reacted')
        self.register_event_type('on_message_pinned')
        self.register_event_type('on_search_results')

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

    def on_contacts_updated(self):
        pass

    def on_contact_added(self, contact_id, contact):
        pass

    def on_contact_deleted(self, contact_id):
        pass

    def on_contact_updated(self, contact_id, contact):
        pass

    def on_contact_favorited(self, contact_id, is_favorite):
        pass

    def on_contact_blocked(self, contact_id, is_blocked):
        pass

    def on_contact_muted(self, contact_id, is_muted):
        pass

    def on_contact_archived(self, contact_id, is_archived):
        pass

    def on_contact_verified(self, contact_id, is_verified):
        pass

    def on_contact_presence_updated(self, contact_id, status):
        pass

    def on_contact_request_created(self, request_id):
        pass

    def on_contact_request_accepted(self, request_id):
        pass

    def on_contact_request_declined(self, request_id):
        pass

    def on_contact_imported(self, contact_id):
        pass

    def on_backup_imported(self):
    def on_message_received(self, message):
        pass

    def on_typing_indicator(self, data):
        pass

    def on_read_receipt(self, data):
        pass

    def on_message_reacted(self, data):
        pass

    def on_message_pinned(self, data):
        pass

    def on_search_results(self, results):
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

    def emit_contacts_updated(self):
        self.dispatch('on_contacts_updated')

    def emit_contact_added(self, contact_id, contact):
        self.dispatch('on_contact_added', contact_id, contact)

    def emit_contact_deleted(self, contact_id):
        self.dispatch('on_contact_deleted', contact_id)

    def emit_contact_updated(self, contact_id, contact):
        self.dispatch('on_contact_updated', contact_id, contact)

    def emit_contact_favorited(self, contact_id, is_favorite):
        self.dispatch('on_contact_favorited', contact_id, is_favorite)

    def emit_contact_blocked(self, contact_id, is_blocked):
        self.dispatch('on_contact_blocked', contact_id, is_blocked)

    def emit_contact_muted(self, contact_id, is_muted):
        self.dispatch('on_contact_muted', contact_id, is_muted)

    def emit_contact_archived(self, contact_id, is_archived):
        self.dispatch('on_contact_archived', contact_id, is_archived)

    def emit_contact_verified(self, contact_id, is_verified):
        self.dispatch('on_contact_verified', contact_id, is_verified)

    def emit_contact_presence_updated(self, contact_id, status):
        self.dispatch('on_contact_presence_updated', contact_id, status)

    def emit_contact_request_created(self, request_id):
        self.dispatch('on_contact_request_created', request_id)

    def emit_contact_request_accepted(self, request_id):
        self.dispatch('on_contact_request_accepted', request_id)

    def emit_contact_request_declined(self, request_id):
        self.dispatch('on_contact_request_declined', request_id)

    def emit_contact_imported(self, contact_id):
        self.dispatch('on_contact_imported', contact_id)

    def emit_backup_imported(self):
        self.dispatch('on_backup_imported')


event_bus = EventBus()
