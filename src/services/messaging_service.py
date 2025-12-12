from datetime import datetime, timedelta
from kivy.clock import Clock
from src.utils.event_bus import event_bus


class Message:
    """Represents a single message."""
    
    def __init__(self, message_id, text, is_outgoing=False, timestamp=None, 
                 delivery_state='sent', reactions=None, is_pinned=False, attachments=None):
        self.id = message_id
        self.text = text
        self.is_outgoing = is_outgoing
        self.timestamp = timestamp or datetime.now()
        self.delivery_state = delivery_state
        self.reactions = reactions or []
        self.is_pinned = is_pinned
        self.attachments = attachments or []
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'is_outgoing': self.is_outgoing,
            'timestamp': self.timestamp,
            'delivery_state': self.delivery_state,
            'reactions': self.reactions,
            'is_pinned': self.is_pinned,
            'attachments': self.attachments,
        }


class Conversation:
    """Represents a conversation thread."""
    
    def __init__(self, conversation_id, name, last_message='', unread_count=0):
        self.id = conversation_id
        self.name = name
        self.last_message = last_message
        self.unread_count = unread_count
        self.messages = []
        self.typing_indicator_user = None
        self.read_receipts = {}
    
    def add_message(self, message):
        self.messages.append(message)
        self.last_message = message.text[:50]
    
    def get_pinned_message(self):
        for msg in self.messages:
            if msg.is_pinned:
                return msg
        return None
    
    def pin_message(self, message_id):
        for msg in self.messages:
            if msg.id == message_id:
                msg.is_pinned = True
                return True
        return False
    
    def unpin_message(self, message_id):
        for msg in self.messages:
            if msg.id == message_id:
                msg.is_pinned = False
                return True
        return False
    
    def add_reaction(self, message_id, emoji, user_id='me'):
        for msg in self.messages:
            if msg.id == message_id:
                for reaction in msg.reactions:
                    if reaction['emoji'] == emoji:
                        reaction['count'] = reaction.get('count', 1) + 1
                        return True
                msg.reactions.append({'emoji': emoji, 'count': 1})
                return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'last_message': self.last_message,
            'unread_count': self.unread_count,
            'messages': [m.to_dict() for m in self.messages],
        }


class MessagingService:
    """Mock messaging service with event emission."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessagingService, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance
    
    def __init__(self, **kwargs):
        if hasattr(self, '_initialized'):
            return
        
        self._service_running = False
        self._tick_event = None
        self._conversations = {}
        self._current_conversation_id = None
        self._typing_simulation_event = None
        self._search_results = []
        
        # Register event types for messaging
        event_bus.register_event_type('on_message_received')
        event_bus.register_event_type('on_typing_indicator')
        event_bus.register_event_type('on_read_receipt')
        event_bus.register_event_type('on_message_reacted')
        event_bus.register_event_type('on_message_pinned')
        event_bus.register_event_type('on_search_results')
        
        # Initialize mock conversations
        self._init_mock_data()
        
        self._initialized = True
    
    def _init_mock_data(self):
        """Initialize mock conversation data."""
        # Create sample conversations
        conv1 = Conversation('conv_1', 'Alice Johnson', 'That sounds great!', 2)
        conv2 = Conversation('conv_2', 'Bob Smith', 'See you soon!', 0)
        conv3 = Conversation('conv_3', 'Team Chat', 'Meeting at 3 PM', 5)
        
        # Add messages to conv1
        now = datetime.now()
        messages_1 = [
            Message('msg_1_1', 'Hey, how are you?', False, now - timedelta(hours=2)),
            Message('msg_1_2', 'I\'m doing great! How about you?', True, now - timedelta(hours=1, minutes=50)),
            Message('msg_1_3', 'Same here. Want to grab coffee?', False, now - timedelta(hours=1, minutes=40)),
            Message('msg_1_4', 'That sounds great!', True, now - timedelta(minutes=30)),
        ]
        for msg in messages_1:
            conv1.add_message(msg)
        
        # Add reactions to last message in conv1
        conv1.messages[-1].reactions = [{'emoji': '👍', 'count': 2}, {'emoji': '❤️', 'count': 1}]
        
        # Add messages to conv2
        messages_2 = [
            Message('msg_2_1', 'Did you finish the project?', False, now - timedelta(hours=3)),
            Message('msg_2_2', 'Yes, just sent it over!', True, now - timedelta(hours=2, minutes=50)),
            Message('msg_2_3', 'Perfect! See you soon!', False, now - timedelta(minutes=45)),
            Message('msg_2_4', 'See you soon!', True, now - timedelta(minutes=30), delivery_state='read'),
        ]
        for msg in messages_2:
            conv2.add_message(msg)
        
        # Add messages to conv3 (team chat)
        messages_3 = [
            Message('msg_3_1', 'Don\'t forget about the meeting!', False, now - timedelta(hours=4)),
            Message('msg_3_2', 'What time is it?', True, now - timedelta(hours=3, minutes=50)),
            Message('msg_3_3', 'Meeting at 3 PM', False, now - timedelta(hours=3, minutes=40)),
        ]
        for msg in messages_3:
            conv3.add_message(msg)
        
        # Pin a message in conv1
        conv1.pin_message('msg_1_3')
        
        self._conversations = {
            'conv_1': conv1,
            'conv_2': conv2,
            'conv_3': conv3,
        }
    
    def start_service(self):
        """Start the messaging service."""
        if self._service_running:
            return
        self._service_running = True
        self._tick_event = Clock.schedule_interval(self._tick, 5.0)
    
    def stop_service(self):
        """Stop the messaging service."""
        self._service_running = False
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None
        if self._typing_simulation_event:
            self._typing_simulation_event.cancel()
            self._typing_simulation_event = None
    
    def get_conversations(self):
        """Get list of conversations."""
        return [
            {
                'id': conv.id,
                'name': conv.name,
                'last_message': conv.last_message,
                'unread_count': conv.unread_count,
            }
            for conv in self._conversations.values()
        ]
    
    def get_conversation_messages(self, conversation_id):
        """Get messages for a conversation."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        self._current_conversation_id = conversation_id
        return [msg.to_dict() for msg in conv.messages]
    
    def send_message(self, conversation_id, text):
        """Send a message (mock)."""
        if conversation_id not in self._conversations:
            return False
        
        conv = self._conversations[conversation_id]
        msg = Message(f'msg_{conversation_id}_{len(conv.messages)}', text, is_outgoing=True)
        conv.add_message(msg)
        
        # Emit event
        event_bus.dispatch('on_message_received', msg.to_dict())
        
        # Simulate read state after a delay
        Clock.schedule_once(
            lambda dt: self._mark_message_read(conversation_id, msg.id),
            2.0
        )
        
        return True
    
    def _mark_message_read(self, conversation_id, message_id):
        """Mark a message as read."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return
        
        for msg in conv.messages:
            if msg.id == message_id and msg.is_outgoing:
                msg.delivery_state = 'read'
                event_bus.dispatch('on_read_receipt', {
                    'message_id': message_id,
                    'state': 'read',
                })
                break
    
    def search_messages(self, conversation_id, query):
        """Search messages in a conversation."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        
        results = []
        for msg in conv.messages:
            if query.lower() in msg.text.lower():
                results.append({
                    'message_id': msg.id,
                    'text': msg.text,
                    'highlighted': msg.text.replace(
                        query, f'[b]{query}[/b]'
                    ),
                })
        
        self._search_results = results
        event_bus.dispatch('on_search_results', results)
        return results
    
    def pin_message(self, conversation_id, message_id):
        """Pin a message."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return False
        
        # Unpin any currently pinned message
        for msg in conv.messages:
            if msg.is_pinned:
                msg.is_pinned = False
        
        # Pin the new message
        success = conv.pin_message(message_id)
        if success:
            event_bus.dispatch('on_message_pinned', {
                'conversation_id': conversation_id,
                'message_id': message_id,
                'pinned': True,
            })
        
        return success
    
    def unpin_message(self, conversation_id, message_id):
        """Unpin a message."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return False
        
        success = conv.unpin_message(message_id)
        if success:
            event_bus.dispatch('on_message_pinned', {
                'conversation_id': conversation_id,
                'message_id': message_id,
                'pinned': False,
            })
        
        return success
    
    def add_reaction(self, conversation_id, message_id, emoji):
        """Add a reaction to a message."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return False
        
        success = conv.add_reaction(message_id, emoji)
        if success:
            event_bus.dispatch('on_message_reacted', {
                'conversation_id': conversation_id,
                'message_id': message_id,
                'emoji': emoji,
            })
        
        return success
    
    def forward_message(self, conversation_id, message_id, target_conversation_id):
        """Forward a message to another conversation."""
        source_conv = self._conversations.get(conversation_id)
        target_conv = self._conversations.get(target_conversation_id)
        
        if not source_conv or not target_conv:
            return False
        
        # Find the message
        source_msg = None
        for msg in source_conv.messages:
            if msg.id == message_id:
                source_msg = msg
                break
        
        if not source_msg:
            return False
        
        # Create a forwarded copy
        forwarded = Message(
            f'fwd_{message_id}',
            f'[Forwarded] {source_msg.text}',
            is_outgoing=True,
        )
        target_conv.add_message(forwarded)
        event_bus.dispatch('on_message_received', forwarded.to_dict())
        
        return True
    
    def set_typing_indicator(self, conversation_id, is_typing, username='Someone'):
        """Set typing indicator for a user."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return False
        
        conv.typing_indicator_user = username if is_typing else None
        event_bus.dispatch('on_typing_indicator', {
            'conversation_id': conversation_id,
            'typing': is_typing,
            'username': username,
        })
        
        return True
    
    def _tick(self, dt):
        """Periodic service tick for mock events."""
        if not self._service_running or not self._current_conversation_id:
            return
        
        # Randomly simulate incoming messages or typing indicators
        import random
        
        if random.random() > 0.85:
            # Simulate incoming message
            conv_id = self._current_conversation_id
            conv = self._conversations.get(conv_id)
            if conv:
                incoming_msg = Message(
                    f'msg_{conv_id}_{len(conv.messages)}',
                    'This is a mock incoming message!',
                    is_outgoing=False,
                )
                conv.add_message(incoming_msg)
                event_bus.dispatch('on_message_received', incoming_msg.to_dict())


messaging_service = MessagingService()
