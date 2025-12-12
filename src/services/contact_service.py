import os
import json
import qrcode
from io import BytesIO
from datetime import datetime
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from cryptography.fernet import Fernet
from src.utils.event_bus import event_bus


class ContactService:
    def __init__(self):
        self._store_path = self._get_store_path()
        self._encryption_key = self._get_or_create_key()
        self._cipher = Fernet(self._encryption_key)
        self._contacts = {}
        self._pending_requests = {}
        self._fingerprints = {}
        self._favorites = set()
        self._groups = {}
        self._muted = set()
        self._blocked = set()
        self._archived = set()
        self._backup_metadata = {}
        self._load_contacts()

    def _get_store_path(self):
        app = App.get_running_app()
        if app is not None and getattr(app, 'user_data_dir', None):
            base_dir = app.user_data_dir
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.contact_manager')

        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'contacts.enc')

    def _get_key_path(self):
        return os.path.join(os.path.dirname(self._store_path), 'contacts.key')

    def _get_or_create_key(self):
        key_path = self._get_key_path()
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            return key

    def _encrypt_data(self, data: dict) -> str:
        json_str = json.dumps(data)
        encrypted = self._cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def _decrypt_data(self, encrypted_str: str) -> dict:
        try:
            decrypted = self._cipher.decrypt(encrypted_str.encode())
            return json.loads(decrypted.decode())
        except Exception:
            return {}

    def _load_contacts(self):
        if os.path.exists(self._store_path):
            try:
                with open(self._store_path, 'r') as f:
                    encrypted_str = f.read()
                    data = self._decrypt_data(encrypted_str)
                    self._contacts = data.get('contacts', {})
                    self._pending_requests = data.get('pending_requests', {})
                    self._fingerprints = data.get('fingerprints', {})
                    self._favorites = set(data.get('favorites', []))
                    self._groups = data.get('groups', {})
                    self._muted = set(data.get('muted', []))
                    self._blocked = set(data.get('blocked', []))
                    self._archived = set(data.get('archived', []))
                    self._backup_metadata = data.get('backup_metadata', {})
            except Exception:
                pass

    def _save_contacts(self):
        data = {
            'contacts': self._contacts,
            'pending_requests': self._pending_requests,
            'fingerprints': self._fingerprints,
            'favorites': list(self._favorites),
            'groups': self._groups,
            'muted': list(self._muted),
            'blocked': list(self._blocked),
            'archived': list(self._archived),
            'backup_metadata': self._backup_metadata,
        }
        encrypted_str = self._encrypt_data(data)
        with open(self._store_path, 'w') as f:
            f.write(encrypted_str)
        event_bus.emit_contacts_updated()

    def add_contact(self, contact_id: str, name: str, onion_address: str, **kwargs):
        """Add a new contact or update existing."""
        contact = {
            'id': contact_id,
            'name': name,
            'onion_address': onion_address,
            'nickname': kwargs.get('nickname', ''),
            'groups': kwargs.get('groups', []),
            'created_at': kwargs.get('created_at', datetime.now().isoformat()),
            'last_message_preview': kwargs.get('last_message_preview', ''),
            'last_message_time': kwargs.get('last_message_time', None),
            'presence_status': kwargs.get('presence_status', 'offline'),
            'verified': kwargs.get('verified', False),
            'custom_fields': kwargs.get('custom_fields', {}),
        }
        self._contacts[contact_id] = contact
        self._save_contacts()
        event_bus.emit_contact_added(contact_id, contact)
        return contact

    def get_contact(self, contact_id: str):
        """Get a contact by ID."""
        return self._contacts.get(contact_id)

    def get_all_contacts(self):
        """Get all contacts."""
        return dict(self._contacts)

    def search_contacts(self, query: str):
        """Search contacts by name, nickname, or onion address."""
        query = query.lower()
        results = {}
        for contact_id, contact in self._contacts.items():
            if contact_id in self._archived:
                continue
            name = contact.get('name', '').lower()
            nickname = contact.get('nickname', '').lower()
            onion = contact.get('onion_address', '').lower()
            if query in name or query in nickname or query in onion:
                results[contact_id] = contact
        return results

    def delete_contact(self, contact_id: str):
        """Delete a contact."""
        if contact_id in self._contacts:
            del self._contacts[contact_id]
            self._favorites.discard(contact_id)
            self._blocked.discard(contact_id)
            self._muted.discard(contact_id)
            self._archived.discard(contact_id)
            if contact_id in self._fingerprints:
                del self._fingerprints[contact_id]
            if contact_id in self._pending_requests:
                del self._pending_requests[contact_id]
            self._save_contacts()
            event_bus.emit_contact_deleted(contact_id)
            return True
        return False

    def update_contact(self, contact_id: str, **kwargs):
        """Update contact fields."""
        if contact_id not in self._contacts:
            return None
        self._contacts[contact_id].update(kwargs)
        self._save_contacts()
        event_bus.emit_contact_updated(contact_id, self._contacts[contact_id])
        return self._contacts[contact_id]

    def set_nickname(self, contact_id: str, nickname: str):
        """Set or update contact nickname."""
        return self.update_contact(contact_id, nickname=nickname)

    def add_to_favorite(self, contact_id: str):
        """Add contact to favorites."""
        if contact_id in self._contacts:
            self._favorites.add(contact_id)
            self._save_contacts()
            event_bus.emit_contact_favorited(contact_id, True)
            return True
        return False

    def remove_from_favorite(self, contact_id: str):
        """Remove contact from favorites."""
        if contact_id in self._contacts:
            self._favorites.discard(contact_id)
            self._save_contacts()
            event_bus.emit_contact_favorited(contact_id, False)
            return True
        return False

    def is_favorite(self, contact_id: str):
        """Check if contact is in favorites."""
        return contact_id in self._favorites

    def get_favorites(self):
        """Get all favorite contacts."""
        return {cid: self._contacts[cid] for cid in self._favorites if cid in self._contacts}

    def block_contact(self, contact_id: str):
        """Block a contact."""
        if contact_id in self._contacts:
            self._blocked.add(contact_id)
            self._save_contacts()
            event_bus.emit_contact_blocked(contact_id, True)
            return True
        return False

    def unblock_contact(self, contact_id: str):
        """Unblock a contact."""
        if contact_id in self._contacts:
            self._blocked.discard(contact_id)
            self._save_contacts()
            event_bus.emit_contact_blocked(contact_id, False)
            return True
        return False

    def is_blocked(self, contact_id: str):
        """Check if contact is blocked."""
        return contact_id in self._blocked

    def get_blocked_contacts(self):
        """Get all blocked contacts."""
        return {cid: self._contacts[cid] for cid in self._blocked if cid in self._contacts}

    def mute_contact(self, contact_id: str):
        """Mute a contact."""
        if contact_id in self._contacts:
            self._muted.add(contact_id)
            self._save_contacts()
            event_bus.emit_contact_muted(contact_id, True)
            return True
        return False

    def unmute_contact(self, contact_id: str):
        """Unmute a contact."""
        if contact_id in self._contacts:
            self._muted.discard(contact_id)
            self._save_contacts()
            event_bus.emit_contact_muted(contact_id, False)
            return True
        return False

    def is_muted(self, contact_id: str):
        """Check if contact is muted."""
        return contact_id in self._muted

    def archive_contact(self, contact_id: str):
        """Archive a contact."""
        if contact_id in self._contacts:
            self._archived.add(contact_id)
            self._save_contacts()
            event_bus.emit_contact_archived(contact_id, True)
            return True
        return False

    def unarchive_contact(self, contact_id: str):
        """Unarchive a contact."""
        if contact_id in self._contacts:
            self._archived.discard(contact_id)
            self._save_contacts()
            event_bus.emit_contact_archived(contact_id, False)
            return True
        return False

    def is_archived(self, contact_id: str):
        """Check if contact is archived."""
        return contact_id in self._archived

    def add_to_group(self, contact_id: str, group_name: str):
        """Add contact to a group."""
        if contact_id not in self._contacts:
            return False
        if group_name not in self._groups:
            self._groups[group_name] = []
        if contact_id not in self._groups[group_name]:
            self._groups[group_name].append(contact_id)
            self._contacts[contact_id].setdefault('groups', []).append(group_name)
        self._save_contacts()
        return True

    def remove_from_group(self, contact_id: str, group_name: str):
        """Remove contact from a group."""
        if contact_id not in self._contacts:
            return False
        if group_name in self._groups:
            self._groups[group_name] = [c for c in self._groups[group_name] if c != contact_id]
        if group_name in self._contacts[contact_id].get('groups', []):
            self._contacts[contact_id]['groups'].remove(group_name)
        self._save_contacts()
        return True

    def get_group_contacts(self, group_name: str):
        """Get all contacts in a group."""
        contact_ids = self._groups.get(group_name, [])
        return {cid: self._contacts[cid] for cid in contact_ids if cid in self._contacts}

    def get_all_groups(self):
        """Get all group names."""
        return list(self._groups.keys())

    def set_verification_fingerprint(self, contact_id: str, fingerprint: str, verified: bool = False):
        """Set verification fingerprint for a contact."""
        if contact_id not in self._contacts:
            return False
        self._fingerprints[contact_id] = {
            'fingerprint': fingerprint,
            'verified': verified,
            'verified_at': datetime.now().isoformat() if verified else None,
        }
        self._contacts[contact_id]['verified'] = verified
        self._save_contacts()
        event_bus.emit_contact_verified(contact_id, verified)
        return True

    def get_verification_fingerprint(self, contact_id: str):
        """Get verification fingerprint for a contact."""
        return self._fingerprints.get(contact_id, {})

    def create_contact_request(self, from_id: str, to_id: str, memo: str = ''):
        """Create a contact request."""
        request_id = f"{from_id}_{to_id}_{datetime.now().timestamp()}"
        self._pending_requests[request_id] = {
            'id': request_id,
            'from_id': from_id,
            'to_id': to_id,
            'memo': memo,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
        }
        self._save_contacts()
        event_bus.emit_contact_request_created(request_id)
        return request_id

    def accept_contact_request(self, request_id: str):
        """Accept a contact request."""
        if request_id not in self._pending_requests:
            return False
        request = self._pending_requests[request_id]
        request['status'] = 'accepted'
        request['accepted_at'] = datetime.now().isoformat()
        self._save_contacts()
        event_bus.emit_contact_request_accepted(request_id)
        return True

    def decline_contact_request(self, request_id: str):
        """Decline a contact request."""
        if request_id not in self._pending_requests:
            return False
        request = self._pending_requests[request_id]
        request['status'] = 'declined'
        request['declined_at'] = datetime.now().isoformat()
        self._save_contacts()
        event_bus.emit_contact_request_declined(request_id)
        return True

    def get_pending_requests(self):
        """Get all pending requests."""
        return {rid: req for rid, req in self._pending_requests.items() if req.get('status') == 'pending'}

    def generate_qr_code(self, onion_address: str, contact_name: str = '') -> BytesIO:
        """Generate a QR code for an onion address."""
        qr_data = {
            'type': 'contact',
            'onion_address': onion_address,
            'name': contact_name,
            'timestamp': datetime.now().isoformat(),
        }
        qr_json = json.dumps(qr_data)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_json)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return img_io

    def decode_qr_payload(self, qr_data: str) -> dict:
        """Decode a QR code payload."""
        try:
            return json.loads(qr_data)
        except Exception:
            return {}

    def import_contact_from_qr(self, qr_payload: dict) -> str:
        """Import a contact from a QR payload."""
        onion_address = qr_payload.get('onion_address', '')
        name = qr_payload.get('name', 'Unknown')
        
        if not onion_address:
            return None
        
        contact_id = onion_address.replace('.onion', '')
        contact = self.add_contact(contact_id, name, onion_address)
        event_bus.emit_contact_imported(contact_id)
        return contact_id

    def export_backup(self) -> str:
        """Export encrypted backup."""
        data = {
            'contacts': self._contacts,
            'pending_requests': self._pending_requests,
            'fingerprints': self._fingerprints,
            'favorites': list(self._favorites),
            'groups': self._groups,
            'muted': list(self._muted),
            'blocked': list(self._blocked),
            'archived': list(self._archived),
            'backup_metadata': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
            },
        }
        return self._encrypt_data(data)

    def import_backup(self, encrypted_backup: str) -> bool:
        """Import encrypted backup."""
        try:
            data = self._decrypt_data(encrypted_backup)
            self._contacts = data.get('contacts', {})
            self._pending_requests = data.get('pending_requests', {})
            self._fingerprints = data.get('fingerprints', {})
            self._favorites = set(data.get('favorites', []))
            self._groups = data.get('groups', {})
            self._muted = set(data.get('muted', []))
            self._blocked = set(data.get('blocked', []))
            self._archived = set(data.get('archived', []))
            self._backup_metadata = data.get('backup_metadata', {})
            self._save_contacts()
            event_bus.emit_backup_imported()
            return True
        except Exception:
            return False

    def set_last_message_preview(self, contact_id: str, preview: str, timestamp: str = None):
        """Set last message preview for a contact."""
        if contact_id not in self._contacts:
            return False
        self._contacts[contact_id]['last_message_preview'] = preview
        self._contacts[contact_id]['last_message_time'] = timestamp or datetime.now().isoformat()
        self._save_contacts()
        return True

    def set_presence_status(self, contact_id: str, status: str):
        """Set presence status for a contact (online/offline/connecting)."""
        if contact_id not in self._contacts:
            return False
        self._contacts[contact_id]['presence_status'] = status
        self._save_contacts()
        event_bus.emit_contact_presence_updated(contact_id, status)
        return True

    def get_sorted_contacts(self, sort_by: str = 'alphabetical'):
        """Get contacts sorted by specified criteria."""
        contacts = {cid: c for cid, c in self._contacts.items() if cid not in self._archived}
        
        if sort_by == 'alphabetical':
            return dict(sorted(contacts.items(), key=lambda x: x[1].get('name', '').lower()))
        elif sort_by == 'recent':
            return dict(sorted(
                contacts.items(),
                key=lambda x: x[1].get('last_message_time', '0'),
                reverse=True
            ))
        elif sort_by == 'favorites':
            favorites = {cid: c for cid, c in contacts.items() if cid in self._favorites}
            others = {cid: c for cid, c in contacts.items() if cid not in self._favorites}
            result = dict(sorted(favorites.items(), key=lambda x: x[1].get('name', '').lower()))
            result.update(dict(sorted(others.items(), key=lambda x: x[1].get('name', '').lower())))
            return result
        
        return contacts


contact_service = ContactService()
