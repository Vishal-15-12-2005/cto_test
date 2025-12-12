#!/usr/bin/env python
"""Lightweight tests for the encrypted app state store.

This validates persistence of onboarding flags and identity metadata, and ensures
private key material is not stored in plaintext.
"""

import base64
import json
import os
import tempfile

from src.services.app_state_store import AppStateStore


def test_onboarding_flags_persist():
    with tempfile.TemporaryDirectory() as tmp:
        store = AppStateStore(base_dir=tmp)
        assert store.is_onboarding_complete() is False

        store.update_onboarding(current_step='identity', step_index=2, step_count=7)
        store.update_onboarding(keys_backed_up=True)
        store.mark_onboarding_complete(skipped=False)

        store2 = AppStateStore(base_dir=tmp)
        ob = store2.get_onboarding()
        assert ob['complete'] is True
        assert ob['skipped'] is False
        assert ob['keys_backed_up'] is True
        assert ob['current_step'] == 'identity'


def test_identity_encryption_and_unlock():
    with tempfile.TemporaryDirectory() as tmp:
        store = AppStateStore(base_dir=tmp)

        username = 'alice'
        passphrase = 'correct horse battery staple'
        private_key = b'\x01' * 32
        public_key = b'\x02' * 32

        md = store.set_identity(
            username=username,
            passphrase=passphrase,
            private_key_bytes=private_key,
            public_key_bytes=public_key,
            keys_backed_up=False,
        )

        assert md.username == username
        assert store.has_identity() is True

        # Ensure the persisted JSON doesn't contain obvious plaintext secrets
        path = os.path.join(tmp, 'app_state.json')
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()

        assert 'private_key_b64' not in raw
        assert passphrase not in raw

        # The identity metadata should be persisted in plaintext
        data = json.loads(raw)
        assert data['identity']['username'] == username
        assert data['identity']['public_key_b64'] == base64.urlsafe_b64encode(public_key).decode('ascii')

        # Unlocking requires the passphrase
        store2 = AppStateStore(base_dir=tmp)
        try:
            store2.unlock('wrong passphrase')
            assert False, 'unlock should fail with wrong passphrase'
        except ValueError:
            pass

        unlocked = store2.unlock(passphrase)
        assert unlocked['private_key_b64'] == base64.urlsafe_b64encode(private_key).decode('ascii')
        assert unlocked['public_key_b64'] == base64.urlsafe_b64encode(public_key).decode('ascii')


if __name__ == '__main__':
    test_onboarding_flags_persist()
    test_identity_encryption_and_unlock()
    print('✅ AppStateStore tests passed!')
