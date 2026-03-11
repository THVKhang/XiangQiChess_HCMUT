from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Tuple

BOARD_COLS = 9
BOARD_ROWS = 10

Pos = Tuple[int, int]  # (row, col) with row in [0..9], col in [0..8]


class Color(str, Enum):
    RED = "red"
    BLACK = "black"

    @property
    def other(self) -> "Color":
        return Color.BLACK if self is Color.RED else Color.RED


class PieceType(str, Enum):
    GENERAL = "general"  # tướng
    ADVISOR = "advisor"  # sĩ
    ELEPHANT = "elephant"  # tượng
    HORSE = "horse"  # mã
    ROOK = "rook"  # xe
    CANNON = "cannon"  # pháo
    SOLDIER = "soldier"  # tốt


@dataclass(frozen=True, slots=True)
class Piece:
    color: Color
    kind: PieceType


def in_bounds(pos: Pos) -> bool:
    r, c = pos
    return 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS


def same_color(a: Optional[Piece], b: Optional[Piece]) -> bool:
    return a is not None and b is not None and a.color == b.color


def enemy_color(a: Optional[Piece], b: Optional[Piece]) -> bool:
    return a is not None and b is not None and a.color != b.color


def palace_contains(color: Color, pos: Pos) -> bool:
    r, c = pos
    if color is Color.RED:
        return 7 <= r <= 9 and 3 <= c <= 5
    return 0 <= r <= 2 and 3 <= c <= 5


def on_own_side_of_river(color: Color, pos: Pos) -> bool:
    r, _ = pos
    # River is between rows 4 and 5 (0-indexed)
    if color is Color.RED:
        return r >= 5
    return r <= 4


def soldier_forward_delta(color: Color) -> int:
    return -1 if color is Color.RED else 1


def initial_setup_piece_at(pos: Pos) -> Optional[Piece]:
    """
    Thiết lập chuẩn (bên Đỏ ở hàng 9, bên Đen ở hàng 0).
    Ký hiệu hàng/cột: (row, col), row 0 ở phía Đen.
    """
    r, c = pos
    # Generals
    if (r, c) == (0, 4):
        return Piece(Color.BLACK, PieceType.GENERAL)
    if (r, c) == (9, 4):
        return Piece(Color.RED, PieceType.GENERAL)

    # Advisors
    if (r, c) in {(0, 3), (0, 5)}:
        return Piece(Color.BLACK, PieceType.ADVISOR)
    if (r, c) in {(9, 3), (9, 5)}:
        return Piece(Color.RED, PieceType.ADVISOR)

    # Elephants
    if (r, c) in {(0, 2), (0, 6)}:
        return Piece(Color.BLACK, PieceType.ELEPHANT)
    if (r, c) in {(9, 2), (9, 6)}:
        return Piece(Color.RED, PieceType.ELEPHANT)

    # Horses
    if (r, c) in {(0, 1), (0, 7)}:
        return Piece(Color.BLACK, PieceType.HORSE)
    if (r, c) in {(9, 1), (9, 7)}:
        return Piece(Color.RED, PieceType.HORSE)

    # Rooks
    if (r, c) in {(0, 0), (0, 8)}:
        return Piece(Color.BLACK, PieceType.ROOK)
    if (r, c) in {(9, 0), (9, 8)}:
        return Piece(Color.RED, PieceType.ROOK)

    # Cannons
    if (r, c) in {(2, 1), (2, 7)}:
        return Piece(Color.BLACK, PieceType.CANNON)
    if (r, c) in {(7, 1), (7, 7)}:
        return Piece(Color.RED, PieceType.CANNON)

    # Soldiers
    if r == 3 and c in {0, 2, 4, 6, 8}:
        return Piece(Color.BLACK, PieceType.SOLDIER)
    if r == 6 and c in {0, 2, 4, 6, 8}:
        return Piece(Color.RED, PieceType.SOLDIER)

    return None


def ray_squares(src: Pos, dr: int, dc: int) -> Iterable[Pos]:
    r, c = src
    r += dr
    c += dc
    while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS:
        yield (r, c)
        r += dr
        c += dc


def generals_face_each_other(board_get, red_general: Pos, black_general: Pos) -> bool:
    """
    Hai tướng "đối mặt" nếu cùng cột và giữa chúng không có quân nào.
    board_get: callable(pos)->Optional[Piece]
    """
    rr, rc = red_general
    br, bc = black_general
    if rc != bc:
        return False
    col = rc
    step = 1 if br > rr else -1
    for r in range(rr + step, br, step):
        if board_get((r, col)) is not None:
            return False
    return True


def find_general(board_get, color: Color) -> Optional[Pos]:
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            p = board_get((r, c))
            if p is not None and p.color is color and p.kind is PieceType.GENERAL:
                return (r, c)
    return None

