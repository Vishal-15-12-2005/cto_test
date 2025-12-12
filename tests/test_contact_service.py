import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from src.services.contact_service import ContactService


class TestContactService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_get_store_path = ContactService._get_store_path
        
        # Mock the _get_store_path to use our temp directory
        self.contact_service = ContactService()
        self.contact_service._store_path = os.path.join(self.test_dir, 'contacts.enc')

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_contact(self):
        """Test adding a contact."""
        contact_id = 'test123'
        contact_data = self.contact_service.add_contact(
            contact_id,
            'Test User',
            'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl.onion'
        )
        
        self.assertEqual(contact_data['id'], contact_id)
        self.assertEqual(contact_data['name'], 'Test User')
        self.assertIsNotNone(contact_data['created_at'])

    def test_get_contact(self):
        """Test retrieving a contact."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl.onion'
        )
        
        contact = self.contact_service.get_contact(contact_id)
        self.assertIsNotNone(contact)
        self.assertEqual(contact['name'], 'Test User')

    def test_search_contacts(self):
        """Test searching contacts by name."""
        self.contact_service.add_contact(
            'id1', 'Alice', 'alice.onion'
        )
        self.contact_service.add_contact(
            'id2', 'Bob', 'bob.onion'
        )
        self.contact_service.add_contact(
            'id3', 'Charlie', 'charlie.onion'
        )
        
        results = self.contact_service.search_contacts('Alice')
        self.assertEqual(len(results), 1)
        self.assertIn('id1', results)

    def test_delete_contact(self):
        """Test deleting a contact."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        result = self.contact_service.delete_contact(contact_id)
        self.assertTrue(result)
        
        contact = self.contact_service.get_contact(contact_id)
        self.assertIsNone(contact)

    def test_favorite_contact(self):
        """Test marking contact as favorite."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        self.contact_service.add_to_favorite(contact_id)
        self.assertTrue(self.contact_service.is_favorite(contact_id))
        
        self.contact_service.remove_from_favorite(contact_id)
        self.assertFalse(self.contact_service.is_favorite(contact_id))

    def test_block_contact(self):
        """Test blocking a contact."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        self.contact_service.block_contact(contact_id)
        self.assertTrue(self.contact_service.is_blocked(contact_id))
        
        self.contact_service.unblock_contact(contact_id)
        self.assertFalse(self.contact_service.is_blocked(contact_id))

    def test_mute_contact(self):
        """Test muting a contact."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        self.contact_service.mute_contact(contact_id)
        self.assertTrue(self.contact_service.is_muted(contact_id))
        
        self.contact_service.unmute_contact(contact_id)
        self.assertFalse(self.contact_service.is_muted(contact_id))

    def test_archive_contact(self):
        """Test archiving a contact."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        self.contact_service.archive_contact(contact_id)
        self.assertTrue(self.contact_service.is_archived(contact_id))
        
        self.contact_service.unarchive_contact(contact_id)
        self.assertFalse(self.contact_service.is_archived(contact_id))

    def test_sort_contacts_alphabetical(self):
        """Test sorting contacts alphabetically."""
        self.contact_service.add_contact('id3', 'Charlie', 'charlie.onion')
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        self.contact_service.add_contact('id2', 'Bob', 'bob.onion')
        
        sorted_contacts = self.contact_service.get_sorted_contacts('alphabetical')
        names = [c['name'] for c in sorted_contacts.values()]
        
        self.assertEqual(names, ['Alice', 'Bob', 'Charlie'])

    def test_sort_contacts_recent(self):
        """Test sorting contacts by recent messages."""
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        self.contact_service.add_contact('id2', 'Bob', 'bob.onion')
        
        # Set last message times
        self.contact_service.set_last_message_preview('id1', 'Hi Alice', '2024-01-02')
        self.contact_service.set_last_message_preview('id2', 'Hi Bob', '2024-01-03')
        
        sorted_contacts = self.contact_service.get_sorted_contacts('recent')
        names = [c['name'] for c in sorted_contacts.values()]
        
        # Recent should be first
        self.assertEqual(names[0], 'Bob')

    def test_sort_contacts_favorites(self):
        """Test sorting with favorites first."""
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        self.contact_service.add_contact('id2', 'Bob', 'bob.onion')
        
        self.contact_service.add_to_favorite('id2')
        
        sorted_contacts = self.contact_service.get_sorted_contacts('favorites')
        names = [c['name'] for c in sorted_contacts.values()]
        
        # Favorite should be first
        self.assertEqual(names[0], 'Bob')

    def test_update_nickname(self):
        """Test updating contact nickname."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        self.contact_service.set_nickname(contact_id, 'Nickname')
        contact = self.contact_service.get_contact(contact_id)
        self.assertEqual(contact['nickname'], 'Nickname')

    def test_verification_fingerprint(self):
        """Test setting and getting verification fingerprint."""
        contact_id = 'test123'
        self.contact_service.add_contact(
            contact_id,
            'Test User',
            'test.onion'
        )
        
        fingerprint = 'ABCD1234EFGH5678IJKL9012MNOP3456'
        self.contact_service.set_verification_fingerprint(contact_id, fingerprint, verified=True)
        
        fp_data = self.contact_service.get_verification_fingerprint(contact_id)
        self.assertEqual(fp_data['fingerprint'], fingerprint)
        self.assertTrue(fp_data['verified'])

    def test_qr_code_generation(self):
        """Test QR code generation."""
        onion = 'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl.onion'
        qr_img = self.contact_service.generate_qr_code(onion, 'Test Contact')
        
        # Check that we got a BytesIO object
        self.assertIsNotNone(qr_img)
        self.assertTrue(len(qr_img.getvalue()) > 0)

    def test_import_from_qr(self):
        """Test importing contact from QR payload."""
        payload = {
            'type': 'contact',
            'onion_address': 'test123456789.onion',
            'name': 'Test User',
        }
        
        contact_id = self.contact_service.import_contact_from_qr(payload)
        self.assertIsNotNone(contact_id)
        
        contact = self.contact_service.get_contact(contact_id)
        self.assertEqual(contact['name'], 'Test User')

    def test_backup_export_import(self):
        """Test exporting and importing backup."""
        # Add some contacts
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        self.contact_service.add_contact('id2', 'Bob', 'bob.onion')
        self.contact_service.add_to_favorite('id1')
        
        # Export backup
        backup = self.contact_service.export_backup()
        self.assertIsNotNone(backup)
        self.assertIsInstance(backup, str)
        
        # Create a new service instance
        new_service = ContactService()
        new_service._store_path = os.path.join(self.test_dir, 'contacts2.enc')
        
        # Import backup
        result = new_service.import_backup(backup)
        self.assertTrue(result)
        
        # Verify data
        self.assertIn('id1', new_service.get_all_contacts())
        self.assertIn('id2', new_service.get_all_contacts())
        self.assertTrue(new_service.is_favorite('id1'))

    def test_contact_request_create_accept(self):
        """Test creating and accepting a contact request."""
        request_id = self.contact_service.create_contact_request('alice', 'bob', 'Hey Bob!')
        self.assertIsNotNone(request_id)
        
        pending = self.contact_service.get_pending_requests()
        self.assertIn(request_id, pending)
        
        result = self.contact_service.accept_contact_request(request_id)
        self.assertTrue(result)
        
        pending = self.contact_service.get_pending_requests()
        self.assertNotIn(request_id, pending)

    def test_contact_request_decline(self):
        """Test declining a contact request."""
        request_id = self.contact_service.create_contact_request('alice', 'bob')
        
        result = self.contact_service.decline_contact_request(request_id)
        self.assertTrue(result)
        
        pending = self.contact_service.get_pending_requests()
        self.assertNotIn(request_id, pending)

    def test_groups(self):
        """Test contact groups functionality."""
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        self.contact_service.add_contact('id2', 'Bob', 'bob.onion')
        
        self.contact_service.add_to_group('id1', 'Work')
        self.contact_service.add_to_group('id2', 'Work')
        
        group_contacts = self.contact_service.get_group_contacts('Work')
        self.assertEqual(len(group_contacts), 2)

    def test_presence_status(self):
        """Test setting and getting presence status."""
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        
        self.contact_service.set_presence_status('id1', 'online')
        contact = self.contact_service.get_contact('id1')
        self.assertEqual(contact['presence_status'], 'online')
        
        self.contact_service.set_presence_status('id1', 'offline')
        contact = self.contact_service.get_contact('id1')
        self.assertEqual(contact['presence_status'], 'offline')

    def test_last_message_preview(self):
        """Test setting last message preview."""
        self.contact_service.add_contact('id1', 'Alice', 'alice.onion')
        
        self.contact_service.set_last_message_preview('id1', 'Hey Alice!', '2024-01-01T10:00:00')
        contact = self.contact_service.get_contact('id1')
        self.assertEqual(contact['last_message_preview'], 'Hey Alice!')


if __name__ == '__main__':
    unittest.main()
