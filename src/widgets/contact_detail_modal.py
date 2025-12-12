from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from src.theming.theme_manager import theme_manager
from src.services.contact_service import contact_service
from src.utils.event_bus import event_bus


class ContactDetailModal(Popup):
    def __init__(self, contact_id: str, contact: dict, **kwargs):
        super().__init__(**kwargs)
        self.contact_id = contact_id
        self.contact = contact
        self.title = 'Contact Details'
        self.size_hint = (0.95, 0.95)

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # Header with close button
        header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        title_label = Label(
            text=contact.get('nickname') or contact.get('name', 'Unknown'),
            font_size=theme_manager.typography.H5,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        title_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=title_label.setter('color'))
        header.add_widget(title_label)
        header.add_widget(BoxLayout())  # Spacer
        close_btn = Button(text='×', size_hint_x=None, width=dp(44), font_size=dp(32))
        close_btn.bind(on_press=self.dismiss)
        header.add_widget(close_btn)
        root.add_widget(header)

        # Scrollable content
        scroll = ScrollView(do_scroll_x=False)
        content = GridLayout(cols=1, spacing=dp(12), padding=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Onion Address
        onion_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), spacing=dp(4))
        onion_label = Label(text='Onion Address:', font_size=theme_manager.typography.SUBTITLE2, color=theme_manager.text_color, halign='left', valign='middle', size_hint_y=None, height=dp(24))
        onion_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=onion_label.setter('color'))
        onion_value = Label(text=contact.get('onion_address', '')[:40], font_size=theme_manager.typography.CAPTION, color=theme_manager.text_color, halign='left', valign='middle', size_hint_y=None, height=dp(24), opacity=0.7)
        onion_value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=onion_value.setter('color'))
        onion_section.add_widget(onion_label)
        onion_section.add_widget(onion_value)
        content.add_widget(onion_section)

        # Nickname field
        nickname_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), spacing=dp(4))
        nickname_label = Label(text='Nickname:', font_size=theme_manager.typography.SUBTITLE2, color=theme_manager.text_color, halign='left', valign='middle', size_hint_y=None, height=dp(24))
        nickname_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=nickname_label.setter('color'))
        self.nickname_input = TextInput(
            text=contact.get('nickname', ''),
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            background_color=theme_manager.surface_color,
        )
        nickname_section.add_widget(nickname_label)
        nickname_section.add_widget(self.nickname_input)
        content.add_widget(nickname_section)

        # Actions section
        actions_label = Label(text='Actions:', font_size=theme_manager.typography.SUBTITLE2, color=theme_manager.text_color, halign='left', valign='middle', size_hint_y=None, height=dp(24))
        actions_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=actions_label.setter('color'))
        content.add_widget(actions_label)

        # Action buttons
        actions_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(100))

        # Favorite button
        favorite_text = '★ Remove Favorite' if contact_service.is_favorite(contact_id) else '☆ Add Favorite'
        fav_btn = Button(text=favorite_text)
        fav_btn.bind(on_press=lambda *_: self._toggle_favorite())
        actions_grid.add_widget(fav_btn)

        # Block button
        block_text = '🚫 Unblock' if contact_service.is_blocked(contact_id) else '🚫 Block'
        self.block_btn = Button(text=block_text)
        self.block_btn.bind(on_press=lambda *_: self._toggle_block())
        actions_grid.add_widget(self.block_btn)

        # Report button
        report_btn = Button(text='⚠ Report Malicious')
        report_btn.bind(on_press=lambda *_: self._report_contact())
        actions_grid.add_widget(report_btn)

        # Share button
        share_btn = Button(text='📤 Share Contact')
        share_btn.bind(on_press=lambda *_: self._share_contact())
        actions_grid.add_widget(share_btn)

        # Mute button
        mute_text = '🔇 Unmute' if contact_service.is_muted(contact_id) else '🔇 Mute'
        self.mute_btn = Button(text=mute_text)
        self.mute_btn.bind(on_press=lambda *_: self._toggle_mute())
        actions_grid.add_widget(self.mute_btn)

        # Fingerprint button
        fingerprint_btn = Button(text='🔐 Verify')
        fingerprint_btn.bind(on_press=lambda *_: self._show_fingerprint())
        actions_grid.add_widget(fingerprint_btn)

        content.add_widget(actions_grid)

        # Verification status
        fingerprint_data = contact_service.get_verification_fingerprint(contact_id)
        if fingerprint_data:
            verify_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(4))
            verify_label = Label(
                text='Verification Fingerprint:',
                font_size=theme_manager.typography.SUBTITLE2,
                color=theme_manager.text_color,
                halign='left',
                valign='middle',
                size_hint_y=None,
                height=dp(24),
            )
            verify_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            theme_manager.bind(text_color=verify_label.setter('color'))
            
            fingerprint_display = Label(
                text=fingerprint_data.get('fingerprint', '')[:32] + '...',
                font_size=theme_manager.typography.CAPTION,
                color=theme_manager.text_color,
                halign='left',
                valign='middle',
                opacity=0.7,
                size_hint_y=None,
                height=dp(24),
            )
            fingerprint_display.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            theme_manager.bind(text_color=fingerprint_display.setter('color'))
            
            verify_section.add_widget(verify_label)
            verify_section.add_widget(fingerprint_display)
            content.add_widget(verify_section)

        # Save button
        save_btn = Button(text='Save Changes', size_hint_y=None, height=dp(44))
        save_btn.bind(on_press=lambda *_: self._save_changes())
        content.add_widget(save_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.content = root

    def _toggle_favorite(self):
        if contact_service.is_favorite(self.contact_id):
            contact_service.remove_from_favorite(self.contact_id)
        else:
            contact_service.add_to_favorite(self.contact_id)

    def _toggle_block(self):
        if contact_service.is_blocked(self.contact_id):
            contact_service.unblock_contact(self.contact_id)
            self.block_btn.text = '🚫 Block'
        else:
            contact_service.block_contact(self.contact_id)
            self.block_btn.text = '🚫 Unblock'

    def _toggle_mute(self):
        if contact_service.is_muted(self.contact_id):
            contact_service.unmute_contact(self.contact_id)
            self.mute_btn.text = '🔇 Mute'
        else:
            contact_service.mute_contact(self.contact_id)
            self.mute_btn.text = '🔇 Unmute'

    def _report_contact(self):
        # Create a modal for reporting
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        label = Label(text='Report Reason:', size_hint_y=None, height=dp(24), color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(label)

        reason_input = TextInput(multiline=True, size_hint_y=None, height=dp(100))
        content.add_widget(reason_input)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        close_btn = Button(text='Cancel')
        submit_btn = Button(text='Submit Report')
        button_box.add_widget(close_btn)
        button_box.add_widget(submit_btn)
        content.add_widget(button_box)

        modal = Popup(title='Report Contact', content=content, size_hint=(0.9, 0.6))
        close_btn.bind(on_press=modal.dismiss)
        submit_btn.bind(on_press=lambda *_: self._submit_report(reason_input.text, modal))
        modal.open()

    def _submit_report(self, reason: str, modal: Popup):
        # In a real implementation, this would send the report to the server
        print(f"Report submitted for {self.contact_id}: {reason}")
        modal.dismiss()

    def _share_contact(self):
        # Generate QR code and show it
        print(f"Share contact: {self.contact_id}")

    def _show_fingerprint(self):
        fingerprint_data = contact_service.get_verification_fingerprint(self.contact_id)
        
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        title = Label(
            text='Verification Fingerprint',
            font_size=theme_manager.typography.H6,
            size_hint_y=None,
            height=dp(40),
            color=theme_manager.text_color,
        )
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(title)

        if fingerprint_data:
            fingerprint_text = fingerprint_data.get('fingerprint', 'Not set')
            is_verified = fingerprint_data.get('verified', False)
        else:
            fingerprint_text = 'Not yet verified'
            is_verified = False

        fp_label = Label(
            text=fingerprint_text,
            font_size=theme_manager.typography.BODY2,
            size_hint_y=None,
            height=dp(80),
            color=theme_manager.text_color,
            valign='top',
            markup=True,
        )
        fp_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(fp_label)

        verification_status = Label(
            text=f"Verified: {'Yes ✓' if is_verified else 'No'}",
            font_size=theme_manager.typography.SUBTITLE2,
            size_hint_y=None,
            height=dp(24),
            color=theme_manager.text_color,
        )
        verification_status.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(verification_status)

        # Verification checklist
        checklist_label = Label(
            text='Verification Checklist:',
            font_size=theme_manager.typography.SUBTITLE2,
            size_hint_y=None,
            height=dp(24),
            color=theme_manager.text_color,
        )
        checklist_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(checklist_label)

        checklist = Label(
            text='☐ Compare fingerprint through verified channel\n☐ Confirm via phone call or video\n☐ Mark as verified once confirmed',
            font_size=theme_manager.typography.BODY2,
            size_hint_y=None,
            height=dp(80),
            color=theme_manager.text_color,
            valign='top',
        )
        checklist.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(checklist)

        button_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        close_btn = Button(text='Close')
        mark_verified_btn = Button(text='Mark as Verified' if not is_verified else 'Mark as Unverified')
        button_box.add_widget(close_btn)
        button_box.add_widget(mark_verified_btn)
        content.add_widget(button_box)

        modal = Popup(title='Verify Fingerprint', content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=modal.dismiss)
        mark_verified_btn.bind(on_press=lambda *_: self._toggle_verified(modal))
        modal.open()

    def _toggle_verified(self, modal: Popup):
        fingerprint_data = contact_service.get_verification_fingerprint(self.contact_id)
        is_verified = fingerprint_data.get('verified', False) if fingerprint_data else False
        
        # For now, generate a mock fingerprint
        if not fingerprint_data:
            mock_fp = 'ABCD1234EFGH5678IJKL9012MNOP3456'
            contact_service.set_verification_fingerprint(self.contact_id, mock_fp, not is_verified)
        else:
            contact_service.set_verification_fingerprint(
                self.contact_id,
                fingerprint_data.get('fingerprint', ''),
                not is_verified
            )
        modal.dismiss()

    def _save_changes(self):
        contact_service.set_nickname(self.contact_id, self.nickname_input.text)
        self.dismiss()
