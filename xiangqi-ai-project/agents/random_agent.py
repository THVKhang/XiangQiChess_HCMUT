from __future__ import annotations

import random
from typing import Optional

from core.move import Move
from core.move_generator import legal_moves
from core.rules import Color
from core.state import GameState


class RandomAgent:
    """Agent chọn ngẫu nhiên một nước đi hợp lệ cho phe được gán."""

    def __init__(
        self,
        player_id: Color,
        name: str = "RandomAgent",
        rng: Optional[random.Random] = None,
    ) -> None:
        self.player_id = player_id
        self.name = name
        self.rng = rng if rng is not None else random.Random()

    def select_move(self, state: GameState) -> Optional[Move]:
        """Chọn ngẫu nhiên một move trong tập legal moves của state hiện tại."""
        moves = legal_moves(state)
        if not moves:
            return None
        return self.rng.choice(moves)
