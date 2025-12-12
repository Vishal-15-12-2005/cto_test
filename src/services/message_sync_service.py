import time
from typing import Any

from kivy.clock import Clock

from src.services.message_store import MessageStatus, MessageStore
from src.utils.event_bus import event_bus


class MessageSyncService:
    def __init__(self, store: MessageStore):
        self._store = store
        self._tick_event = None
        self._online = False
        self._sending = False

        event_bus.bind(on_tor_state_update=self._on_tor_state_update)

    def start(self):
        if self._tick_event is not None:
            return
        self._tick_event = Clock.schedule_interval(lambda dt: self._tick(), 1.0)

    def stop(self):
        if self._tick_event is None:
            return
        self._tick_event.cancel()
        self._tick_event = None

    def set_online(self, online: bool):
        self._online = bool(online)
        if self._online:
            self.flush_outgoing_queue()

    def queue_outgoing_message(
        self,
        conversation_id: str,
        message_id: str,
        *,
        sender_id: str | None = None,
        body: str | None = None,
        created_at: float | None = None,
        ttl_seconds: int | None = None,
        message_type: str = 'text',
    ) -> dict[str, Any]:
        msg = self._store.upsert_message(
            conversation_id,
            message_id,
            sender_id=sender_id,
            body=body,
            created_at=created_at,
            status='queued',
            is_outgoing=True,
            ttl_seconds=ttl_seconds,
            message_type=message_type,
        )

        if self._online:
            self.flush_outgoing_queue()
        return msg

    def apply_receipt(self, _conversation_id: str, message_id: str, status: MessageStatus):
        # MessageStore will emit receipt + message update events.
        self._store.update_message_status(message_id, status)

    def apply_incoming_packet(self, packet: dict[str, Any]) -> dict[str, Any] | None:
        message_id = str(packet.get('message_id') or '')
        conversation_id = str(packet.get('conversation_id') or '')
        if not message_id or not conversation_id:
            return None

        existing = self._store.get_message(message_id)
        if existing is not None:
            return existing

        msg = self._store.upsert_message(
            conversation_id,
            message_id,
            sender_id=packet.get('sender_id'),
            body=packet.get('body'),
            created_at=float(packet.get('created_at') or time.time()),
            status=str(packet.get('status') or 'delivered'),
            is_outgoing=False,
            ttl_seconds=packet.get('ttl_seconds'),
            message_type=str(packet.get('message_type') or 'text'),
        )
        return msg

    def set_typing_state(self, conversation_id: str, peer_id: str, is_typing: bool):
        event_bus.emit_typing_state(conversation_id, peer_id, bool(is_typing))

    def _on_tor_state_update(self, instance, state: dict[str, Any]):
        cs = state.get('connection_state')
        self.set_online(cs == 'connected')

    def _tick(self):
        if not self._online:
            return
        self.flush_outgoing_queue()

    def flush_outgoing_queue(self):
        if self._sending:
            return
        self._sending = True
        try:
            for msg in self._store.get_outgoing_queue(limit=100):
                self._attempt_send(msg)
        finally:
            self._sending = False

    def _attempt_send(self, msg: dict[str, Any]):
        # In the current codebase we don't have a network transport, so we
        # model a successful send once Tor is connected.
        mid = msg['id']
        self._store.update_message_status(mid, 'sent')

        def _confirm(dt):
            current = self._store.get_message(mid)
            if current is None:
                return
            if current['status'] == 'sent':
                self._store.update_message_status(mid, 'delivered')

        Clock.schedule_once(_confirm, 0)


message_sync_service: MessageSyncService | None = None


def get_message_sync_service(store: MessageStore) -> MessageSyncService:
    global message_sync_service
    if message_sync_service is None:
        message_sync_service = MessageSyncService(store)
        message_sync_service.start()
    return message_sync_service
