from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from kivy.clock import Clock

from src.services.deep_learning_agent import deep_learning_agent
from src.utils.event_bus import event_bus
from src.utils.text_sanitizer import sanitize_action_text


class MaximumAIManager:
    def __init__(self):
        self._service_running = False
        self._preview_event = None

        self._state_version = 0
        self._context_sensitive_comms_active = False
        self._context_reason = ''

        self._config = {
            'enabled': False,
            'human_like_synthesis': True,
            'pattern_type': 'Adaptive',
            'complexity': 35,
            'always_on_background': False,
        }

        self._state: Dict[str, Any] = {
            'state_version': 0,
            'enabled': False,
            'human_like_synthesis': True,
            'pattern_type': 'Adaptive',
            'complexity': 35,
            'always_on_background': False,
            'current_mode': 'standard',
            'context_sensitive_comms': False,
            'transition_reason': 'Disabled by user',
            'status_text': 'Disabled.',
            'impact_level': 'low',
            'impact_warning': 'Low impact.',
            'preview_actions': [],
            'preview_updated_at': None,
        }

        event_bus.bind(on_sensitive_comms_update=self._on_sensitive_comms)

        self._recompute_state(emit=False)

    def start_service(self):
        if self._service_running:
            return
        self._service_running = True
        self._emit_state()
        self._preview_event = Clock.schedule_interval(self._refresh_preview, 2.5)

    def stop_service(self):
        self._service_running = False
        if self._preview_event is not None:
            self._preview_event.cancel()
            self._preview_event = None

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def update_config(
        self,
        *,
        enabled: Optional[bool] = None,
        human_like_synthesis: Optional[bool] = None,
        pattern_type: Optional[str] = None,
        complexity: Optional[int] = None,
        always_on_background: Optional[bool] = None,
    ):
        if enabled is not None:
            self._config['enabled'] = bool(enabled)
        if human_like_synthesis is not None:
            self._config['human_like_synthesis'] = bool(human_like_synthesis)
        if pattern_type is not None:
            self._config['pattern_type'] = str(pattern_type)
        if complexity is not None:
            self._config['complexity'] = max(0, min(100, int(complexity)))
        if always_on_background is not None:
            self._config['always_on_background'] = bool(always_on_background)

        self._recompute_state(emit=True)

    def _on_sensitive_comms(self, instance, active: bool, reason: str = ''):
        self._context_sensitive_comms_active = bool(active)
        self._context_reason = str(reason or '')
        self._recompute_state(emit=True)

    def _recompute_state(self, *, emit: bool):
        enabled = bool(self._config['enabled'])
        always_on = bool(self._config['always_on_background'])
        sensitive = bool(self._context_sensitive_comms_active)

        if not enabled:
            current_mode = 'standard'
            transition_reason = 'Disabled by user'
        elif always_on:
            current_mode = 'maximum'
            transition_reason = 'Always-On background is enabled'
        elif sensitive:
            current_mode = 'maximum'
            transition_reason = self._context_reason or 'Context trigger: sensitive comms'
        else:
            current_mode = 'standard'
            transition_reason = 'No contextual triggers'

        if enabled and current_mode == 'maximum' and self._config['human_like_synthesis']:
            status_text = 'Simulating human-like activity…'
        elif enabled and current_mode == 'maximum':
            status_text = 'Simulating activity…'
        elif enabled:
            status_text = 'Standing by (Standard mode).'
        else:
            status_text = 'Disabled.'

        impact_level, impact_warning = self._impact_warning(
            complexity=int(self._config['complexity']),
            always_on=always_on,
        )

        self._update_state(
            {
                **self._config,
                'current_mode': current_mode,
                'context_sensitive_comms': sensitive,
                'transition_reason': transition_reason,
                'status_text': status_text,
                'impact_level': impact_level,
                'impact_warning': impact_warning,
            },
            emit=emit,
        )

    def _impact_warning(self, *, complexity: int, always_on: bool) -> tuple[str, str]:
        complexity = max(0, min(100, int(complexity)))

        if complexity <= 25:
            idx = 0
        elif complexity <= 50:
            idx = 1
        elif complexity <= 75:
            idx = 2
        else:
            idx = 3

        if always_on:
            idx = min(3, idx + 1)

        levels = ['low', 'moderate', 'high', 'severe']
        warnings = [
            'Low impact: minimal background activity.',
            'Moderate impact: may increase battery usage and network chatter.',
            'High impact: noticeable battery drain and increased network activity.',
            'Severe impact: heavy battery/network usage. Use sparingly on mobile data.',
        ]

        return levels[idx], warnings[idx]

    def force_refresh_preview(self):
        self._refresh_preview(0, force=True)

    def _refresh_preview(self, dt, force: bool = False):
        if not self._service_running and not force:
            return

        if not self._config['enabled']:
            if self._state.get('preview_actions'):
                self._update_state({'preview_actions': [], 'preview_updated_at': None}, emit=True)
            return

        raw_actions = deep_learning_agent.generate_activity_preview(
            pattern_type=self._config['pattern_type'],
            complexity=int(self._config['complexity']),
            human_like=bool(self._config['human_like_synthesis']),
        )
        actions: List[str] = [sanitize_action_text(a) for a in raw_actions]

        self._update_state(
            {
                'preview_actions': actions,
                'preview_updated_at': time.time(),
            },
            emit=True,
        )

    def _emit_state(self):
        event_bus.emit_max_ai_state(dict(self._state))

    def _update_state(self, patch: Dict[str, Any], *, emit: bool):
        self._state.update(patch)
        self._state_version += 1
        self._state['state_version'] = self._state_version
        if emit:
            self._emit_state()


maximum_ai_manager = MaximumAIManager()
