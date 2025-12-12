from __future__ import annotations

import time
from typing import Any, Callable, Dict, List

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch

from src.services.deep_learning_agent import deep_learning_agent
from src.theming.theme_manager import theme_manager
from src.widgets.cards import Card


class MaxAIModeCard(Card):
    def __init__(self, **kwargs):
        body = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.mode_label = Label(text='Mode: —', halign='left', valign='middle', color=theme_manager.text_color)
        self.mode_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.mode_label.setter('color'))

        self.status_label = Label(text='—', halign='left', valign='top', color=theme_manager.text_color)
        self.status_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.status_label.setter('color'))

        self.reason_label = Label(
            text='—',
            halign='left',
            valign='top',
            color=theme_manager.text_color,
            font_size=theme_manager.typography.CAPTION,
        )
        self.reason_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.reason_label.setter('color'))

        self.impact_label = Label(
            text='—',
            halign='left',
            valign='top',
            color=theme_manager.text_color,
            font_size=theme_manager.typography.CAPTION,
        )
        self.impact_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.impact_label.setter('color'))

        body.add_widget(self.mode_label)
        body.add_widget(self.status_label)
        body.add_widget(self.reason_label)
        body.add_widget(self.impact_label)

        super().__init__(title='Maximum AI', body=body, **kwargs)

        self._last_version = -1

    def apply_state(self, state: Dict[str, Any]):
        v = int(state.get('state_version', 0))
        if v < self._last_version:
            return
        self._last_version = v

        enabled = bool(state.get('enabled', False))
        mode = state.get('current_mode', 'standard')
        self.mode_label.text = f"Mode: {mode.title()}" + ('' if enabled else ' (disabled)')
        self.status_label.text = state.get('status_text', '—')
        self.reason_label.text = state.get('transition_reason', '—')
        self.impact_label.text = state.get('impact_warning', '—')


class MaxAIControlCard(Card):
    def __init__(self, *, on_update_config: Callable[..., None], **kwargs):
        self._on_update_config = on_update_config
        self._updating = False
        self._pending_complexity_event = None

        body = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.enabled_switch = Switch(active=False)
        self.enabled_switch.bind(active=self._handle_enabled)
        body.add_widget(self._row('Enable Maximum AI', self.enabled_switch))

        self.human_like_switch = Switch(active=True)
        self.human_like_switch.bind(active=self._handle_human_like)
        body.add_widget(self._row('Human-like synthesis', self.human_like_switch))

        self.always_on_switch = Switch(active=False)
        self.always_on_switch.bind(active=self._handle_always_on)
        body.add_widget(self._row('Always-On background', self.always_on_switch))

        self.pattern_spinner = Spinner(text='Adaptive', values=tuple(deep_learning_agent.PATTERN_TYPES))
        self.pattern_spinner.bind(text=self._handle_pattern)
        body.add_widget(self._row('Pattern type', self.pattern_spinner))

        complexity_wrap = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        complexity_wrap.bind(minimum_height=complexity_wrap.setter('height'))

        complexity_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        self.complexity_value = Label(
            text='35',
            size_hint_x=None,
            width=dp(46),
            halign='right',
            valign='middle',
            color=theme_manager.text_color,
        )
        self.complexity_value.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.complexity_value.setter('color'))

        self.complexity_slider = Slider(min=0, max=100, value=35, step=1)
        self.complexity_slider.bind(value=self._handle_complexity)

        complexity_label = Label(text='Complexity', halign='left', valign='middle', color=theme_manager.text_color)
        complexity_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=complexity_label.setter('color'))

        complexity_row.add_widget(complexity_label)
        complexity_row.add_widget(BoxLayout())
        complexity_row.add_widget(self.complexity_value)

        complexity_wrap.add_widget(complexity_row)
        complexity_wrap.add_widget(self.complexity_slider)

        self.warning_label = Label(
            text='Low impact: minimal background activity.',
            halign='left',
            valign='top',
            color=theme_manager.text_color,
            font_size=theme_manager.typography.CAPTION,
        )
        self.warning_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.warning_label.setter('color'))

        complexity_wrap.add_widget(self.warning_label)
        body.add_widget(complexity_wrap)

        self.status_label = Label(text='Disabled.', halign='left', valign='top', color=theme_manager.text_color)
        self.status_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.status_label.setter('color'))
        body.add_widget(self.status_label)

        super().__init__(title='Controls', body=body, **kwargs)

        self._last_version = -1

    def _row(self, label_text: str, widget):
        row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(34))
        label = Label(text=label_text, halign='left', valign='middle', color=theme_manager.text_color)
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=label.setter('color'))

        row.add_widget(label)
        row.add_widget(BoxLayout())
        row.add_widget(widget)
        return row

    def _handle_enabled(self, instance, enabled: bool):
        if self._updating:
            return
        self._on_update_config(enabled=bool(enabled))

    def _handle_human_like(self, instance, enabled: bool):
        if self._updating:
            return
        self._on_update_config(human_like_synthesis=bool(enabled))

    def _handle_always_on(self, instance, enabled: bool):
        if self._updating:
            return
        self._on_update_config(always_on_background=bool(enabled))

    def _handle_pattern(self, instance, value: str):
        if self._updating:
            return
        self._on_update_config(pattern_type=value)

    def _handle_complexity(self, instance, value: float):
        value_i = int(value)
        self.complexity_value.text = str(value_i)
        if self._updating:
            return

        if self._pending_complexity_event is not None:
            self._pending_complexity_event.cancel()
        self._pending_complexity_event = Clock.schedule_once(lambda dt: self._commit_complexity(value_i), 0.15)

    def _commit_complexity(self, value_i: int):
        self._pending_complexity_event = None
        self._on_update_config(complexity=value_i)

    def apply_state(self, state: Dict[str, Any]):
        v = int(state.get('state_version', 0))
        if v < self._last_version:
            return
        self._last_version = v

        self._updating = True
        try:
            self.enabled_switch.active = bool(state.get('enabled', False))
            self.human_like_switch.active = bool(state.get('human_like_synthesis', True))
            self.always_on_switch.active = bool(state.get('always_on_background', False))

            pattern = state.get('pattern_type', 'Adaptive')
            if pattern in self.pattern_spinner.values:
                self.pattern_spinner.text = pattern

            complexity = int(state.get('complexity', 35))
            self.complexity_slider.value = complexity
            self.complexity_value.text = str(complexity)

            self.warning_label.text = state.get('impact_warning', '—')
            self.status_label.text = state.get('status_text', '—')
        finally:
            self._updating = False


class MaxAIPreviewCard(Card):
    def __init__(self, *, preview_slots: int = 6, **kwargs):
        body = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        self.meta_label = Label(
            text='—',
            halign='left',
            valign='top',
            color=theme_manager.text_color,
            font_size=theme_manager.typography.CAPTION,
        )
        self.meta_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        theme_manager.bind(text_color=self.meta_label.setter('color'))
        body.add_widget(self.meta_label)

        self.action_cards: List[Card] = []
        for i in range(int(preview_slots)):
            c = Card(title=f"Action {i + 1}", content='—')
            self.action_cards.append(c)
            body.add_widget(c)

        super().__init__(title='Generated Activity Preview', body=body, **kwargs)

        self._last_version = -1

    def apply_state(self, state: Dict[str, Any]):
        v = int(state.get('state_version', 0))
        if v < self._last_version:
            return
        self._last_version = v

        enabled = bool(state.get('enabled', False))
        pattern = state.get('pattern_type', '—')
        complexity = state.get('complexity', '—')

        updated_at = state.get('preview_updated_at')
        if updated_at:
            ts = time.strftime('%H:%M:%S', time.localtime(float(updated_at)))
            updated_text = f"Last refresh: {ts}"
        else:
            updated_text = 'Last refresh: —'

        if not enabled:
            self.meta_label.text = 'Enable Maximum AI to generate previews.'
        else:
            self.meta_label.text = f"Pattern: {pattern} • Complexity: {complexity} • {updated_text}"

        actions = state.get('preview_actions') or []
        for idx, card in enumerate(self.action_cards):
            text = actions[idx] if idx < len(actions) else '—'
            card.update_content(text)
