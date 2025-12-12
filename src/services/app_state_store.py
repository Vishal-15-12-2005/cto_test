import base64
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from kivy.app import App

from src.utils.event_bus import event_bus

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except Exception as exc:  # pragma: no cover
    AESGCM = None
    PBKDF2HMAC = None
    hashes = None
    _CRYPTO_IMPORT_ERROR = exc


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode('ascii')


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode('ascii'))


@dataclass(frozen=True)
class IdentityMetadata:
    username: str
    key_type: str
    public_key_b64: str
    fingerprint: str
    created_at: float


class AppStateStore:
    def __init__(self, base_dir: Optional[str] = None, filename: str = 'app_state.json'):
        self._base_dir = base_dir
        self._filename = filename
        self._path = None
        self._state = self._default_state()
        self._unlocked_identity: Optional[Dict[str, Any]] = None

        self._load()

    def _default_state(self) -> Dict[str, Any]:
        return {
            'version': 1,
            'onboarding': {
                'complete': False,
                'skipped': False,
                'current_step': 'welcome',
                'step_index': 0,
                'step_count': 7,
                'keys_backed_up': False,
                'completed_at': None,
            },
            'identity': None,
            'secrets': None,
            'contacts': {
                'first_contact': None,
            },
        }

    def _resolve_base_dir(self) -> str:
        if self._base_dir:
            base_dir = self._base_dir
        else:
            app = App.get_running_app()
            if app is not None and getattr(app, 'user_data_dir', None):
                base_dir = app.user_data_dir
            else:
                base_dir = os.path.join(os.path.expanduser('~'), '.tor_dashboard')

        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    def _resolve_path(self) -> str:
        if self._path is None:
            self._path = os.path.join(self._resolve_base_dir(), self._filename)
        return self._path

    def _load(self) -> None:
        path = self._resolve_path()
        if not os.path.exists(path):
            self._persist()
            return

        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        if not isinstance(loaded, dict):
            self._state = self._default_state()
            self._persist()
            return

        self._state = self._default_state()
        self._deep_update(self._state, loaded)

    def _deep_update(self, dst: Dict[str, Any], src: Dict[str, Any]) -> None:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                self._deep_update(dst[k], v)
            else:
                dst[k] = v

    def _persist(self) -> None:
        path = self._resolve_path()
        tmp = f"{path}.tmp"

        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self._state, f, indent=2, sort_keys=True)

        os.replace(tmp, path)

        try:
            os.chmod(path, 0o600)
        except Exception:
            pass

    def get_onboarding(self) -> Dict[str, Any]:
        return dict(self._state.get('onboarding') or {})

    def is_onboarding_complete(self) -> bool:
        return bool((self._state.get('onboarding') or {}).get('complete'))

    def identity_metadata(self) -> Optional[IdentityMetadata]:
        ident = self._state.get('identity')
        if not isinstance(ident, dict):
            return None
        try:
            return IdentityMetadata(
                username=ident['username'],
                key_type=ident['key_type'],
                public_key_b64=ident['public_key_b64'],
                fingerprint=ident['fingerprint'],
                created_at=float(ident['created_at']),
            )
        except Exception:
            return None

    def update_onboarding(self, **patch: Any) -> Dict[str, Any]:
        ob = dict(self._state.get('onboarding') or {})
        ob.update(patch)
        self._state['onboarding'] = ob
        self._persist()

        payload = dict(ob)
        payload['identity_exists'] = self._state.get('identity') is not None
        event_bus.emit_app_onboarding_progress(payload)
        return payload

    def mark_onboarding_complete(self, skipped: bool = False) -> Dict[str, Any]:
        patch = {
            'complete': True,
            'skipped': bool(skipped),
            'completed_at': time.time(),
        }
        ob = self.update_onboarding(**patch)
        event_bus.emit_app_onboarding_complete(
            {
                'onboarding': dict(ob),
                'identity': self._state.get('identity'),
            }
        )
        return ob

    def set_first_contact(self, name: str, public_key: str) -> None:
        self._state.setdefault('contacts', {})
        self._state['contacts']['first_contact'] = {
            'name': (name or '').strip(),
            'public_key': (public_key or '').strip(),
            'added_at': time.time(),
        }
        self._persist()

    def has_identity(self) -> bool:
        return self._state.get('identity') is not None and self._state.get('secrets') is not None

    def _require_crypto(self) -> None:
        if AESGCM is None or PBKDF2HMAC is None or hashes is None:  # pragma: no cover
            raise RuntimeError(f"cryptography is required for encrypted state store: {_CRYPTO_IMPORT_ERROR}")

    def _derive_key(self, passphrase: str, salt: bytes, iterations: int) -> bytes:
        self._require_crypto()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=int(iterations),
        )
        return kdf.derive(passphrase.encode('utf-8'))

    def _encrypt(self, key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
        self._require_crypto()
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce, ct

    def _decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        self._require_crypto()
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def set_identity(
        self,
        *,
        username: str,
        passphrase: str,
        private_key_bytes: bytes,
        public_key_bytes: bytes,
        key_type: str = 'ed25519',
        keys_backed_up: bool = False,
    ) -> IdentityMetadata:
        username = (username or '').strip()
        if not username:
            raise ValueError('username is required')
        if not passphrase:
            raise ValueError('passphrase is required')

        self._require_crypto()

        created_at = time.time()
        fingerprint = self._fingerprint(public_key_bytes)

        kdf_salt = secrets.token_bytes(16)
        verifier_salt = secrets.token_bytes(16)
        iterations = 200_000

        key = self._derive_key(passphrase, kdf_salt, iterations)

        secrets_payload = {
            'key_type': key_type,
            'private_key_b64': _b64e(private_key_bytes),
            'public_key_b64': _b64e(public_key_bytes),
            'created_at': created_at,
        }
        plaintext = json.dumps(secrets_payload, sort_keys=True).encode('utf-8')
        nonce, ciphertext = self._encrypt(key, plaintext)

        verifier = self._derive_key(passphrase, verifier_salt, iterations)

        self._state['identity'] = {
            'username': username,
            'key_type': key_type,
            'public_key_b64': _b64e(public_key_bytes),
            'fingerprint': fingerprint,
            'created_at': created_at,
        }
        self._state['secrets'] = {
            'kdf': {
                'algo': 'pbkdf2-sha256',
                'iterations': iterations,
                'salt_b64': _b64e(kdf_salt),
            },
            'verifier': {
                'algo': 'pbkdf2-sha256',
                'iterations': iterations,
                'salt_b64': _b64e(verifier_salt),
                'check_b64': _b64e(verifier),
            },
            'ciphertext': {
                'nonce_b64': _b64e(nonce),
                'data_b64': _b64e(ciphertext),
            },
        }

        self.update_onboarding(keys_backed_up=bool(keys_backed_up))
        self._persist()

        md = self.identity_metadata()
        if md is None:
            raise RuntimeError('failed to persist identity metadata')

        self.unlock(passphrase)
        return md

    def unlock(self, passphrase: str) -> Dict[str, Any]:
        if not self.has_identity():
            raise RuntimeError('no identity to unlock')
        if not passphrase:
            raise ValueError('passphrase is required')

        secrets_block = self._state.get('secrets') or {}
        verifier = (secrets_block.get('verifier') or {})
        kdf = (secrets_block.get('kdf') or {})
        ciphertext = (secrets_block.get('ciphertext') or {})

        iterations = int(verifier.get('iterations') or kdf.get('iterations') or 200_000)

        verifier_salt = _b64d(verifier['salt_b64'])
        expected = _b64d(verifier['check_b64'])
        actual = self._derive_key(passphrase, verifier_salt, iterations)
        if not secrets.compare_digest(expected, actual):
            raise ValueError('invalid passphrase')

        enc_salt = _b64d(kdf['salt_b64'])
        key = self._derive_key(passphrase, enc_salt, iterations)
        nonce = _b64d(ciphertext['nonce_b64'])
        data = _b64d(ciphertext['data_b64'])

        plaintext = self._decrypt(key, nonce, data)
        payload = json.loads(plaintext.decode('utf-8'))

        self._unlocked_identity = payload

        event_bus.emit_identity_ready(
            {
                'identity': self._state.get('identity'),
            }
        )
        return dict(payload)

    def get_unlocked_identity(self) -> Optional[Dict[str, Any]]:
        return dict(self._unlocked_identity) if self._unlocked_identity else None

    def lock(self) -> None:
        self._unlocked_identity = None

    def _fingerprint(self, public_key_bytes: bytes) -> str:
        import hashlib

        return hashlib.sha256(public_key_bytes).hexdigest()


app_state_store = AppStateStore()
