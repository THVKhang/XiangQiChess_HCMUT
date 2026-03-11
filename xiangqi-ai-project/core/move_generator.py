from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Tuple

from .move import Move
from .rules import (
    BOARD_COLS,
    BOARD_ROWS,
    Color,
    Piece,
    PieceType,
    Pos,
    enemy_color,
    find_general,
    generals_face_each_other,
    in_bounds,
    on_own_side_of_river,
    palace_contains,
    ray_squares,
    soldier_forward_delta,
    same_color,
)
from .state import GameState


ORTHO_DIRS: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _yield_if_ok(
    state: GameState, src: Pos, dst: Pos, *, allow_empty: bool = True
) -> Iterator[Move]:
    if not in_bounds(dst):
        return
    sp = state.board.get(src)
    if sp is None:
        return
    tp = state.board.get(dst)
    if tp is None:
        if allow_empty:
            yield Move(src, dst, capture=None)
        return
    if enemy_color(sp, tp):
        yield Move(src, dst, capture=tp)


def pseudo_legal_moves_for_piece(state: GameState, src: Pos) -> Iterator[Move]:
    p = state.board.get(src)
    if p is None:
        return
    r, c = src

    if p.kind is PieceType.ROOK:
        for dr, dc in ORTHO_DIRS:
            for sq in ray_squares(src, dr, dc):
                tp = state.board.get(sq)
                if tp is None:
                    yield Move(src, sq, None)
                    continue
                if enemy_color(p, tp):
                    yield Move(src, sq, tp)
                break

    elif p.kind is PieceType.CANNON:
        # Move like rook when not capturing.
        # Capture: must have exactly one screen piece between src and dst on same rank/file.
        for dr, dc in ORTHO_DIRS:
            screened = False
            for sq in ray_squares(src, dr, dc):
                tp = state.board.get(sq)
                if not screened:
                    if tp is None:
                        yield Move(src, sq, None)
                        continue
                    screened = True
                    continue
                # screened == True
                if tp is None:
                    continue
                if enemy_color(p, tp):
                    yield Move(src, sq, tp)
                break

    elif p.kind is PieceType.HORSE:
        # Knight with leg block.
        # (dr, dc, leg_pos)
        candidates: list[tuple[int, int, Pos]] = [
            (-2, -1, (r - 1, c)),
            (-2, 1, (r - 1, c)),
            (2, -1, (r + 1, c)),
            (2, 1, (r + 1, c)),
            (-1, -2, (r, c - 1)),
            (1, -2, (r, c - 1)),
            (-1, 2, (r, c + 1)),
            (1, 2, (r, c + 1)),
        ]
        for dr, dc, leg in candidates:
            if not in_bounds(leg) or state.board.get(leg) is not None:
                continue
            dst = (r + dr, c + dc)
            yield from _yield_if_ok(state, src, dst)

    elif p.kind is PieceType.ELEPHANT:
        # 2 diagonal, cannot cross river, eye block.
        candidates: list[tuple[int, int, Pos]] = [
            (-2, -2, (r - 1, c - 1)),
            (-2, 2, (r - 1, c + 1)),
            (2, -2, (r + 1, c - 1)),
            (2, 2, (r + 1, c + 1)),
        ]
        for dr, dc, eye in candidates:
            dst = (r + dr, c + dc)
            if not in_bounds(dst):
                continue
            if not on_own_side_of_river(p.color, dst):
                continue
            if state.board.get(eye) is not None:
                continue
            yield from _yield_if_ok(state, src, dst)

    elif p.kind is PieceType.ADVISOR:
        # 1 diagonal, within palace.
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            dst = (r + dr, c + dc)
            if not in_bounds(dst) or not palace_contains(p.color, dst):
                continue
            yield from _yield_if_ok(state, src, dst)

    elif p.kind is PieceType.GENERAL:
        # 1 orthogonal within palace; plus "flying general" capture on same file if clear.
        for dr, dc in ORTHO_DIRS:
            dst = (r + dr, c + dc)
            if not in_bounds(dst) or not palace_contains(p.color, dst):
                continue
            yield from _yield_if_ok(state, src, dst)

        # flying general capture (treated as a legal capture if unobstructed)
        for dr, dc in [(-1, 0), (1, 0)]:
            for sq in ray_squares(src, dr, dc):
                tp = state.board.get(sq)
                if tp is None:
                    continue
                if tp.kind is PieceType.GENERAL and enemy_color(p, tp):
                    yield Move(src, sq, tp)
                break

    elif p.kind is PieceType.SOLDIER:
        f = soldier_forward_delta(p.color)
        # forward
        yield from _yield_if_ok(state, src, (r + f, c))
        # sideways after crossing river
        if not on_own_side_of_river(p.color, src):
            yield from _yield_if_ok(state, src, (r, c - 1))
            yield from _yield_if_ok(state, src, (r, c + 1))


def pseudo_legal_moves(state: GameState, color: Optional[Color] = None) -> List[Move]:
    """
    Sinh nước đi theo luật di chuyển quân, chưa lọc tự-chiếu và "tướng đối mặt".
    """
    if color is None:
        color = state.side_to_move
    out: list[Move] = []
    for (pos, p) in state.board.squares():
        if p is None or p.color is not color:
            continue
        out.extend(list(pseudo_legal_moves_for_piece(state, pos)))
    return out


def _is_in_check(state: GameState, color: Color) -> bool:
    gpos = find_general(state.board.get, color)
    if gpos is None:
        return True  # king captured => considered in-check (terminal)
    # Any enemy pseudo move capturing the general square means check.
    for m in pseudo_legal_moves(state, color.other):
        if m.dst == gpos:
            return True
    return False


def _violates_facing_generals(state: GameState) -> bool:
    red_g = find_general(state.board.get, Color.RED)
    black_g = find_general(state.board.get, Color.BLACK)
    if red_g is None or black_g is None:
        return False
    return generals_face_each_other(state.board.get, red_g, black_g)


def legal_moves(state: GameState) -> List[Move]:
    """
    Nước đi hợp lệ: không tự để tướng bị chiếu và không làm 2 tướng đối mặt.
    """
    color = state.side_to_move
    out: list[Move] = []
    for m in pseudo_legal_moves(state, color):
        undo = state.apply_move(m)
        illegal = _is_in_check(state, color) or _violates_facing_generals(state)
        state.undo_move(undo)
        if not illegal:
            out.append(m)
    return out


def is_check(state: GameState, color: Optional[Color] = None) -> bool:
    if color is None:
        color = state.side_to_move
    return _is_in_check(state, color)


@dataclass(frozen=True, slots=True)
class GameResult:
    winner: Optional[Color]  # None means draw/unknown
    reason: str


def result_if_terminal(state: GameState) -> Optional[GameResult]:
    """
    Terminal tối thiểu:
    - **Checkmate**: bên tới lượt không có nước hợp lệ và đang bị chiếu.
    - **Stalemate**: bên tới lượt không có nước hợp lệ và không bị chiếu (tính là hòa).
    """
    moves = legal_moves(state)
    if moves:
        return None
    stm = state.side_to_move
    if _is_in_check(state, stm):
        return GameResult(winner=stm.other, reason="checkmate")
    return GameResult(winner=None, reason="stalemate")

