from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from src.services.maximum_ai_manager import maximum_ai_manager
from src.theming.theme_manager import theme_manager
from src.utils.event_bus import event_bus
from src.widgets.max_ai_widgets import MaxAIControlCard, MaxAIModeCard, MaxAIPreviewCard


class MaximumAIControlPanel(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'maximum_ai'

        root = BoxLayout(orientation='vertical')

        header = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(64),
        )
        self.title = Label(
            text='Maximum AI Control Panel',
            font_size=theme_manager.typography.H4,
            color=theme_manager.text_color,
            halign='left',
            valign='middle',
        )
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.title.setter('color'))

        refresh_btn = Button(text='Refresh Preview', size_hint_x=None, width=dp(140), on_release=lambda *_: self._force_refresh())

        header.add_widget(self.title)
        header.add_widget(BoxLayout())
        header.add_widget(refresh_btn)
        root.add_widget(header)

        self.scroll = ScrollView(do_scroll_x=False)
        self.cards = GridLayout(cols=1, spacing=dp(12), padding=[dp(20), dp(12)], size_hint_y=None)
        self.cards.bind(minimum_height=self.cards.setter('height'))
        self.scroll.add_widget(self.cards)
        root.add_widget(self.scroll)

        self.add_widget(root)

        self.control_card = MaxAIControlCard(on_update_config=maximum_ai_manager.update_config)
        self.mode_card = MaxAIModeCard()
        self.preview_card = MaxAIPreviewCard()

        for w in [self.control_card, self.mode_card, self.preview_card]:
            self.cards.add_widget(w)

        Window.bind(size=lambda *_: self._update_cols())
        self._update_cols()

        event_bus.bind(on_max_ai_state_update=self._on_state)
        Clock.schedule_once(lambda dt: self._bootstrap_initial_state(), 0)

    def _bootstrap_initial_state(self):
        self._on_state(self, maximum_ai_manager.get_state())

    def _update_cols(self):
        width, _ = Window.size
        self.cards.cols = 1 if width < dp(900) else 2

    def _force_refresh(self):
        maximum_ai_manager.force_refresh_preview()

    @mainthread
    def _on_state(self, instance, state):
        self.control_card.apply_state(state)
        self.mode_card.apply_state(state)
        self.preview_card.apply_state(state)
