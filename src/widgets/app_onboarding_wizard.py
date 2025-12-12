import base64
from typing import Any, Dict, List, Tuple

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from src.services.app_state_store import app_state_store
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.tor_onboarding_wizard import TorOnboardingWizard

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
except Exception:
    Ed25519PrivateKey = None
    Encoding = None
    PrivateFormat = None
    PublicFormat = None
    NoEncryption = None


def _wrap_label(label: Label) -> None:
    label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))


def _themed_label(text: str, *, font_size: float, bold: bool = False) -> Label:
    lbl = Label(
        text=text,
        font_size=font_size,
        bold=bold,
        halign='left',
        valign='top',
        color=theme_manager.text_color,
        size_hint_y=None,
    )
    _wrap_label(lbl)
    theme_manager.bind(text_color=lbl.setter('color'))
    lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(8)))
    return lbl


class WizardStep(Screen):
    step_id: str = ''
    title: str = ''

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        return True, ''

    def on_step_enter(self, wizard: 'AppOnboardingWizard') -> None:
        pass


class WelcomeStep(WizardStep):
    step_id = 'welcome'
    title = 'Welcome'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id

        body = BoxLayout(orientation='vertical', spacing=dp(12), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Welcome to the secure setup wizard.",
            font_size=theme_manager.typography.H5,
            bold=True,
        ))

        body.add_widget(_themed_label(
            "This app is designed for privacy-first operation. The wizard will help you:"
            "\n• bootstrap Tor"
            "\n• create a local identity (username + encrypted keys)"
            "\n• confirm you backed up your recovery material"
            "\n• add your first contact"
            "\n\nYou can skip onboarding, but some features will remain unavailable until an identity exists.",
            font_size=theme_manager.typography.BODY1,
        ))

        row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.ack = Switch(active=False)
        ack_lbl = Label(
            text='I understand and want to continue',
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
        )
        _wrap_label(ack_lbl)
        theme_manager.bind(text_color=ack_lbl.setter('color'))

        row.add_widget(ack_lbl)
        row.add_widget(BoxLayout())
        row.add_widget(self.ack)

        body.add_widget(row)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        if not self.ack.active:
            return False, 'Please acknowledge the privacy mission to continue.'
        return True, ''


class TorBootstrapStep(WizardStep):
    step_id = 'tor'
    title = 'Tor Bootstrap'

    def __init__(self, tor_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id
        self.tor_manager = tor_manager
        self._tor_state: Dict[str, Any] = {}

        body = BoxLayout(orientation='vertical', spacing=dp(12), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Tor provides network-level privacy. We'll wait until Tor finishes bootstrapping.",
            font_size=theme_manager.typography.BODY1,
        ))

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(16))
        self.status = _themed_label('—', font_size=theme_manager.typography.BODY2)

        btn_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(44))
        self.start_btn = Button(text='Start Tor', on_release=lambda *_: self.tor_manager.start_tor())
        self.advanced_btn = Button(text='Advanced Tor Setup', on_release=lambda *_: TorOnboardingWizard(self.tor_manager).open())
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.advanced_btn)

        body.add_widget(self.progress)
        body.add_widget(self.status)
        body.add_widget(btn_row)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

    def on_step_enter(self, wizard: 'AppOnboardingWizard') -> None:
        self._apply_state(self.tor_manager.get_state())

    def _apply_state(self, state: Dict[str, Any]) -> None:
        self._tor_state = dict(state or {})
        self.progress.value = int(self._tor_state.get('bootstrap_progress', 0) or 0)
        self.status.text = self._tor_state.get('bootstrap_status', '—')
        self.start_btn.disabled = self._tor_state.get('daemon_status') in {'starting', 'running', 'restarting'}

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        if (self._tor_state.get('connection_state') or '').lower() != 'connected':
            return False, 'Tor must be connected before continuing. If you are blocked, use Skip (with warnings).'
        return True, ''


class IdentityStep(WizardStep):
    step_id = 'identity'
    title = 'Create Username & Passphrase'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id

        body = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Choose a local username and a passphrase. Your keys will be encrypted with this passphrase.",
            font_size=theme_manager.typography.BODY1,
        ))

        self.username = TextInput(hint_text='Username', multiline=False, size_hint_y=None, height=dp(44))
        self.passphrase = TextInput(hint_text='Passphrase', multiline=False, password=True, size_hint_y=None, height=dp(44))
        self.passphrase_confirm = TextInput(hint_text='Confirm passphrase', multiline=False, password=True, size_hint_y=None, height=dp(44))

        body.add_widget(self.username)
        body.add_widget(self.passphrase)
        body.add_widget(self.passphrase_confirm)

        hint = _themed_label(
            "Tip: use a long passphrase you can remember. Minimum 8 characters is required.",
            font_size=theme_manager.typography.CAPTION,
        )
        body.add_widget(hint)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        username = self.username.text.strip()
        if not username:
            return False, 'Please enter a username.'

        p1 = self.passphrase.text
        p2 = self.passphrase_confirm.text
        if len(p1) < 8:
            return False, 'Passphrase must be at least 8 characters.'
        if p1 != p2:
            return False, 'Passphrases do not match.'

        wizard._draft_identity = {
            'username': username,
            'passphrase': p1,
        }
        return True, ''


class KeypairStep(WizardStep):
    step_id = 'keys'
    title = 'Generate & Back Up Keys'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id

        self._generated = False

        body = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Generate an identity keypair. Your private key never touches disk unencrypted.",
            font_size=theme_manager.typography.BODY1,
        ))

        self.generate_btn = Button(text='Generate Keypair', size_hint_y=None, height=dp(44))
        body.add_widget(self.generate_btn)

        pub_lbl = _themed_label('Public key', font_size=theme_manager.typography.BODY2)
        body.add_widget(pub_lbl)
        self.public_key = TextInput(text='', readonly=True, multiline=True, size_hint_y=None, height=dp(110))
        body.add_widget(self.public_key)

        rec_lbl = _themed_label('Recovery key (backup this)', font_size=theme_manager.typography.BODY2)
        body.add_widget(rec_lbl)
        self.recovery_key = TextInput(text='', readonly=True, multiline=True, size_hint_y=None, height=dp(110))
        body.add_widget(self.recovery_key)

        copy_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(44))
        self.copy_pub = Button(text='Copy Public Key', on_release=lambda *_: self._copy(self.public_key.text.strip()))
        self.copy_rec = Button(text='Copy Recovery Key', on_release=lambda *_: self._copy(self.recovery_key.text.strip()))
        copy_row.add_widget(self.copy_pub)
        copy_row.add_widget(self.copy_rec)
        body.add_widget(copy_row)

        backup_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.backup_ack = Switch(active=False)
        ack_lbl = Label(
            text='I have backed up my recovery key',
            halign='left',
            valign='middle',
            color=theme_manager.text_color,
        )
        _wrap_label(ack_lbl)
        theme_manager.bind(text_color=ack_lbl.setter('color'))

        backup_row.add_widget(ack_lbl)
        backup_row.add_widget(BoxLayout())
        backup_row.add_widget(self.backup_ack)
        body.add_widget(backup_row)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

        self.generate_btn.bind(on_release=lambda *_: self._generate())
        self.backup_ack.bind(active=lambda inst, val: app_state_store.update_onboarding(keys_backed_up=bool(val)))

    def _copy(self, text: str) -> None:
        if not text:
            return
        try:
            Clipboard.copy(text)
        except Exception:
            return

    def _generate(self) -> None:
        if self._generated:
            return

        if Ed25519PrivateKey is None:
            self.recovery_key.text = 'Key generation unavailable: missing cryptography Ed25519 support.'
            return

        wizard = getattr(self, 'wizard', None)
        draft = getattr(wizard, '_draft_identity', None) or {}
        username = draft.get('username')
        passphrase = draft.get('passphrase')
        if not username or not passphrase:
            self.recovery_key.text = 'Return to the previous step to set a username and passphrase.'
            return

        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        public_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

        self.public_key.text = base64.urlsafe_b64encode(public_bytes).decode('ascii')
        self.recovery_key.text = base64.urlsafe_b64encode(private_bytes).decode('ascii')

        app_state_store.set_identity(
            username=username,
            passphrase=passphrase,
            private_key_bytes=private_bytes,
            public_key_bytes=public_bytes,
            keys_backed_up=bool(self.backup_ack.active),
        )

        self._generated = True
        self.generate_btn.disabled = True

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        if not self._generated:
            return False, 'Please generate your keypair.'
        if not self.backup_ack.active:
            return False, 'You must confirm you backed up your recovery key to continue.'
        return True, ''


class SecurityChecklistStep(WizardStep):
    step_id = 'checklist'
    title = 'Security Checklist'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id
        self.items: List[Switch] = []

        body = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Quick checklist to keep your identity safe:",
            font_size=theme_manager.typography.BODY1,
        ))

        for text in [
            'My passphrase is unique and strong',
            'I will keep my recovery key offline',
            'I understand Tor may take time to bootstrap on some networks',
        ]:
            row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
            sw = Switch(active=False)
            lbl = Label(text=text, halign='left', valign='middle', color=theme_manager.text_color)
            _wrap_label(lbl)
            theme_manager.bind(text_color=lbl.setter('color'))
            row.add_widget(lbl)
            row.add_widget(BoxLayout())
            row.add_widget(sw)
            body.add_widget(row)
            self.items.append(sw)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        if not all(sw.active for sw in self.items):
            return False, 'Please acknowledge each checklist item.'
        return True, ''


class FirstContactStep(WizardStep):
    step_id = 'first_contact'
    title = 'Add Your First Contact'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id

        body = BoxLayout(orientation='vertical', spacing=dp(10), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "Add a first contact now (optional). You can enter their public key manually or scan a QR code.",
            font_size=theme_manager.typography.BODY1,
        ))

        self.method = Spinner(text='manual', values=['manual', 'qr_scan'], size_hint_y=None, height=dp(44))
        body.add_widget(self.method)

        self.name_input = TextInput(hint_text='Contact name (optional)', multiline=False, size_hint_y=None, height=dp(44))
        self.key_input = TextInput(hint_text='Contact public key / fingerprint', multiline=True, size_hint_y=None, height=dp(90))

        body.add_widget(self.name_input)
        body.add_widget(self.key_input)

        self.qr_payload = TextInput(hint_text='QR payload (paste here to simulate scanning)', multiline=True, size_hint_y=None, height=dp(90))
        self.qr_parse_btn = Button(text='Parse QR Payload', size_hint_y=None, height=dp(44), on_release=lambda *_: self._parse_qr())
        body.add_widget(self.qr_payload)
        body.add_widget(self.qr_parse_btn)

        self.qr_hint = _themed_label(
            "Tip: QR payload can be JSON like {\"name\": \"Bob\", \"public_key\": \"...\"}.",
            font_size=theme_manager.typography.CAPTION,
        )
        body.add_widget(self.qr_hint)

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)

        self.method.bind(text=lambda *_: self._sync_visibility())
        self._sync_visibility()

    def _sync_visibility(self) -> None:
        qr = self.method.text == 'qr_scan'

        self.qr_payload.disabled = not qr
        self.qr_parse_btn.disabled = not qr
        self.qr_payload.opacity = 1 if qr else 0
        self.qr_parse_btn.opacity = 1 if qr else 0

        self.qr_hint.opacity = 1 if qr else 0
        self.qr_hint.height = self.qr_hint.texture_size[1] + dp(8) if qr else 0

        if not qr:
            self.qr_payload.height = 0
            self.qr_parse_btn.height = 0
        else:
            self.qr_payload.height = dp(90)
            self.qr_parse_btn.height = dp(44)

    def _parse_qr(self) -> None:
        raw = (self.qr_payload.text or '').strip()
        if not raw:
            return

        name = ''
        key = ''

        try:
            import json

            payload = json.loads(raw)
            if isinstance(payload, dict):
                name = str(payload.get('name') or payload.get('username') or '').strip()
                key = str(payload.get('public_key') or payload.get('key') or payload.get('fingerprint') or '').strip()
        except Exception:
            pass

        if not key:
            parts = [p.strip() for p in raw.replace(';', '\n').splitlines() if p.strip()]
            if len(parts) == 1 and ':' in parts[0]:
                k, v = parts[0].split(':', 1)
                if k.lower().strip() in {'key', 'public_key', 'fingerprint'}:
                    key = v.strip()
            elif len(parts) >= 2:
                name = name or parts[0]
                key = key or parts[1]

        if name:
            self.name_input.text = name
        if key:
            self.key_input.text = key

    def validate(self, wizard: 'AppOnboardingWizard') -> Tuple[bool, str]:
        if self.method.text == 'qr_scan' and self.qr_payload.text.strip() and not self.key_input.text.strip():
            self._parse_qr()

        name = self.name_input.text.strip()
        key = self.key_input.text.strip()
        if key and len(key) < 10:
            return False, 'Contact key looks too short.'

        if self.method.text == 'qr_scan' and not key and self.qr_payload.text.strip():
            return False, 'Unable to parse QR payload. Paste JSON or switch to manual.'

        if key:
            app_state_store.set_first_contact(name, key)
        return True, ''


class FeatureTourStep(WizardStep):
    step_id = 'tour'
    title = 'Quick Tour'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.step_id

        body = BoxLayout(orientation='vertical', spacing=dp(12), padding=(0, dp(8)))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(_themed_label(
            "You're ready.",
            font_size=theme_manager.typography.H5,
            bold=True,
        ))

        body.add_widget(_themed_label(
            "Next steps inside the app:\n"
            "• Dashboard: see Tor status and system health\n"
            "• Traffic: monitor obfuscation metrics\n"
            "• Obfuscation: tune settings and view live monitoring\n\n"
            "You can revisit Tor configuration from the dashboard at any time.",
            font_size=theme_manager.typography.BODY1,
        ))

        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(body)
        self.add_widget(sv)


class AppOnboardingWizard(ModalView):
    def __init__(self, tor_manager, **kwargs):
        super().__init__(**kwargs)
        self.tor_manager = tor_manager

        self.size_hint = (0.95, 0.95)
        self.auto_dismiss = False

        self._draft_identity: Dict[str, Any] = {}

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        header = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        header.bind(minimum_height=header.setter('height'))

        title_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.title_label = Label(
            text='Secure Setup',
            font_size=theme_manager.typography.H5,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        _wrap_label(self.title_label)
        theme_manager.bind(text_color=self.title_label.setter('color'))

        self.step_label = Label(
            text='Step',
            font_size=theme_manager.typography.BODY2,
            color=theme_manager.text_color,
            halign='right',
            valign='middle',
            size_hint_x=None,
            width=dp(120),
        )
        _wrap_label(self.step_label)
        theme_manager.bind(text_color=self.step_label.setter('color'))

        title_row.add_widget(self.title_label)
        title_row.add_widget(BoxLayout())
        title_row.add_widget(self.step_label)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))

        header.add_widget(title_row)
        header.add_widget(self.progress)

        root.add_widget(header)

        self.error_label = Label(
            text='',
            font_size=theme_manager.typography.CAPTION,
            halign='left',
            valign='top',
            color=[0.9, 0.25, 0.25, 1],
            size_hint_y=None,
        )
        _wrap_label(self.error_label)
        self.error_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(8)))
        self.error_label.opacity = 0
        root.add_widget(self.error_label)

        self.sm = ScreenManager()
        self.steps: List[WizardStep] = [
            WelcomeStep(),
            TorBootstrapStep(tor_manager),
            IdentityStep(),
            KeypairStep(),
            SecurityChecklistStep(),
            FirstContactStep(),
            FeatureTourStep(),
        ]

        for s in self.steps:
            s.wizard = self
            self.sm.add_widget(s)

        root.add_widget(self.sm)
        root.add_widget(self._build_footer())
        self.add_widget(root)

        self._step_index = 0
        self._set_initial_step_from_store()
        self._sync_ui()

    def open(self, *largs):
        event_bus.bind(on_tor_state_update=self._on_tor_state_update)
        Clock.schedule_once(lambda dt: self._emit_progress(), 0)
        return super().open(*largs)

    def dismiss(self, *largs, **kwargs):
        event_bus.unbind(on_tor_state_update=self._on_tor_state_update)
        return super().dismiss(*largs, **kwargs)

    def _set_initial_step_from_store(self) -> None:
        ob = app_state_store.get_onboarding()
        step_id = (ob.get('current_step') or 'welcome').strip()
        for idx, step in enumerate(self.steps):
            if step.step_id == step_id:
                self._step_index = idx
                self.sm.current = step.step_id
                return

    def _build_footer(self) -> BoxLayout:
        footer = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(46))

        self.skip_btn = Button(text='Skip', on_release=lambda *_: self._confirm_skip())
        self.back_btn = Button(text='Back', on_release=lambda *_: self._go(-1))
        self.next_btn = Button(text='Next', on_release=lambda *_: self._next())

        footer.add_widget(self.skip_btn)
        footer.add_widget(BoxLayout())
        footer.add_widget(self.back_btn)
        footer.add_widget(self.next_btn)
        return footer

    def _confirm_skip(self) -> None:
        confirm = ModalView(size_hint=(0.9, 0.4), auto_dismiss=False)
        layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        layout.add_widget(_themed_label(
            "Skip secure setup?", font_size=theme_manager.typography.H6, bold=True
        ))
        layout.add_widget(_themed_label(
            "Skipping means you may not have an identity configured and secure messaging features may be disabled."
            " You can rerun onboarding later by deleting app_state.json.",
            font_size=theme_manager.typography.BODY2,
        ))

        btns = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(44))
        cancel = Button(text='Go Back', on_release=lambda *_: confirm.dismiss())
        skip = Button(text='Skip Anyway', on_release=lambda *_: self._skip_anyway(confirm))
        btns.add_widget(cancel)
        btns.add_widget(skip)
        layout.add_widget(btns)

        confirm.add_widget(layout)
        confirm.open()

    def _skip_anyway(self, modal: ModalView) -> None:
        modal.dismiss()
        app_state_store.mark_onboarding_complete(skipped=True)
        self.dismiss()

    def _show_error(self, message: str) -> None:
        self.error_label.text = message
        self.error_label.opacity = 1 if message else 0

    def _emit_progress(self) -> None:
        step = self.steps[self._step_index]
        app_state_store.update_onboarding(
            current_step=step.step_id,
            step_index=self._step_index,
            step_count=len(self.steps),
        )

    def _sync_ui(self) -> None:
        step = self.steps[self._step_index]
        self.title_label.text = f"Secure Setup • {step.title}"
        self.step_label.text = f"{self._step_index + 1}/{len(self.steps)}"
        self.progress.value = int(((self._step_index + 1) / len(self.steps)) * 100)

        self.back_btn.disabled = self._step_index == 0

        if self._step_index == len(self.steps) - 1:
            self.next_btn.text = 'Finish'
        else:
            self.next_btn.text = 'Next'

        self._show_error('')
        step.on_step_enter(self)

    def _go(self, delta: int) -> None:
        new_idx = max(0, min(len(self.steps) - 1, self._step_index + delta))
        if new_idx == self._step_index:
            return

        self._step_index = new_idx
        self.sm.current = self.steps[self._step_index].step_id
        self._emit_progress()
        self._sync_ui()

    def _next(self) -> None:
        step = self.steps[self._step_index]
        ok, msg = step.validate(self)
        if not ok:
            self._show_error(msg)
            return

        if self._step_index == len(self.steps) - 1:
            if app_state_store.has_identity() and not app_state_store.get_onboarding().get('keys_backed_up'):
                self._show_error('You must confirm your key backup before finishing.')
                return

            app_state_store.mark_onboarding_complete(skipped=False)
            self.dismiss()
            return

        self._go(1)

    def _on_tor_state_update(self, instance, state):
        step = self.steps[self._step_index]
        if isinstance(step, TorBootstrapStep):
            step._apply_state(state)
