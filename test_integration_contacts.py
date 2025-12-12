#!/usr/bin/env python3
"""
Integration test for the Contact Manager implementation.
Tests basic workflow without running the full Kivy app.
"""

import sys
import tempfile
import os
from unittest.mock import MagicMock, patch


def test_contact_service_integration():
    """Test basic contact service operations."""
    print("Testing Contact Service Integration...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the App.get_running_app() to use temp directory
        with patch('kivy.app.App.get_running_app') as mock_app:
            mock_app_instance = MagicMock()
            mock_app_instance.user_data_dir = tmpdir
            mock_app.return_value = mock_app_instance
            
            # Import contact service
            from src.services.contact_service import ContactService
            
            # Create a new instance for testing
            service = ContactService()
            service._store_path = os.path.join(tmpdir, 'contacts.enc')
            
            # Test 1: Add contacts
            print("  ✓ Adding contacts...")
            c1 = service.add_contact('alice_id', 'Alice', 'alice123.onion', nickname='Alice')
            c2 = service.add_contact('bob_id', 'Bob', 'bob456.onion')
            assert c1['name'] == 'Alice'
            assert c2['name'] == 'Bob'
            
            # Test 2: Retrieve contacts
            print("  ✓ Retrieving contacts...")
            contacts = service.get_all_contacts()
            assert len(contacts) == 2
            
            # Test 3: Search contacts
            print("  ✓ Searching contacts...")
            results = service.search_contacts('Alice')
            assert len(results) == 1
            assert 'alice_id' in results
            
            # Test 4: Favorite operations
            print("  ✓ Testing favorite operations...")
            service.add_to_favorite('alice_id')
            assert service.is_favorite('alice_id')
            assert not service.is_favorite('bob_id')
            
            # Test 5: Block operations
            print("  ✓ Testing block operations...")
            service.block_contact('bob_id')
            assert service.is_blocked('bob_id')
            
            # Test 6: Sorting
            print("  ✓ Testing sorting...")
            sorted_alpha = service.get_sorted_contacts('alphabetical')
            names = [c['name'] for c in sorted_alpha.values()]
            assert names == ['Alice', 'Bob']
            
            sorted_fav = service.get_sorted_contacts('favorites')
            # Alice should come first (favorite)
            assert list(sorted_fav.values())[0]['id'] == 'alice_id'
            
            # Test 7: Groups
            print("  ✓ Testing groups...")
            service.add_to_group('alice_id', 'Friends')
            service.add_to_group('bob_id', 'Friends')
            group_contacts = service.get_group_contacts('Friends')
            assert len(group_contacts) == 2
            
            # Test 8: Contact requests
            print("  ✓ Testing contact requests...")
            req_id = service.create_contact_request('alice_id', 'bob_id', 'Let\'s chat')
            assert req_id is not None
            
            pending = service.get_pending_requests()
            assert len(pending) == 1
            
            service.accept_contact_request(req_id)
            pending = service.get_pending_requests()
            assert len(pending) == 0
            
            # Test 9: Verification fingerprints
            print("  ✓ Testing verification fingerprints...")
            fp = 'ABCD1234EFGH5678IJKL9012MNOP3456'
            service.set_verification_fingerprint('alice_id', fp, verified=True)
            fp_data = service.get_verification_fingerprint('alice_id')
            assert fp_data['fingerprint'] == fp
            assert fp_data['verified']
            
            # Test 10: Last message preview
            print("  ✓ Testing last message preview...")
            service.set_last_message_preview('bob_id', 'Hello!', '2024-01-01T12:00:00')
            contact = service.get_contact('bob_id')
            assert contact['last_message_preview'] == 'Hello!'
            
            # Test 11: Presence status
            print("  ✓ Testing presence status...")
            service.set_presence_status('alice_id', 'online')
            contact = service.get_contact('alice_id')
            assert contact['presence_status'] == 'online'
            
            # Test 12: Backup and restore
            print("  ✓ Testing backup/restore...")
            backup = service.export_backup()
            assert isinstance(backup, str)
            assert len(backup) > 0
            
            # Create new service instance and import backup
            service2 = ContactService()
            service2._store_path = os.path.join(tmpdir, 'contacts2.enc')
            
            result = service2.import_backup(backup)
            assert result
            
            # Verify imported data
            restored_contacts = service2.get_all_contacts()
            assert len(restored_contacts) == 2
            assert service2.is_favorite('alice_id')
            assert service2.is_blocked('bob_id')
            
            print("  ✓ All integration tests passed!")


def test_event_bus_integration():
    """Test event bus contact events."""
    print("Testing Event Bus Integration...")
    
    from src.utils.event_bus import event_bus
    
    # Test that events are registered
    events_to_check = [
        'on_contacts_updated',
        'on_contact_added',
        'on_contact_deleted',
        'on_contact_updated',
        'on_contact_favorited',
        'on_contact_blocked',
        'on_contact_muted',
        'on_contact_archived',
        'on_contact_verified',
        'on_contact_presence_updated',
        'on_contact_request_created',
        'on_contact_request_accepted',
        'on_contact_request_declined',
        'on_contact_imported',
        'on_backup_imported',
    ]
    
    for event_name in events_to_check:
        assert hasattr(event_bus, f'emit_{event_name.replace("on_", "")}'), \
            f"Event bus missing emit method for {event_name}"
    
    print(f"  ✓ All {len(events_to_check)} contact events registered!")


def test_widgets_integration():
    """Test that widgets can be instantiated."""
    print("Testing Widgets Integration...")
    
    from src.widgets.contact_list import ContactList, ContactListItem
    
    # Test ContactList creation
    contacts = {
        'id1': {'id': 'id1', 'name': 'Alice', 'onion_address': 'alice.onion', 'presence_status': 'online'},
        'id2': {'id': 'id2', 'name': 'Bob', 'onion_address': 'bob.onion', 'presence_status': 'offline'},
    }
    
    contact_list = ContactList(contacts=contacts)
    assert contact_list is not None
    print("  ✓ ContactList widget instantiated!")
    
    print("  ✓ Widgets integration tests passed!")


def test_screen_integration():
    """Test that contacts screen can be created."""
    print("Testing ContactsScreen Integration...")
    
    from src.screens.contacts_screen import ContactsScreen
    
    # Create screen
    screen = ContactsScreen()
    assert screen.name == 'contacts'
    assert screen.current_tab == 'all'
    
    print("  ✓ ContactsScreen created successfully!")


def test_imports():
    """Test that all modules can be imported."""
    print("Testing Module Imports...")
    
    try:
        from src.services.contact_service import contact_service
        print("  ✓ contact_service imported")
        
        from src.screens.contacts_screen import ContactsScreen
        print("  ✓ ContactsScreen imported")
        
        from src.widgets.contact_list import ContactList, ContactListItem
        print("  ✓ contact_list widgets imported")
        
        from src.widgets.contact_detail_modal import ContactDetailModal
        print("  ✓ contact_detail_modal imported")
        
        from src.utils.event_bus import event_bus
        print("  ✓ event_bus imported")
        
        from src.main import MainApp
        print("  ✓ MainApp imported")
        
        print("  ✓ All imports successful!")
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    return True


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("Contact Manager Integration Tests")
        print("=" * 60)
        
        if not test_imports():
            sys.exit(1)
        
        print()
        test_event_bus_integration()
        
        print()
        test_contact_service_integration()
        
        print()
        test_widgets_integration()
        
        print()
        test_screen_integration()
        
        print()
        print("=" * 60)
        print("✓ All integration tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
