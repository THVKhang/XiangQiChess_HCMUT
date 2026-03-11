from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional

from .rules import (
    BOARD_COLS,
    BOARD_ROWS,
    Piece,
    Pos,
    initial_setup_piece_at,
    in_bounds,
)


@dataclass(slots=True)
class Board:
    grid: List[List[Optional[Piece]]]

    @classmethod
    def initial(cls) -> "Board":
        grid: List[List[Optional[Piece]]] = []
        for r in range(BOARD_ROWS):
            row: List[Optional[Piece]] = []
            for c in range(BOARD_COLS):
                row.append(initial_setup_piece_at((r, c)))
            grid.append(row)
        return cls(grid=grid)

    @classmethod
    def empty(cls) -> "Board":
        return cls(grid=[[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)])

    def copy(self) -> "Board":
        return Board(grid=[list(row) for row in self.grid])

    def get(self, pos: Pos) -> Optional[Piece]:
        r, c = pos
        return self.grid[r][c]

    def set(self, pos: Pos, piece: Optional[Piece]) -> None:
        r, c = pos
        self.grid[r][c] = piece

    def move_piece(self, src: Pos, dst: Pos) -> Optional[Piece]:
        if not in_bounds(src) or not in_bounds(dst):
            raise ValueError("pos out of bounds")
        piece = self.get(src)
        if piece is None:
            raise ValueError("no piece at src")
        captured = self.get(dst)
        self.set(dst, piece)
        self.set(src, None)
        return captured

    def squares(self) -> Iterator[tuple[Pos, Optional[Piece]]]:
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                yield (r, c), self.grid[r][c]

