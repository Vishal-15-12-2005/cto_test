from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus


class ContactListItem(BoxLayout):
    def __init__(self, contact_id: str, contact: dict, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.contact_id = contact_id
        self.contact = contact
        self.on_select = on_select
        self.orientation = 'horizontal'
        self.padding = dp(12)
        self.spacing = dp(12)
        self.size_hint_y = None
        self.height = dp(72)

        theme_manager.bind(surface_color=self.update_bg)
        self.bind(pos=self.update_rect, size=self.update_rect)

        with self.canvas.before:
            self.bg_color_instruction = Color(rgba=theme_manager.surface_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Status indicator circle
        status_container = BoxLayout(size_hint_x=None, width=dp(12))
        self.status_indicator = BoxLayout()
        with self.status_indicator.canvas:
            status_color = self._get_status_color(contact.get('presence_status', 'offline'))
            Color(rgba=status_color)
            Rectangle(pos=self.status_indicator.pos, size=self.status_indicator.size)
        status_container.add_widget(self.status_indicator)
        self.add_widget(status_container)

        # Contact info
        info_container = BoxLayout(orientation='vertical', spacing=dp(4))

        # Name + badges
        name_row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        self.name_label = Label(
            text=contact.get('nickname') or contact.get('name', 'Unknown'),
            font_size=theme_manager.typography.BODY1,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        self.name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.name_label.setter('color'))
        name_row.add_widget(self.name_label)

        # Badges
        badge_container = BoxLayout(size_hint_x=None, width=dp(80), spacing=dp(4))
        if contact_id in [cid for cid in [] if False]:  # Placeholder for blocked/muted checks
            pass
        badge_container.add_widget(BoxLayout())  # Spacer
        name_row.add_widget(badge_container)

        info_container.add_widget(name_row)

        # Last message preview
        preview_text = contact.get('last_message_preview', '')
        if not preview_text:
            preview_text = contact.get('onion_address', '')[:20] + '...'

        self.preview_label = Label(
            text=preview_text[:40],
            font_size=theme_manager.typography.CAPTION,
            color=theme_manager.text_color,
            halign='left',
            valign='top',
            opacity=0.7,
        )
        self.preview_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.preview_label.setter('color'))
        info_container.add_widget(self.preview_label)

        self.add_widget(info_container)

        # Select button
        select_btn = Button(text='', size_hint_x=None, width=dp(44), background_color=(0, 0, 0, 0))
        select_btn.bind(on_press=lambda *_: self._on_select())
        self.add_widget(select_btn)

    def _get_status_color(self, status):
        if status == 'online':
            return (0.2, 0.9, 0.3, 1.0)  # Green
        elif status == 'connecting':
            return (1.0, 0.7, 0.0, 1.0)  # Orange
        else:
            return (0.5, 0.5, 0.5, 1.0)  # Gray

    def _on_select(self):
        if self.on_select:
            self.on_select(self.contact_id, self.contact)

    def update_bg(self, instance, value):
        self.bg_color_instruction.rgba = value

    def update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def update_contact(self, contact: dict):
        self.contact = contact
        self.name_label.text = contact.get('nickname') or contact.get('name', 'Unknown')
        self.preview_label.text = contact.get('last_message_preview', '')[:40]


class ContactList(GridLayout):
    def __init__(self, contacts: dict = None, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.spacing = 0
        self.padding = 0
        self.size_hint_y = None
        self.on_select = on_select
        self._items = {}

        self.bind(minimum_height=self.setter('height'))

        if contacts:
            self.set_contacts(contacts)

    def set_contacts(self, contacts: dict):
        self.clear_widgets()
        self._items = {}
        for contact_id, contact in contacts.items():
            item = ContactListItem(
                contact_id=contact_id,
                contact=contact,
                on_select=self.on_select,
            )
            self._items[contact_id] = item
            self.add_widget(item)

    def update_contact(self, contact_id: str, contact: dict):
        if contact_id in self._items:
            self._items[contact_id].update_contact(contact)

    def remove_contact(self, contact_id: str):
        if contact_id in self._items:
            self.remove_widget(self._items[contact_id])
            del self._items[contact_id]

    def add_contact(self, contact_id: str, contact: dict):
        if contact_id not in self._items:
            item = ContactListItem(
                contact_id=contact_id,
                contact=contact,
                on_select=self.on_select,
            )
            self._items[contact_id] = item
            self.add_widget(item)
