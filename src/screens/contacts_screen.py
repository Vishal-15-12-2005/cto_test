from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.image import Image
import json

from src.services.contact_service import contact_service
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.contact_list import ContactList
from src.widgets.contact_detail_modal import ContactDetailModal


class ContactsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'contacts'
        self._current_sort = 'alphabetical'
        self._current_group = None
        self._search_query = ''

        root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(orientation='horizontal', padding=[dp(20), dp(16)], spacing=dp(12), size_hint_y=None, height=dp(64))
        self.title = Label(
            text='Contacts',
            font_size=theme_manager.typography.H4,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))

        header.add_widget(self.title)
        header.add_widget(BoxLayout())  # Spacer

        add_btn = Button(text='+ Add', size_hint_x=None, width=dp(100))
        add_btn.bind(on_press=lambda *_: self._show_add_contact_menu())
        header.add_widget(add_btn)

        root.add_widget(header)

        # Search bar
        search_box = BoxLayout(padding=dp(12), spacing=dp(8), size_hint_y=None, height=dp(44))
        self.search_input = TextInput(
            hint_text='Search contacts...',
            multiline=False,
            size_hint_x=0.8,
        )
        self.search_input.bind(text=lambda inst, val: self._on_search(val))
        search_box.add_widget(self.search_input)

        search_btn = Button(text='🔍', size_hint_x=None, width=dp(44))
        search_btn.bind(on_press=lambda *_: self._refresh_contacts())
        search_box.add_widget(search_btn)

        root.add_widget(search_box)

        # Sorting/grouping tabs
        self.tabs = TabbedPanel(size_hint_y=None, height=dp(40))
        self.tabs.do_default_tab = False

        all_tab = TabbedPanelItem(text='All')
        all_tab.bind(on_press=lambda *_: self._set_view('all', None))
        self.tabs.add_widget(all_tab)

        favorites_tab = TabbedPanelItem(text='★ Favorites')
        favorites_tab.bind(on_press=lambda *_: self._set_view('favorites', None))
        self.tabs.add_widget(favorites_tab)

        recent_tab = TabbedPanelItem(text='Recent')
        recent_tab.bind(on_press=lambda *_: self._set_view('recent', None))
        self.tabs.add_widget(recent_tab)

        pending_tab = TabbedPanelItem(text='Pending')
        pending_tab.bind(on_press=lambda *_: self._set_view('pending', None))
        self.tabs.add_widget(pending_tab)

        blocked_tab = TabbedPanelItem(text='🚫 Blocked')
        blocked_tab.bind(on_press=lambda *_: self._set_view('blocked', None))
        self.tabs.add_widget(blocked_tab)

        # Set default tab
        self.tabs.default_tab = all_tab
        self.tabs.default_tab_content = None
        self.current_tab = 'all'

        root.add_widget(self.tabs)

        # Contact list
        self.scroll = ScrollView(do_scroll_x=False)
        self.contact_list = ContactList(on_select=self._on_contact_selected)
        self.scroll.add_widget(self.contact_list)
        root.add_widget(self.scroll)

        self.add_widget(root)

        # Event bindings
        event_bus.bind(on_contact_added=self._on_contact_added)
        event_bus.bind(on_contact_deleted=self._on_contact_deleted)
        event_bus.bind(on_contact_updated=self._on_contact_updated)
        event_bus.bind(on_contacts_updated=self._on_contacts_updated)
        event_bus.bind(on_contact_favorited=self._on_contact_favorited)
        event_bus.bind(on_contact_blocked=self._on_contact_blocked)
        event_bus.bind(on_contact_muted=self._on_contact_muted)
        event_bus.bind(on_contact_presence_updated=self._on_presence_updated)

        Window.bind(size=lambda *_: self._update_cols())
        self._update_cols()

        Clock.schedule_once(lambda dt: self._refresh_contacts(), 0)

    def _update_cols(self):
        width, _ = Window.size
        # This is mainly for consistency, but since we're using a single column list,
        # we might not need dynamic columns here

    def _refresh_contacts(self):
        self._load_contacts_for_current_view()

    def _on_search(self, query):
        self._search_query = query
        self._load_contacts_for_current_view()

    def _load_contacts_for_current_view(self):
        if self.current_tab == 'all':
            if self._search_query:
                contacts = contact_service.search_contacts(self._search_query)
            else:
                contacts = contact_service.get_sorted_contacts('alphabetical')
        elif self.current_tab == 'favorites':
            contacts = contact_service.get_favorites()
            if self._search_query:
                contacts = {cid: c for cid, c in contacts.items() if self._search_query.lower() in c.get('name', '').lower()}
        elif self.current_tab == 'recent':
            contacts = contact_service.get_sorted_contacts('recent')
            if self._search_query:
                contacts = {cid: c for cid, c in contacts.items() if self._search_query.lower() in c.get('name', '').lower()}
        elif self.current_tab == 'pending':
            contacts = {}
            pending = contact_service.get_pending_requests()
            for req_id, req in pending.items():
                from_id = req.get('from_id', '')
                if from_id and from_id != 'self':
                    contact = contact_service.get_contact(from_id)
                    if contact:
                        contacts[from_id] = contact
        elif self.current_tab == 'blocked':
            contacts = contact_service.get_blocked_contacts()
            if self._search_query:
                contacts = {cid: c for cid, c in contacts.items() if self._search_query.lower() in c.get('name', '').lower()}
        else:
            contacts = {}

        self.contact_list.set_contacts(contacts)

    def _set_view(self, tab_name, group=None):
        self.current_tab = tab_name
        self._current_group = group
        self._load_contacts_for_current_view()

    @mainthread
    def _on_contact_selected(self, contact_id: str, contact: dict):
        modal = ContactDetailModal(contact_id, contact)
        modal.open()

    @mainthread
    def _on_contact_added(self, instance, contact_id, contact):
        if self.current_tab in ['all', 'alphabetical']:
            self.contact_list.add_contact(contact_id, contact)

    @mainthread
    def _on_contact_deleted(self, instance, contact_id):
        self.contact_list.remove_contact(contact_id)

    @mainthread
    def _on_contact_updated(self, instance, contact_id, contact):
        self.contact_list.update_contact(contact_id, contact)

    @mainthread
    def _on_contacts_updated(self, instance):
        self._load_contacts_for_current_view()

    @mainthread
    def _on_contact_favorited(self, instance, contact_id, is_favorite):
        self._load_contacts_for_current_view()

    @mainthread
    def _on_contact_blocked(self, instance, contact_id, is_blocked):
        self._load_contacts_for_current_view()

    @mainthread
    def _on_contact_muted(self, instance, contact_id, is_muted):
        self._load_contacts_for_current_view()

    @mainthread
    def _on_presence_updated(self, instance, contact_id, status):
        contact = contact_service.get_contact(contact_id)
        if contact:
            self.contact_list.update_contact(contact_id, contact)

    def _show_add_contact_menu(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        manual_btn = Button(text='Add Manually', size_hint_y=None, height=dp(44))
        manual_btn.bind(on_press=lambda *_: self._show_add_manual_modal())
        content.add_widget(manual_btn)

        qr_scan_btn = Button(text='Scan QR Code', size_hint_y=None, height=dp(44))
        qr_scan_btn.bind(on_press=lambda *_: self._show_qr_scanner())
        content.add_widget(qr_scan_btn)

        qr_gen_btn = Button(text='Generate My QR Code', size_hint_y=None, height=dp(44))
        qr_gen_btn.bind(on_press=lambda *_: self._show_my_qr())
        content.add_widget(qr_gen_btn)

        import_btn = Button(text='Import Contact File', size_hint_y=None, height=dp(44))
        import_btn.bind(on_press=lambda *_: self._show_import_dialog())
        content.add_widget(import_btn)

        backup_btn = Button(text='Backup/Restore', size_hint_y=None, height=dp(44))
        backup_btn.bind(on_press=lambda *_: self._show_backup_menu())
        content.add_widget(backup_btn)

        close_btn = Button(text='Close', size_hint_y=None, height=dp(44))
        close_btn.bind(on_press=lambda modal: modal.dismiss())
        content.add_widget(close_btn)

        modal = Popup(title='Add Contact', content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=modal.dismiss)
        modal.open()

    def _show_add_manual_modal(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        name_label = Label(text='Name:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(name_label)

        name_input = TextInput(multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(name_input)

        onion_label = Label(text='Onion Address:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        onion_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(onion_label)

        onion_input = TextInput(multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(onion_input)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel_btn = Button(text='Cancel')
        add_btn = Button(text='Add Contact')
        button_box.add_widget(cancel_btn)
        button_box.add_widget(add_btn)
        content.add_widget(button_box)

        modal = Popup(title='Add Contact Manually', content=content, size_hint=(0.9, 0.6))
        
        def add_contact(*args):
            name = name_input.text.strip()
            onion = onion_input.text.strip()
            if name and onion:
                contact_id = onion.replace('.onion', '')
                contact_service.add_contact(contact_id, name, onion)
                modal.dismiss()

        cancel_btn.bind(on_press=modal.dismiss)
        add_btn.bind(on_press=add_contact)
        modal.open()

    def _show_qr_scanner(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        instruction = Label(
            text='Scanning QR codes requires a camera.\nFor desktop, you can import a QR JSON file instead.',
            size_hint_y=None,
            height=dp(60),
            color=theme_manager.text_color,
        )
        instruction.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(instruction)

        # Simulated QR scan input
        label = Label(text='Paste QR Data:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        qr_input = TextInput(multiline=True, size_hint_y=None, height=dp(100))
        content.add_widget(qr_input)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel_btn = Button(text='Cancel')
        import_btn = Button(text='Import')
        button_box.add_widget(cancel_btn)
        button_box.add_widget(import_btn)
        content.add_widget(button_box)

        modal = Popup(title='Scan QR Code', content=content, size_hint=(0.9, 0.6))

        def import_qr(*args):
            try:
                payload = json.loads(qr_input.text)
                contact_service.import_contact_from_qr(payload)
                modal.dismiss()
            except Exception as e:
                print(f"Error importing QR: {e}")

        cancel_btn.bind(on_press=modal.dismiss)
        import_btn.bind(on_press=import_qr)
        modal.open()

    def _show_my_qr(self):
        # Get the user's onion address (would come from tor_manager in a real app)
        # For now, use a mock address
        mock_onion = 'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl.onion'

        qr_img = contact_service.generate_qr_code(mock_onion, 'Me')

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        label = Label(
            text='Your Contact QR Code:',
            size_hint_y=None,
            height=dp(24),
            color=theme_manager.text_color,
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        img = Image(source_from_bytesio(qr_img), size_hint=(1, 0.7))
        content.add_widget(img)

        export_box = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(8))
        copy_btn = Button(text='Copy Address')
        save_btn = Button(text='Save QR Code')
        close_btn = Button(text='Close')
        export_box.add_widget(copy_btn)
        export_box.add_widget(save_btn)
        export_box.add_widget(close_btn)
        content.add_widget(export_box)

        modal = Popup(title='My QR Code', content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=modal.dismiss)
        modal.open()

    def _show_import_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        label = Label(text='Select contact file to import:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        # File chooser simulation
        file_input = TextInput(hint_text='Enter file path or paste JSON...', multiline=True, size_hint_y=0.7)
        content.add_widget(file_input)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel_btn = Button(text='Cancel')
        import_btn = Button(text='Import')
        button_box.add_widget(cancel_btn)
        button_box.add_widget(import_btn)
        content.add_widget(button_box)

        modal = Popup(title='Import Contact File', content=content, size_hint=(0.9, 0.7))

        def import_file(*args):
            try:
                payload = json.loads(file_input.text)
                contact_service.import_contact_from_qr(payload)
                modal.dismiss()
            except Exception as e:
                print(f"Error importing file: {e}")

        cancel_btn.bind(on_press=modal.dismiss)
        import_btn.bind(on_press=import_file)
        modal.open()

    def _show_backup_menu(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        export_btn = Button(text='Export Backup', size_hint_y=None, height=dp(44))
        export_btn.bind(on_press=lambda *_: self._export_backup())
        content.add_widget(export_btn)

        import_btn = Button(text='Import Backup', size_hint_y=None, height=dp(44))
        import_btn.bind(on_press=lambda *_: self._import_backup())
        content.add_widget(import_btn)

        close_btn = Button(text='Close', size_hint_y=None, height=dp(44))
        close_btn.bind(on_press=lambda modal: modal.dismiss())
        content.add_widget(close_btn)

        modal = Popup(title='Backup/Restore', content=content, size_hint=(0.9, 0.5))
        close_btn.bind(on_press=modal.dismiss)
        modal.open()

    def _export_backup(self):
        backup_data = contact_service.export_backup()
        
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        label = Label(text='Encrypted Backup Data:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        backup_display = TextInput(text=backup_data, multiline=True, readonly=True, size_hint_y=0.7)
        content.add_widget(backup_display)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        copy_btn = Button(text='Copy')
        close_btn = Button(text='Close')
        button_box.add_widget(copy_btn)
        button_box.add_widget(close_btn)
        content.add_widget(button_box)

        modal = Popup(title='Export Backup', content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=modal.dismiss)
        modal.open()

    def _import_backup(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        label = Label(text='Paste encrypted backup data:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        backup_input = TextInput(multiline=True, size_hint_y=0.7)
        content.add_widget(backup_input)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel_btn = Button(text='Cancel')
        import_btn = Button(text='Import')
        button_box.add_widget(cancel_btn)
        button_box.add_widget(import_btn)
        content.add_widget(button_box)

        modal = Popup(title='Import Backup', content=content, size_hint=(0.9, 0.7))

        def import_backup(*args):
            if contact_service.import_backup(backup_input.text):
                self._load_contacts_for_current_view()
                modal.dismiss()

        cancel_btn.bind(on_press=modal.dismiss)
        import_btn.bind(on_press=import_backup)
        modal.open()


def source_from_bytesio(bio):
    """Convert BytesIO to a source that Kivy Image can use."""
    # This is a helper function to display QR codes
    # In a real implementation, we'd save to a temp file or use base64
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(bio.getvalue())
        return f.name
