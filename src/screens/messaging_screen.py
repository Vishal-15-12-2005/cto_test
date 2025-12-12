from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

from src.services.messaging_service import messaging_service
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.chat_components import (
    ChatBubble,
    TypingIndicator,
    PinnedMessageBanner,
    MessageActionMenu,
    MessageComposer,
    MessageSearchBar,
    ConversationListItem,
    format_timestamp,
)


class MessagingScreen(Screen):
    """Responsive messaging surface with master/detail layout."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'messages'
        
        self.current_conversation_id = None
        self.current_conversation_name = 'Select a conversation'
        self.search_active = False
        self.search_results = []
        self.current_search_index = 0
        
        # Main container
        self.root = BoxLayout(orientation='vertical')
        
        # Header
        self._create_header()
        self.root.add_widget(self.header)
        
        # Content area (will be swapped based on layout)
        self.content_container = BoxLayout()
        self.root.add_widget(self.content_container)
        
        # Message composer
        self.composer = MessageComposer(
            on_send=self._on_send_message,
            on_attach=self._on_attach,
            on_disappearing=self._on_disappearing_toggle,
        )
        self.root.add_widget(self.composer)
        
        self.add_widget(self.root)
        
        # Window binding for responsive layout
        Window.bind(size=lambda *_: self._update_layout())
        self.current_layout = None
        self._update_layout()
        
        # Event bus bindings
        event_bus.bind(on_message_received=self._on_message_received)
        event_bus.bind(on_typing_indicator=self._on_typing_indicator)
        event_bus.bind(on_message_reacted=self._on_message_reacted)
        event_bus.bind(on_message_pinned=self._on_message_pinned)
        event_bus.bind(on_read_receipt=self._on_read_receipt)
        
        # Bootstrap
        Clock.schedule_once(lambda dt: self._bootstrap(), 0)
    
    def _create_header(self):
        """Create the header with title and controls."""
        self.header = BoxLayout(orientation='horizontal', padding=[dp(16), dp(12)], spacing=dp(12), size_hint_y=None, height=dp(56))
        
        self.title = Label(
            text=self.current_conversation_name,
            font_size=theme_manager.typography.H5,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
            size_hint_x=0.7,
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))
        
        # Search icon
        search_btn = Button(
            text='🔍',
            size_hint_x=None,
            width=dp(40),
            on_release=self._toggle_search,
        )
        
        # Settings/info icon
        info_btn = Button(
            text='ℹ️',
            size_hint_x=None,
            width=dp(40),
            on_release=self._on_info,
        )
        
        self.header.add_widget(self.title)
        self.header.add_widget(BoxLayout())  # Spacer
        self.header.add_widget(search_btn)
        self.header.add_widget(info_btn)
    
    def _bootstrap(self):
        """Load initial data."""
        conversations = messaging_service.get_conversations()
        if conversations:
            self._load_conversation(conversations[0]['id'])
    
    def _create_conversation_list(self):
        """Create the left-side conversation list."""
        container = BoxLayout(orientation='vertical', size_hint_x=0.35)
        
        # List title
        list_title = Label(
            text='Conversations',
            font_size=theme_manager.typography.H6,
            color=theme_manager.text_color,
            size_hint_y=None,
            height=dp(40),
            halign='left',
        )
        list_title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        container.add_widget(list_title)
        
        # Scrollable conversation list
        scroll = ScrollView(do_scroll_x=False)
        self.conv_list = GridLayout(cols=1, spacing=dp(4), padding=dp(8), size_hint_y=None)
        self.conv_list.bind(minimum_height=self.conv_list.setter('height'))
        
        conversations = messaging_service.get_conversations()
        for conv in conversations:
            item = ConversationListItem(
                conversation_id=conv['id'],
                name=conv['name'],
                last_message=conv['last_message'],
                unread_count=conv['unread_count'],
                on_select=lambda cid=conv['id']: self._load_conversation(cid),
            )
            self.conv_list.add_widget(item)
        
        scroll.add_widget(self.conv_list)
        container.add_widget(scroll)
        
        return container
    
    def _create_message_feed(self):
        """Create the right-side message feed."""
        container = BoxLayout(orientation='vertical')
        
        # Pinned message banner (if applicable)
        self.pinned_banner = None
        
        # Message scroll area
        scroll = ScrollView(do_scroll_x=False)
        self.message_list = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None)
        self.message_list.bind(minimum_height=self.message_list.setter('height'))
        
        # Add messages
        messages = messaging_service.get_conversation_messages(self.current_conversation_id)
        for msg in messages:
            bubble = self._create_chat_bubble(msg)
            self.message_list.add_widget(bubble)
        
        # Check for pinned message and add banner
        if messages:
            for msg in messages:
                if msg.get('is_pinned'):
                    self.pinned_banner = PinnedMessageBanner(
                        message_text=msg['text'],
                        on_close=self._close_pinned_banner,
                    )
                    container.add_widget(self.pinned_banner)
                    break
        
        scroll.add_widget(self.message_list)
        container.add_widget(scroll)
        
        return container
    
    def _create_chat_bubble(self, msg_dict):
        """Create a chat bubble widget from message data."""
        return ChatBubble(
            text=msg_dict['text'],
            is_outgoing=msg_dict['is_outgoing'],
            timestamp=format_timestamp(msg_dict['timestamp']),
            delivery_state=msg_dict.get('delivery_state', 'sent'),
            reactions=msg_dict.get('reactions', []),
            is_pinned=msg_dict.get('is_pinned', False),
            attachments=msg_dict.get('attachments', []),
            on_menu=lambda action, bubble, mid=msg_dict['id']: self._on_message_action(action, mid),
            size_hint_y=None,
        )
    
    def _update_layout(self):
        """Update layout based on window size (responsive)."""
        width, _ = Window.size
        new_layout = 'desktop' if width >= dp(900) else 'mobile'
        
        if self.current_layout == new_layout:
            return
        
        self.current_layout = new_layout
        self.content_container.clear_widgets()
        
        if new_layout == 'desktop':
            # Master/detail layout
            conv_list = self._create_conversation_list()
            msg_feed = self._create_message_feed()
            
            self.content_container.add_widget(conv_list)
            self.content_container.add_widget(msg_feed)
        else:
            # Stacked mobile layout
            if self.current_conversation_id:
                msg_feed = self._create_message_feed()
                self.content_container.add_widget(msg_feed)
            else:
                conv_list = self._create_conversation_list()
                self.content_container.add_widget(conv_list)
    
    def _load_conversation(self, conversation_id):
        """Load a conversation and update the view."""
        self.current_conversation_id = conversation_id
        
        # Update header title
        conversations = messaging_service.get_conversations()
        for conv in conversations:
            if conv['id'] == conversation_id:
                self.current_conversation_name = conv['name']
                self.title.text = self.current_conversation_name
                break
        
        messaging_service.set_typing_indicator(conversation_id, False)
        
        # Refresh layout
        self._update_layout()
    
    def _on_send_message(self, text):
        """Handle message send."""
        if not text.strip() or not self.current_conversation_id:
            return
        
        messaging_service.send_message(self.current_conversation_id, text)
        self._refresh_message_feed()
    
    def _on_attach(self):
        """Handle attach button click."""
        # Stub for attachment functionality
        popup = Popup(
            title='Attachments',
            content=Label(text='Attachment picker coming soon...'),
            size_hint=(0.6, 0.4),
        )
        popup.open()
    
    def _on_disappearing_toggle(self):
        """Handle disappearing message toggle."""
        # Stub for disappearing message toggle
        pass
    
    def _on_message_action(self, action, message_id):
        """Handle message context menu actions."""
        if action == 'menu':
            menu = MessageActionMenu(
                message=message_id,
                on_pin=lambda mid: self._pin_message(mid),
                on_react=lambda mid: self._open_reaction_picker(mid),
                on_forward=lambda mid: self._forward_message(mid),
                on_delete=lambda mid: self._delete_message(mid),
            )
            menu.open()
        elif action == 'react':
            self._open_reaction_picker(message_id)
    
    def _pin_message(self, message_id):
        """Pin a message."""
        if not self.current_conversation_id:
            return
        
        messaging_service.pin_message(self.current_conversation_id, message_id)
        self._refresh_message_feed()
    
    def _open_reaction_picker(self, message_id):
        """Open a popup to pick reaction emoji."""
        reactions = ['👍', '❤️', '😂', '😮', '😢', '🔥', '✅', '🚀']
        
        content = GridLayout(cols=4, padding=dp(16), spacing=dp(8))
        for emoji in reactions:
            btn = Button(
                text=emoji,
                size_hint_y=None,
                height=dp(60),
                on_release=lambda x, e=emoji, mid=message_id: (
                    self._add_reaction(mid, e),
                    popup.dismiss(),
                ),
            )
            content.add_widget(btn)
        
        popup = Popup(
            title='React',
            content=content,
            size_hint=(0.8, 0.4),
        )
        popup.open()
    
    def _add_reaction(self, message_id, emoji):
        """Add a reaction to a message."""
        if not self.current_conversation_id:
            return
        
        messaging_service.add_reaction(self.current_conversation_id, message_id, emoji)
        self._refresh_message_feed()
    
    def _forward_message(self, message_id):
        """Forward a message to another conversation."""
        # Stub for forward functionality
        conversations = messaging_service.get_conversations()
        content = GridLayout(cols=1, padding=dp(16), spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        for conv in conversations:
            if conv['id'] != self.current_conversation_id:
                btn = Button(
                    text=conv['name'],
                    size_hint_y=None,
                    height=dp(48),
                    on_release=lambda x, cid=conv['id'], mid=message_id: (
                        messaging_service.forward_message(self.current_conversation_id, mid, cid),
                        popup.dismiss(),
                    ),
                )
                content.add_widget(btn)
        
        scroll = ScrollView()
        scroll.add_widget(content)
        
        popup = Popup(
            title='Forward to',
            content=scroll,
            size_hint=(0.8, 0.6),
        )
        popup.open()
    
    def _delete_message(self, message_id):
        """Delete a message (stub)."""
        pass
    
    def _toggle_search(self):
        """Toggle search bar visibility."""
        self.search_active = not self.search_active
        
        if self.search_active:
            search_bar = MessageSearchBar(
                on_search=self._on_search,
                on_navigate=self._on_search_navigate,
            )
            self.root.add_widget(search_bar, index=1)
            self.search_bar = search_bar
        else:
            if hasattr(self, 'search_bar'):
                self.root.remove_widget(self.search_bar)
            self._refresh_message_feed()
    
    def _on_search(self, query):
        """Handle message search."""
        if not query.strip() or not self.current_conversation_id:
            return
        
        self.search_results = messaging_service.search_messages(
            self.current_conversation_id, query
        )
        self.current_search_index = 0
        self._refresh_message_feed()
    
    def _on_search_navigate(self, direction):
        """Navigate through search results."""
        if not self.search_results:
            return
        
        if direction == 'next':
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        else:
            self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        
        self._refresh_message_feed()
    
    def _close_pinned_banner(self):
        """Close the pinned message banner."""
        if self.pinned_banner and self.pinned_banner.parent:
            self.pinned_banner.parent.remove_widget(self.pinned_banner)
            self.pinned_banner = None
    
    def _refresh_message_feed(self):
        """Refresh the message feed with current data."""
        if self.current_layout == 'mobile':
            # Refresh only if currently showing messages
            if self.current_conversation_id:
                self._update_layout()
        else:
            # Update message feed in desktop layout
            if hasattr(self, 'message_list'):
                self.message_list.clear_widgets()
                messages = messaging_service.get_conversation_messages(self.current_conversation_id)
                
                for msg in messages:
                    # Check if this message matches search
                    if self.search_results:
                        if msg['id'] not in [r['message_id'] for r in self.search_results]:
                            continue
                    
                    bubble = self._create_chat_bubble(msg)
                    self.message_list.add_widget(bubble)
    
    @mainthread
    def _on_message_received(self, instance, message):
        """Handle incoming message event."""
        if message.get('conversation_id') != self.current_conversation_id:
            return
        
        self._refresh_message_feed()
    
    @mainthread
    def _on_typing_indicator(self, instance, data):
        """Handle typing indicator event."""
        if data.get('conversation_id') != self.current_conversation_id:
            return
        
        if data.get('typing'):
            # Add typing indicator to message list
            if hasattr(self, 'message_list'):
                indicator = TypingIndicator(username=data.get('username', 'Someone'))
                self.message_list.add_widget(indicator)
        else:
            # Remove typing indicator
            if hasattr(self, 'message_list'):
                for widget in list(self.message_list.children):
                    if isinstance(widget, TypingIndicator):
                        self.message_list.remove_widget(widget)
    
    @mainthread
    def _on_message_reacted(self, instance, data):
        """Handle message reaction event."""
        if data.get('conversation_id') != self.current_conversation_id:
            return
        
        self._refresh_message_feed()
    
    @mainthread
    def _on_message_pinned(self, instance, data):
        """Handle message pinned event."""
        if data.get('conversation_id') != self.current_conversation_id:
            return
        
        self._update_layout()
    
    @mainthread
    def _on_read_receipt(self, instance, data):
        """Handle read receipt event."""
        self._refresh_message_feed()
    
    def _on_info(self):
        """Handle info button click."""
        popup = Popup(
            title='Conversation Info',
            content=Label(text='Conversation details coming soon...'),
            size_hint=(0.6, 0.4),
        )
        popup.open()
