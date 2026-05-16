"""Ánh xạ Move ↔ policy phẳng cho ML, khớp ``BOARD_*``/``Color`` và ``state_to_tensor(canonical=True)``."""

from __future__ import annotations

from .move import Move
from .rules import BOARD_COLS, BOARD_ROWS, Color, Pos

# Một lượt action = (ô xuất phát, ô đích) trên lưới 10×9.
BOARD_SQUARES: int = BOARD_ROWS * BOARD_COLS
POLICY_FLAT_LEN: int = BOARD_SQUARES * BOARD_SQUARES


def square_index(pos: Pos) -> int:
    """Ô 0..89: hàng * 9 + cột."""
    r, c = pos
    return r * BOARD_COLS + c


def move_to_policy_index(move: Move) -> int:
    """Policy index theo tọa độ bàn gốc (không xoay canonical)."""
    return square_index(move.src) * BOARD_SQUARES + square_index(move.dst)


def canonical_square(pos: Pos, side_to_move: Color) -> Pos:
    """Cùng phép xoay 180° như ``state_to_tensor(..., canonical=True)`` khi tới lượt Đen."""
    if side_to_move == Color.BLACK:
        return BOARD_ROWS - 1 - pos[0], BOARD_COLS - 1 - pos[1]
    return pos


def canonical_move_to_policy_index(move: Move, side_to_move: Color) -> int:
    """Policy index khi tensor đã canonical (người tới lượt luôn được nhìn như Đỏ trong tensor)."""
    src = canonical_square(move.src, side_to_move)
    dst = canonical_square(move.dst, side_to_move)
    return square_index(src) * BOARD_SQUARES + square_index(dst)
