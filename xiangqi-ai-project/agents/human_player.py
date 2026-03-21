from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from core.move import Move
from core.move_generator import legal_moves
from core.state import GameState

InputFunc = Callable[[str], str]
OutputFunc = Callable[[str], None]


@dataclass(slots=True)
class HumanPlayer:
    """Người chơi nhập nước đi từ terminal theo dạng: r1 c1 r2 c2"""

    name: str = "HumanPlayer"
    input_func: InputFunc = input
    output_func: OutputFunc = print

    def select_move(self, state: GameState) -> Optional[Move]:
        moves = legal_moves(state)
        if not moves:
            self.output_func("No legal moves available.")
            return None

        legal_by_coords = {(m.src, m.dst): m for m in moves}

        while True:
            raw = self.input_func(
                f"{state.side_to_move.value} to move. Enter move as 'src_row src_col dst_row dst_col': "
            ).strip()
            try:
                move = self._parse_move(raw)
            except ValueError as exc:
                self.output_func(str(exc))
                continue

            matched = legal_by_coords.get((move.src, move.dst))
            if matched is not None:
                return matched
            self.output_func("Illegal move. Please try again.")

    @staticmethod
    def _parse_move(raw: str) -> Move:
        parts = raw.replace(",", " ").split()
        if len(parts) != 4:
            raise ValueError("Please enter exactly 4 integers: src_row src_col dst_row dst_col")
        try:
            src_r, src_c, dst_r, dst_c = map(int, parts)
        except ValueError as exc:
            raise ValueError("Move coordinates must be integers.") from exc
        return Move(src=(src_r, src_c), dst=(dst_r, dst_c))
