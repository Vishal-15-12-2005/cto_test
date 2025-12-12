# Contact Manager Implementation (Phase 2)

## Overview

The Contact Manager is a comprehensive contact management system for the Kivy-based application, providing secure, encrypted storage and management of contacts with support for presence indicators, verification, grouping, and backup/restore functionality.

## Architecture

### Services

#### ContactService (`src/services/contact_service.py`)

A singleton service providing encrypted contact management with the following features:

**Core Functionality:**
- **Contact Management**: Add, retrieve, update, delete, and search contacts
- **Encryption**: Fernet-based encryption for secure storage at rest
- **Sorting**: Alphabetical, recent (by message time), and favorites-first sorting
- **Search**: Search by name, nickname, or onion address

**State Management:**
- **Favorites**: Mark contacts as favorites
- **Blocking**: Block/unblock contacts
- **Muting**: Mute/unmute contacts for notifications
- **Archiving**: Archive/unarchive contacts
- **Groups**: Organize contacts into groups
- **Presence**: Track online/offline/connecting status
- **Verification**: Store and manage verification fingerprints
- **Contact Requests**: Create, accept, and decline contact requests

**Data Features:**
- **Last Message Preview**: Store preview text of last message
- **Custom Fields**: Extensible custom field support
- **Audit Trail**: Track creation times, verification timestamps
- **Backup/Restore**: Encrypted export and import functionality

### Screens

#### ContactsScreen (`src/screens/contacts_screen.py`)

Main contact management interface with:

**UI Components:**
- Search bar for finding contacts
- Tabbed interface with views:
  - **All**: All non-archived contacts
  - **Favorites**: Favorite contacts
  - **Recent**: Contacts sorted by last message
  - **Pending**: Incoming contact requests
  - **Blocked**: Blocked contacts
- Responsive contact list with inline indicators
- Add contact menu with multiple options

**Add Contact Options:**
1. **Add Manually**: Enter name and onion address directly
2. **Scan QR Code**: Scan a QR code containing contact data
3. **Generate QR Code**: Generate a QR code for sharing your contact
4. **Import Contact File**: Import contact from JSON/contact file
5. **Backup/Restore**: Export and import encrypted backups

### Widgets

#### ContactList & ContactListItem (`src/widgets/contact_list.py`)

Reusable components for displaying contacts:

**ContactListItem Features:**
- Presence indicator (green/orange/gray circle)
- Contact name (with nickname if set)
- Last message preview or onion address snippet
- Responsive layout with proper text wrapping

**ContactList Features:**
- Grid layout with dynamic sizing
- Add/remove/update contacts dynamically
- Selection callbacks for contact interaction

#### ContactDetailModal (`src/widgets/contact_detail_modal.py`)

Modal dialog for viewing and managing contact details:

**Features:**
- **Edit Nickname**: Update contact display name
- **Favorite Toggle**: Mark/unmark as favorite
- **Block/Unblock**: Block unwanted contacts
- **Mute/Unmute**: Manage notification preferences
- **Report**: Report malicious contacts
- **Share**: Generate and share contact card via QR
- **Verify**: View and manage verification fingerprints
  - Shows fingerprint with guided checklist
  - Option to mark contact as verified
  - Tracks verification state and timestamp
- **Save**: Persist changes to contact database

## Event System

The implementation extends the event bus with the following contact-related events:

```python
# General notifications
on_contacts_updated()

# Contact lifecycle
on_contact_added(contact_id, contact)
on_contact_deleted(contact_id)
on_contact_updated(contact_id, contact)

# Contact states
on_contact_favorited(contact_id, is_favorite)
on_contact_blocked(contact_id, is_blocked)
on_contact_muted(contact_id, is_muted)
on_contact_archived(contact_id, is_archived)

# Verification and presence
on_contact_verified(contact_id, is_verified)
on_contact_presence_updated(contact_id, status)

# Contact requests
on_contact_request_created(request_id)
on_contact_request_accepted(request_id)
on_contact_request_declined(request_id)

# Data operations
on_contact_imported(contact_id)
on_backup_imported()
```

## Encryption

The contact data uses **Fernet encryption** from the cryptography library:

- **Key Storage**: Encryption key stored in `~/.contact_manager/contacts.key`
- **Data Storage**: Encrypted JSON stored in `~/.contact_manager/contacts.enc`
- **Format**: Encrypted data is base64-encoded for storage
- **Security**: Fernet provides AES encryption with authentication

## Data Structure

### Contact Object

```python
{
    'id': 'contact_id',
    'name': 'Contact Name',
    'onion_address': 'address.onion',
    'nickname': 'Optional Nickname',
    'groups': ['group1', 'group2'],
    'created_at': 'ISO timestamp',
    'last_message_preview': 'Last message...',
    'last_message_time': 'ISO timestamp',
    'presence_status': 'online|offline|connecting',
    'verified': False,
    'custom_fields': {}
}
```

### Fingerprint Object

```python
{
    'fingerprint': 'ABCD1234EFGH5678...',
    'verified': False,
    'verified_at': 'ISO timestamp or None'
}
```

### Contact Request Object

```python
{
    'id': 'request_id',
    'from_id': 'requester_contact_id',
    'to_id': 'recipient_contact_id',
    'memo': 'Optional message',
    'created_at': 'ISO timestamp',
    'status': 'pending|accepted|declined',
    'accepted_at': 'ISO timestamp or None',
    'declined_at': 'ISO timestamp or None'
}
```

## QR Code Functionality

### QR Code Format

```json
{
    "type": "contact",
    "onion_address": "address.onion",
    "name": "Contact Name",
    "timestamp": "ISO timestamp"
}
```

### Generation

```python
from src.services.contact_service import contact_service

qr_img = contact_service.generate_qr_code('address.onion', 'Contact Name')
# Returns: BytesIO object containing PNG image
```

### Importing

```python
payload = {
    "type": "contact",
    "onion_address": "address.onion",
    "name": "Contact Name"
}
contact_id = contact_service.import_contact_from_qr(payload)
```

## Backup and Restore

### Export Backup

```python
encrypted_backup = contact_service.export_backup()
# Returns: Encrypted string (base64 encoded)
```

### Import Backup

```python
success = contact_service.import_backup(encrypted_backup)
# Returns: True if successful, False otherwise
```

The backup includes all contacts, groups, preferences, and metadata with proper encryption.

## Usage Examples

### Adding a Contact

```python
from src.services.contact_service import contact_service

contact = contact_service.add_contact(
    'contact_id',
    'John Doe',
    'john123456789.onion',
    nickname='Johnny'
)
```

### Searching Contacts

```python
results = contact_service.search_contacts('john')
# Returns dictionary of matching contacts
```

### Managing Contact State

```python
# Favorite
contact_service.add_to_favorite('contact_id')
contact_service.remove_from_favorite('contact_id')
is_fav = contact_service.is_favorite('contact_id')

# Block
contact_service.block_contact('contact_id')
contact_service.unblock_contact('contact_id')
is_blocked = contact_service.is_blocked('contact_id')

# Mute
contact_service.mute_contact('contact_id')
contact_service.unmute_contact('contact_id')
is_muted = contact_service.is_muted('contact_id')

# Archive
contact_service.archive_contact('contact_id')
contact_service.unarchive_contact('contact_id')
is_archived = contact_service.is_archived('contact_id')
```

### Contact Requests

```python
# Create request
request_id = contact_service.create_contact_request(
    'alice',
    'bob',
    'Hey Bob, can we chat?'
)

# Accept request
contact_service.accept_contact_request(request_id)

# Decline request
contact_service.decline_contact_request(request_id)

# Get pending requests
pending = contact_service.get_pending_requests()
```

### Verification

```python
# Set fingerprint
contact_service.set_verification_fingerprint(
    'contact_id',
    'ABCD1234EFGH5678IJKL9012MNOP3456',
    verified=True
)

# Get fingerprint
fp_data = contact_service.get_verification_fingerprint('contact_id')
```

### Groups

```python
# Add to group
contact_service.add_to_group('contact_id', 'Work')

# Remove from group
contact_service.remove_from_group('contact_id', 'Work')

# Get group contacts
work_contacts = contact_service.get_group_contacts('Work')

# Get all groups
groups = contact_service.get_all_groups()
```

## Testing

Comprehensive test suite in `tests/test_contact_service.py` with 21 unit tests covering:

- Contact CRUD operations
- Search and sorting
- Favorite/block/mute/archive operations
- Verification fingerprints
- QR code generation and import
- Backup/restore encryption
- Contact request workflow
- Presence status management

### Running Tests

```bash
python -m unittest tests.test_contact_service -v
```

All tests pass and verify core functionality.

## Dependencies

**New Dependencies:**
- `qrcode[pil]>=7.3.1` - QR code generation
- `cryptography>=38.0.0` - Fernet encryption

**Existing Dependencies:**
- `kivy>=2.2.0` - UI framework

## Integration with Messaging

The contact manager integrates with messaging through:

1. **Last Message Preview**: Updated by messaging service when messages are sent/received
2. **Presence Indicators**: Updated via event bus when connection status changes
3. **Blocked/Muted State**: Enforced by messaging UI to prevent sending to blocked contacts and suppressing notifications for muted contacts

## Future Enhancements

Potential improvements for future phases:

- Multi-device sync using backup/restore as foundation
- Direct contact import from device filesystem
- Photo/avatar support for contacts
- Custom verification methods beyond fingerprints
- Contact statistics (message count, last active time)
- Smart grouping and suggestions
- Advanced search filters
- Contact templates/cards for sharing

## Security Considerations

1. **Encryption Key**: Stored locally in user's home directory
2. **No Network Communication**: All operations are local
3. **State Management**: Blocked/muted states prevent unauthorized access
4. **Verification**: Fingerprint system allows manual verification of contact identity
5. **Backup Security**: Encrypted backup format prevents unauthorized restore

## File Structure

```
src/
├── services/
│   └── contact_service.py          # Main contact management service
├── screens/
│   └── contacts_screen.py          # Contact manager screen
├── widgets/
│   ├── contact_list.py             # Contact list components
│   └── contact_detail_modal.py      # Contact detail modal
└── utils/
    └── event_bus.py                # Extended with contact events

tests/
└── test_contact_service.py         # Comprehensive unit tests
```

## Notes

- All user data is stored encrypted at rest
- Event bus ensures UI updates propagate throughout the application
- ContactService is a singleton, accessible globally via `from src.services.contact_service import contact_service`
- Theme colors automatically update all UI components
- Responsive design adapts to various window sizes
