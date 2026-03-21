from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from core.move import Move
from core.move_generator import legal_moves
from core.state import GameState


@dataclass(slots=True)
class RandomAgent:
    """Agent chọn ngẫu nhiên một nước đi hợp lệ."""

    name: str = "RandomAgent"
    rng: random.Random = field(default_factory=random.Random)

    def select_move(self, state: GameState) -> Optional[Move]:
        moves = legal_moves(state)
        if not moves:
            return None
        return self.rng.choice(moves)
