"""Helpers trùng khớp logic GameLoop cho vị trí lặp / đếm threefold."""

from __future__ import annotations

from typing import Tuple

from core.state import GameState

# Giống kiểu khóa trong ``GameLoop._position_key``.
PositionKey = Tuple[str, Tuple[Tuple[Tuple[int, int], str, str], ...]]


def game_loop_position_key(state: GameState) -> PositionKey:
    """Khóa vị trí giống ``GameLoop._position_key`` (side_to_move + quân trên bàn)."""
    pieces: list[tuple[tuple[int, int], str, str]] = []
    for pos, piece in state.board.squares():
        if piece is None:
            continue
        pieces.append((pos, piece.color.value, piece.kind.value))
    pieces.sort()
    return state.side_to_move.value, tuple(pieces)


def cumulative_position_visit_counts(state: GameState) -> dict[PositionKey, int]:
    """Đếm số lần mỗi khóa vị trí đã xuất hiện (khởi tạo giống GameLoop: trạng thái đầu = 1)."""
    counts: dict[PositionKey, int] = {}
    replay = GameState()
    k0 = game_loop_position_key(replay)
    counts[k0] = 1
    for mv in state.move_history:
        replay.apply_move(mv)
        k = game_loop_position_key(replay)
        counts[k] = counts.get(k, 0) + 1
    return counts
