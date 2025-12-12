import random
import time
from typing import List, Optional


class DeepLearningAgent:
    PATTERN_TYPES = [
        'Stealth',
        'Burst',
        'Adaptive',
        'Random Walk',
    ]

    def __init__(self):
        self._seed = int(time.time())

    def train(self, data):
        print("Training model...")

    def predict(self, input_data):
        print("Predicting...")
        return "Prediction"

    def generate_activity_preview(
        self,
        *,
        pattern_type: str,
        complexity: int,
        human_like: bool,
        count: Optional[int] = None,
    ) -> List[str]:
        rng = random.Random(self._seed + int(time.time() // 2))

        pattern_type = pattern_type if pattern_type in self.PATTERN_TYPES else 'Adaptive'
        complexity = max(0, min(100, int(complexity)))

        if count is None:
            count = max(3, min(10, 3 + int(complexity / 12)))

        base_actions = {
            'Stealth': [
                'Idle (background noise)',
                'Move pointer slightly',
                'Scroll feed gently',
                'Open a page and wait',
                'Read a message preview',
                'Dismiss notification',
            ],
            'Burst': [
                'Open 3 tabs quickly',
                'Rapid scroll → stop',
                'Send short ping',
                'Refresh dashboard',
                'Toggle setting',
            ],
            'Adaptive': [
                'Observe traffic stats',
                'Adjust pacing based on latency',
                'Interleave browsing + idle',
                'Re-order actions based on context',
                'Probe endpoint health',
            ],
            'Random Walk': [
                'Navigate to random section',
                'Scroll random distance',
                'Open random item',
                'Back',
                'Wait',
            ],
        }[pattern_type]

        actions: List[str] = []
        for _ in range(int(count)):
            a = rng.choice(base_actions)

            if complexity >= 60 and rng.random() < 0.2:
                a = rng.choice(
                    [
                        'Prefetch content (higher bandwidth)',
                        'Background sync attempt',
                        'Open media preview <img src=x onerror=alert(1)>',
                        'Click\nNewline Injection',
                    ]
                )

            if human_like:
                delay_ms = max(80, int(rng.gauss(320, 120)))
                jitter = rng.choice(['micro-jitter', 'natural pause', 'hesitation'])
                a = f"{a} • {jitter} • {delay_ms}ms"

            actions.append(a)

        if complexity >= 85:
            actions.insert(0, 'High complexity: multi-threaded simulation <script>bad()</script>')

        return actions


deep_learning_agent = DeepLearningAgent()
