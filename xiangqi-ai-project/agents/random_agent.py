from __future__ import annotations

import random
from typing import Optional

from core.move import Move
from core.move_generator import legal_moves
from core.state import GameState
from agents.base_agent import BaseAgent

class RandomAgent(BaseAgent):
    """Agent chọn ngẫu nhiên một nước đi hợp lệ."""

    def __init__(self, player_id, name: str = "RandomAgent", rng: Optional[random.Random] = None):
        super().__init__(player_id)
        self.name = name
        self.rng = rng if rng is not None else random.Random()

    def select_move(self, state: GameState) -> Optional[Move]:
        moves = legal_moves(state)
        if not moves:
            return None
        return self.rng.choice(moves)
