from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.input.motionevent import MotionEvent
from src.theming.theme_manager import theme_manager
from src.theming.tokens import ColorPalette


def format_timestamp(dt=None):
    """Format a datetime object or use current time for message timestamps."""
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, str):
        return dt
    return dt.strftime('%H:%M')


class ChatBubble(BoxLayout):
    """Parameterized chat bubble that works for both incoming and outgoing messages."""
    
    def __init__(self, text='', is_outgoing=False, timestamp='', delivery_state='sent',
                 show_reactions=True, reactions=None, is_pinned=False, 
                 attachments=None, avatar=None, on_menu=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = dp(8)
        self.spacing = dp(4)
        
        self.is_outgoing = is_outgoing
        self.text = text
        self.timestamp = timestamp if timestamp else format_timestamp()
        self.delivery_state = delivery_state
        self.reactions = reactions or []
        self.is_pinned = is_pinned
        self.attachments = attachments or []
        self.on_menu = on_menu
        
        # Container for bubble and avatar
        bubble_container = BoxLayout(orientation='horizontal', size_hint_y=None, spacing=dp(8))
        
        # Avatar/spacer on left for incoming, right for outgoing
        if not is_outgoing:
            if avatar:
                bubble_container.add_widget(avatar)
            else:
                spacer = BoxLayout(size_hint_x=None, width=dp(36))
                bubble_container.add_widget(spacer)
        
        # Main bubble content
        bubble_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        # Pinned banner if applicable
        if is_pinned:
            pinned_banner = BoxLayout(size_hint_y=None, height=dp(24), padding=dp(4), spacing=dp(4))
            pinned_label = Label(
                text='📌 Pinned',
                font_size=theme_manager.typography.CAPTION,
                color=theme_manager.primary_color,
                size_hint_y=None,
                height=dp(16),
            )
            pinned_banner.add_widget(pinned_label)
            bubble_layout.add_widget(pinned_banner)
        
        # Message text with bubble background
        message_box = BoxLayout(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(4),
            size_hint_y=None,
        )
        
        with message_box.canvas.before:
            bubble_color = ColorPalette.PRIMARY if is_outgoing else ColorPalette.LIGHT_SURFACE
            if theme_manager.theme_mode == 'dark':
                bubble_color = ColorPalette.PRIMARY if is_outgoing else ColorPalette.DARK_SURFACE
            # Ensure bubble_color is a valid RGBA tuple
            if isinstance(bubble_color, (list, tuple)) and len(bubble_color) == 4:
                self.bubble_color_instruction = Color(rgba=bubble_color)
            elif isinstance(bubble_color, (list, tuple)) and len(bubble_color) == 3:
                self.bubble_color_instruction = Color(rgba=bubble_color + (1,))
            else:
                self.bubble_color_instruction = Color(rgba=(1, 1, 1, 1))
            self.bubble_rect = RoundedRectangle(size=message_box.size, pos=message_box.pos, radius=[dp(12)])
        
        message_box.bind(pos=self._update_bubble_rect, size=self._update_bubble_rect)
        
        msg_label = Label(
            text=text,
            font_size=theme_manager.typography.BODY1,
            color=ColorPalette.LIGHT_ON_PRIMARY if is_outgoing else theme_manager.text_color,
            markup=False,
            size_hint_y=None,
        )
        msg_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        msg_label.bind(texture_size=lambda inst, val: self._update_message_height(message_box, msg_label))
        message_box.add_widget(msg_label)
        
        # Attachments display
        if attachments:
            for attachment in attachments:
                att_label = Label(
                    text=f'📎 {attachment.get("name", "File")}',
                    font_size=theme_manager.typography.CAPTION,
                    color=ColorPalette.LIGHT_ON_PRIMARY if is_outgoing else theme_manager.text_color,
                    size_hint_y=None,
                    height=dp(20),
                )
                message_box.add_widget(att_label)
        
        # Footer: timestamp and delivery state
        footer = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(4))
        
        footer_label = Label(
            text=f'{self.timestamp}',
            font_size=theme_manager.typography.CAPTION,
            color=ColorPalette.LIGHT_ON_PRIMARY if is_outgoing else (0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(16),
        )
        footer.add_widget(footer_label)
        
        # Delivery state icon
        if is_outgoing:
            state_icon = '✓' if delivery_state == 'sent' else ('✓✓' if delivery_state == 'read' else '⏱')
            state_label = Label(
                text=state_icon,
                font_size=theme_manager.typography.CAPTION,
                color=ColorPalette.PRIMARY if delivery_state == 'read' else (0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(16),
            )
            footer.add_widget(state_label)
        
        message_box.add_widget(footer)
        bubble_layout.add_widget(message_box)
        
        # Avatar/spacer on right for outgoing, left for incoming
        if is_outgoing:
            bubble_container.add_widget(BoxLayout())  # Spacer
        
        bubble_container.add_widget(bubble_layout)
        self.add_widget(bubble_container)
        
        # Reactions row
        if show_reactions and self.reactions:
            reactions_layout = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4), padding=[dp(12), 0])
            for reaction in self.reactions:
                reaction_chip = Label(
                    text=f'{reaction["emoji"]} {reaction.get("count", 1)}',
                    font_size=theme_manager.typography.CAPTION,
                    size_hint_y=None,
                    height=dp(24),
                    color=theme_manager.text_color,
                )
                reactions_layout.add_widget(reaction_chip)
            
            # Add reaction button
            if on_menu:
                add_reaction_btn = Button(
                    text='➕',
                    size_hint_x=None,
                    width=dp(30),
                    size_hint_y=None,
                    height=dp(24),
                    on_release=lambda: on_menu('react', self),
                )
                reactions_layout.add_widget(add_reaction_btn)
            
            self.add_widget(reactions_layout)
        
        # Message action menu button
        if on_menu:
            menu_btn = Button(
                text='⋮',
                size_hint_x=None,
                width=dp(40),
                size_hint_y=None,
                height=dp(32),
                on_release=lambda: on_menu('menu', self),
            )
            self.add_widget(menu_btn)
        
        # Calculate height
        self.bind(minimum_height=self.setter('height'))
        self._update_message_height(message_box, msg_label)
    
    def _update_bubble_rect(self, instance, value):
        """Update bubble background rectangle position and size."""
        self.bubble_rect.pos = instance.pos
        self.bubble_rect.size = instance.size
    
    def _update_message_height(self, message_box, msg_label):
        """Update message box height based on text wrapping."""
        if msg_label.texture_size[0] > 0:
            message_box.height = msg_label.texture_size[1] + dp(24)


class TypingIndicator(BoxLayout):
    """Animated typing indicator showing user is typing."""
    
    def __init__(self, username='Someone', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = dp(12)
        
        label = Label(
            text=f'{username} is typing',
            font_size=theme_manager.typography.BODY2,
            color=theme_manager.text_color,
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        # Animated dots (simple version - static)
        dots = Label(
            text='●●●',
            font_size=theme_manager.typography.BODY2,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_x=None,
            width=dp(40),
        )
        
        self.add_widget(label)
        self.add_widget(dots)


class PinnedMessageBanner(BoxLayout):
    """Banner showing pinned message in conversation."""
    
    def __init__(self, message_text='', on_close=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.padding = dp(12)
        self.spacing = dp(12)
        
        with self.canvas.before:
            self.bg_color = Color(rgba=theme_manager.primary_color + (0.1,))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        label = Label(
            text=f'📌 Pinned: {message_text[:40]}...' if len(message_text) > 40 else f'📌 Pinned: {message_text}',
            font_size=theme_manager.typography.BODY2,
            color=theme_manager.text_color,
            halign='left',
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        close_btn = Button(
            text='✕',
            size_hint_x=None,
            width=dp(40),
            on_release=on_close if on_close else lambda: None,
        )
        
        self.add_widget(label)
        self.add_widget(close_btn)
    
    def _update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class MessageActionMenu(Popup):
    """Context menu for message actions (pin, react, forward, delete)."""
    
    def __init__(self, message=None, on_pin=None, on_react=None, on_forward=None, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Message Actions'
        self.size_hint = (0.6, 0.4)
        
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        buttons = [
            ('📌 Pin', on_pin),
            ('😊 React', on_react),
            ('↗️ Forward', on_forward),
            ('🗑️ Delete', on_delete),
        ]
        
        for btn_text, callback in buttons:
            btn = Button(
                text=btn_text,
                size_hint_y=None,
                height=dp(48),
                on_release=lambda x, cb=callback: (cb(message) if cb else None, self.dismiss()),
            )
            content.add_widget(btn)
        
        self.content = content


class MessageComposer(BoxLayout):
    """Input area for composing messages with send, attach, and disappearing message toggle."""
    
    def __init__(self, on_send=None, on_attach=None, on_disappearing=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = dp(12)
        self.spacing = dp(8)
        
        with self.canvas.before:
            self.bg_color = Color(rgba=theme_manager.surface_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        theme_manager.bind(surface_color=self._update_bg_color)
        
        # Attach button
        attach_btn = Button(
            text='📎',
            size_hint_x=None,
            width=dp(40),
            on_release=lambda x: on_attach() if on_attach else None,
        )
        self.add_widget(attach_btn)
        
        # Message input
        self.message_input = TextInput(
            hint_text='Type a message...',
            multiline=True,
            size_hint_y=None,
            height=dp(40),
            font_size=theme_manager.typography.BODY1,
        )
        self.add_widget(self.message_input)
        
        # Disappearing message toggle
        self.disappearing_btn = Button(
            text='⏰',
            size_hint_x=None,
            width=dp(40),
            on_release=lambda x: on_disappearing() if on_disappearing else None,
        )
        self.add_widget(self.disappearing_btn)
        
        # Send button
        send_btn = Button(
            text='Send',
            size_hint_x=None,
            width=dp(60),
            on_release=lambda x: (on_send(self.message_input.text) if on_send else None, 
                                   setattr(self.message_input, 'text', '')),
        )
        self.add_widget(send_btn)
    
    def _update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _update_bg_color(self, instance, value):
        self.bg_color.rgba = value


class MessageSearchBar(BoxLayout):
    """Inline message search with filtering and navigation."""
    
    def __init__(self, on_search=None, on_navigate=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = dp(12)
        self.spacing = dp(8)
        
        # Search input
        self.search_input = TextInput(
            hint_text='Search messages...',
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
        self.add_widget(self.search_input)
        
        # Navigation buttons
        prev_btn = Button(
            text='◀',
            size_hint_x=None,
            width=dp(40),
            on_release=lambda x: on_navigate('prev') if on_navigate else None,
        )
        self.add_widget(prev_btn)
        
        next_btn = Button(
            text='▶',
            size_hint_x=None,
            width=dp(40),
            on_release=lambda x: on_navigate('next') if on_navigate else None,
        )
        self.add_widget(next_btn)
        
        # Expand button to open full search
        expand_btn = Button(
            text='⛶',
            size_hint_x=None,
            width=dp(40),
            on_release=lambda x: on_search(self.search_input.text) if on_search else None,
        )
        self.add_widget(expand_btn)


class ConversationListItem(BoxLayout):
    """List item for conversation preview in master view."""
    
    def __init__(self, conversation_id, name='', last_message='', timestamp='', unread_count=0, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = dp(12)
        self.spacing = dp(4)
        
        self.conversation_id = conversation_id
        self.on_select = on_select
        
        with self.canvas.before:
            self.bg_color = Color(rgba=theme_manager.surface_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Enable touch input
        self.register_event_type('on_touch_down')
        
        # Header: name + timestamp
        header = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(8))
        
        name_label = Label(
            text=name,
            font_size=theme_manager.typography.BODY1,
            color=theme_manager.text_color,
            halign='left',
        )
        name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        time_label = Label(
            text=timestamp,
            font_size=theme_manager.typography.CAPTION,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_x=None,
            width=dp(60),
        )
        
        header.add_widget(name_label)
        header.add_widget(time_label)
        
        # Message preview + unread badge
        msg_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
        
        msg_label = Label(
            text=last_message,
            font_size=theme_manager.typography.BODY2,
            color=(0.5, 0.5, 0.5, 1),
            halign='left',
        )
        msg_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        if unread_count > 0:
            badge = Label(
                text=str(unread_count),
                font_size=theme_manager.typography.CAPTION,
                color=ColorPalette.LIGHT_ON_PRIMARY,
                size_hint_x=None,
                width=dp(24),
                height=dp(24),
            )
            with badge.canvas.before:
                Color(rgba=theme_manager.primary_color)
                Rectangle(pos=badge.pos, size=badge.size)
            msg_row.add_widget(msg_label)
            msg_row.add_widget(badge)
        else:
            msg_row.add_widget(msg_label)
        
        self.add_widget(header)
        self.add_widget(msg_row)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_select:
                self.on_select()
            return True
        return super().on_touch_down(touch)
    
    def _update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
