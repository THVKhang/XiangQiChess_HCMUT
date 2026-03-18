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
        """Khởi tạo bàn cờ với vị trí chuẩn"""
        grid: List[List[Optional[Piece]]] = []
        for r in range(BOARD_ROWS):
            row: List[Optional[Piece]] = []
            for c in range(BOARD_COLS):
                row.append(initial_setup_piece_at((r, c)))
            grid.append(row)
        return cls(grid=grid)

    @classmethod
    def empty(cls) -> "Board":
        """Khởi tạo bàn cờ trống"""
        return cls(grid=[[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)])

    def copy(self) -> "Board":
        """Tạo bản sao độc lập (shallow copy của từng row)"""
        return Board(grid=[list(row) for row in self.grid])

    def get(self, pos: Pos) -> Optional[Piece]:
        """Lấy quân cờ tại vị trí pos"""
        r, c = pos
        return self.grid[r][c]

    def set(self, pos: Pos, piece: Optional[Piece]) -> None:
        """Đặt một quân cờ (hoặc None) vào vị trí pos"""
        r, c = pos
        self.grid[r][c] = piece

    def move_piece(self, src: Pos, dst: Pos) -> Optional[Piece]:
        """Di chuyển quân và trả về quân bị ăn nếu có"""
        if not in_bounds(src) or not in_bounds(dst):
            raise ValueError(f"Position out of bounds: {src} -> {dst}")
        
        piece = self.get(src)
        if piece is None:
            raise ValueError(f"No piece at source: {src}")
            
        captured = self.get(dst)
        self.set(dst, piece)
        self.set(src, None)
        return captured

    def squares(self) -> Iterator[tuple[Pos, Optional[Piece]]]:
        """Duyệt qua tất cả các ô trên bàn cờ"""
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                yield (r, c), self.grid[r][c]

    def __repr__(self) -> str:
        """Hiển thị bàn cờ dạng văn bản để dễ dàng debug"""
        lines = []
        for row in self.grid:
            chars = []
            for p in row:
                if p is None:
                    chars.append(".")
                else:
                    # Lấy chữ cái đầu của màu và loại quân (vị dụ: rR cho Red Rook)
                    color_code = 'r' if p.color.value == "red" else 'b'
                    kind_code = p.kind.value[0].upper()
                    chars.append(f"{color_code}{kind_code}")
            lines.append(" ".join(chars))
        return "\n".join(lines)