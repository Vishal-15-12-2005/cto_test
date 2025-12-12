from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from src.services.tor_settings_store import tor_settings_store
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus


class TorOnboardingWizard(ModalView):
    def __init__(self, tor_manager, **kwargs):
        super().__init__(**kwargs)
        self.tor_manager = tor_manager

        self.size_hint = (0.95, 0.95)
        self.auto_dismiss = False

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44))
        self.title = Label(text='Tor Setup & Onboarding', font_size=theme_manager.typography.H5, color=theme_manager.text_color, halign='left', valign='middle')
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))

        header.add_widget(self.title)
        header.add_widget(BoxLayout())
        root.add_widget(header)

        self.sm = ScreenManager()
        self.config_screen = self._build_config_screen()
        self.bootstrap_screen = self._build_bootstrap_screen()
        self.sm.add_widget(self.config_screen)
        self.sm.add_widget(self.bootstrap_screen)
        root.add_widget(self.sm)

        root.add_widget(self._build_footer())
        self.add_widget(root)

        self._apply_settings_to_form(tor_settings_store.get_settings())
        self._state = {}

    def open(self, *largs):
        event_bus.bind(on_tor_state_update=self._on_tor_state_update)
        event_bus.bind(on_tor_settings_update=self._on_tor_settings_update)
        return super().open(*largs)

    def dismiss(self, *largs, **kwargs):
        event_bus.unbind(on_tor_state_update=self._on_tor_state_update)
        event_bus.unbind(on_tor_settings_update=self._on_tor_settings_update)
        return super().dismiss(*largs, **kwargs)

    def _build_config_screen(self):
        s = Screen(name='config')
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(6)))

        self.binary_mode = Spinner(text='bundled', values=['bundled', 'system', 'custom'], size_hint_y=None, height=dp(44))
        self.binary_path = TextInput(text='', hint_text='Custom tor binary path', multiline=False, size_hint_y=None, height=dp(44))

        self.bridge_mode = Spinner(text='none', values=['none', 'obfs4', 'meek-azure', 'custom'], size_hint_y=None, height=dp(44))
        self.bridge_lines = TextInput(text='', hint_text='Bridge lines (one per line)', multiline=True)

        self.auto_reconnect = Switch(active=True)
        ar_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36))
        self.ar_label = Label(text='Enable auto-reconnect', halign='left', valign='middle', color=theme_manager.text_color)
        self.ar_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.ar_label.setter('color'))
        ar_row.add_widget(self.ar_label)
        ar_row.add_widget(BoxLayout())
        ar_row.add_widget(self.auto_reconnect)

        self.config_hint = Label(
            text='Choose how Tor should start and (optionally) configure bridges.',
            halign='left',
            valign='top',
            color=theme_manager.text_color,
            font_size=theme_manager.typography.BODY2,
        )
        self.config_hint.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.config_hint.setter('color'))

        layout.add_widget(self.config_hint)

        binary_label = Label(text='Tor binary', size_hint_y=None, height=dp(20), color=theme_manager.text_color, halign='left', valign='middle')
        binary_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=binary_label.setter('color'))
        layout.add_widget(binary_label)

        layout.add_widget(self.binary_mode)
        layout.add_widget(self.binary_path)

        bridges_label = Label(text='Bridges', size_hint_y=None, height=dp(20), color=theme_manager.text_color, halign='left', valign='middle')
        bridges_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=bridges_label.setter('color'))
        layout.add_widget(bridges_label)

        layout.add_widget(self.bridge_mode)
        layout.add_widget(self.bridge_lines)
        layout.add_widget(ar_row)

        s.add_widget(layout)

        self.binary_mode.bind(text=lambda *_: self._update_form_visibility())
        self.bridge_mode.bind(text=lambda *_: self._update_form_visibility())

        self._update_form_visibility()
        return s

    def _build_bootstrap_screen(self):
        s = Screen(name='bootstrap')
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(6)))

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(16))
        self.status = Label(text='—', halign='left', valign='top', color=theme_manager.text_color)
        self.status.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.status.setter('color'))

        self.start_btn = Button(text='Start Tor', size_hint_y=None, height=dp(44), on_release=lambda *_: self._start_tor())

        bootstrap_label = Label(text='Bootstrap', size_hint_y=None, height=dp(22), color=theme_manager.text_color, halign='left', valign='middle')
        bootstrap_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=bootstrap_label.setter('color'))
        layout.add_widget(bootstrap_label)

        layout.add_widget(self.progress)
        layout.add_widget(self.status)
        layout.add_widget(self.start_btn)

        s.add_widget(layout)
        return s

    def _build_footer(self):
        footer = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(46))

        self.cancel_btn = Button(text='Cancel', on_release=lambda *_: self.dismiss())
        self.back_btn = Button(text='Back', on_release=lambda *_: self._go_back())
        self.next_btn = Button(text='Next', on_release=lambda *_: self._go_next())
        self.finish_btn = Button(text='Finish', on_release=lambda *_: self._finish())

        footer.add_widget(self.cancel_btn)
        footer.add_widget(BoxLayout())
        footer.add_widget(self.back_btn)
        footer.add_widget(self.next_btn)
        footer.add_widget(self.finish_btn)

        self._sync_footer()
        return footer

    def _sync_footer(self):
        cur = self.sm.current
        self.back_btn.disabled = cur == 'config'
        self.next_btn.disabled = cur != 'config'

        connected = self._state.get('connection_state') == 'connected'
        self.finish_btn.disabled = cur != 'bootstrap' or not connected

    def _go_back(self):
        self.sm.current = 'config'
        self._sync_footer()

    def _go_next(self):
        self._save_settings()
        self.sm.current = 'bootstrap'
        self._sync_footer()
        self._start_tor()

    def _finish(self):
        self._save_settings(has_onboarded=True)
        self.dismiss()

    def _save_settings(self, **extra):
        patch = {
            'tor_binary_mode': self.binary_mode.text,
            'tor_binary_path': self.binary_path.text.strip(),
            'bridge_mode': self.bridge_mode.text,
            'bridge_lines': self.bridge_lines.text.strip(),
            'auto_reconnect': bool(self.auto_reconnect.active),
        }
        patch.update(extra)
        tor_settings_store.update_settings(**patch)

    def _apply_settings_to_form(self, settings):
        self.binary_mode.text = settings.get('tor_binary_mode', 'bundled')
        self.binary_path.text = settings.get('tor_binary_path', '')
        self.bridge_mode.text = settings.get('bridge_mode', 'none')
        self.bridge_lines.text = settings.get('bridge_lines', '')
        self.auto_reconnect.active = bool(settings.get('auto_reconnect', True))
        self._update_form_visibility()

    def _update_form_visibility(self):
        self.binary_path.disabled = self.binary_mode.text != 'custom'
        self.binary_path.opacity = 1 if self.binary_mode.text == 'custom' else 0

        custom_bridges = self.bridge_mode.text == 'custom'
        self.bridge_lines.disabled = not custom_bridges
        self.bridge_lines.opacity = 1 if custom_bridges else 0

    def _start_tor(self):
        self._save_settings()
        self.tor_manager.apply_settings(**tor_settings_store.get_settings())
        self.tor_manager.start_tor()

    def _on_tor_settings_update(self, instance, settings):
        if self.sm.current == 'config':
            self._apply_settings_to_form(settings)

    def _on_tor_state_update(self, instance, state):
        self._state = state
        self.progress.value = int(state.get('bootstrap_progress', 0) or 0)
        self.status.text = state.get('bootstrap_status', '—')
        self.start_btn.disabled = state.get('daemon_status') in {'starting', 'running', 'restarting'}
        self._sync_footer()
