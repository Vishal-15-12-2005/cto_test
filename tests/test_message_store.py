import os
import tempfile
import time
import unittest

from kivy.clock import Clock

from src.services.message_store import MessageStore
from src.services.message_sync_service import MessageSyncService
from src.utils.event_bus import event_bus


class TestMessageStore(unittest.TestCase):
    def test_encryption_key_handling_and_no_plaintext(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='correct-horse-battery-staple', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')
            store.upsert_message(
                'c1',
                'm1',
                sender_id='alice',
                body='secret message',
                created_at=time.time(),
                status='sent',
            )
            store.close()

            with open(db_path, 'rb') as f:
                raw = f.read()
            self.assertNotIn(b'secret message', raw)

            with self.assertRaises(ValueError):
                bad = MessageStore(key='wrong-key', db_path=db_path)
                bad.close()

    def test_pagination_returns_chronological_order(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='k1', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')

            base = time.time() - 1000
            for i in range(25):
                store.upsert_message(
                    'c1',
                    f'm{i:03d}',
                    sender_id='alice',
                    body=f'msg {i}',
                    created_at=base + i,
                    status='delivered',
                )

            batch = store.fetch_history('c1', limit=10)
            self.assertEqual(len(batch), 10)
            self.assertEqual([m['id'] for m in batch], [f'm{i:03d}' for i in range(15, 25)])
            self.assertTrue(all(batch[i]['created_at'] <= batch[i + 1]['created_at'] for i in range(len(batch) - 1)))

            older = store.fetch_history('c1', limit=10, before=batch[0])
            self.assertEqual(len(older), 10)
            self.assertEqual([m['id'] for m in older], [f'm{i:03d}' for i in range(5, 15)])

            store.close()

    def test_disappearing_message_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='k1', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')

            created = time.time()
            store.upsert_message(
                'c1',
                'm1',
                sender_id='alice',
                body='tmp',
                created_at=created,
                status='sent',
                ttl_seconds=0,
            )

            deleted = store.cleanup_expired(now=created + 0.1)
            self.assertEqual(deleted, 1)
            self.assertEqual(store.fetch_history('c1', limit=10), [])
            store.close()

    def test_reaction_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='k1', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')
            store.upsert_message('c1', 'm1', sender_id='alice', body='hey', status='sent')
            store.add_reaction('m1', actor_id='bob', emoji='👍')
            store.close()

            store2 = MessageStore(key='k1', db_path=db_path)
            msg = store2.get_message('m1')
            self.assertIsNotNone(msg)
            self.assertEqual(len(msg['reactions']), 1)
            self.assertEqual(msg['reactions'][0]['emoji'], '👍')
            store2.close()

    def test_read_receipt_propagation_event(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='k1', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')
            store.upsert_message('c1', 'm1', sender_id='alice', body='hey', status='delivered')

            received = []

            def _on_receipt(instance, conversation_id, message_id, status):
                received.append((conversation_id, message_id, status))

            event_bus.bind(on_receipt_update=_on_receipt)
            store.update_message_status('m1', 'read')

            self.assertTrue(received)
            self.assertEqual(received[-1][0], 'c1')
            self.assertEqual(received[-1][1], 'm1')
            self.assertEqual(received[-1][2], 'read')

            event_bus.unbind(on_receipt_update=_on_receipt)
            store.close()

    def test_sync_queue_and_retry_on_connectivity(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, 'messages.db')
            store = MessageStore(key='k1', db_path=db_path)
            store.upsert_conversation('c1', title='Chat')
            sync = MessageSyncService(store)

            sync.set_online(False)
            sync.queue_outgoing_message('c1', 'm1', sender_id='me', body='hi')
            self.assertEqual(store.get_message('m1')['status'], 'queued')

            sync.set_online(True)
            for _ in range(5):
                Clock.tick()

            self.assertIn(store.get_message('m1')['status'], {'sent', 'delivered'})
            store.close()


if __name__ == '__main__':
    unittest.main()
