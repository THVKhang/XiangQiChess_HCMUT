from __future__ import annotations

from typing import Iterable, Literal, Sequence

from .rules import BOARD_COLS, BOARD_ROWS, Color, PieceType
from .state import GameState
from .move import Move

# Channel order (fixed):
#   0..6   : Red   (general, advisor, elephant, horse, rook, cannon, soldier)
#   7..13  : Black (general, advisor, elephant, horse, rook, cannon, soldier)
#   14     : side-to-move plane (1 for RED, 0 for BLACK) in the original (non-canonical) view.
_PIECE_KIND_ORDER: tuple[PieceType, ...] = (
    PieceType.GENERAL,
    PieceType.ADVISOR,
    PieceType.ELEPHANT,
    PieceType.HORSE,
    PieceType.ROOK,
    PieceType.CANNON,
    PieceType.SOLDIER,
)

_KIND_TO_OFFSET = {k: i for i, k in enumerate(_PIECE_KIND_ORDER)}


def _piece_channel_index(color: Color, kind: PieceType) -> int:
    off = _KIND_TO_OFFSET.get(kind)
    if off is None:
        raise ValueError(f"Unknown piece kind: {kind}")
    return off if color == Color.RED else (7 + off)


def state_to_tensor(
    state: GameState,
    *,
    channels_first: bool = True,
    canonical: bool = False,
    as_numpy: bool = False,
    dtype: Literal["float32", "float64"] = "float32",
) -> "Sequence[Sequence[Sequence[float]]]":
    """
    Encode a Xiangqi `GameState` into a dense tensor suitable for NN models.

    Output planes:
    - 14 one-hot planes for piece placement (7 kinds x 2 colors)
    - 1 plane for side-to-move (broadcast over 10x9)

    Shape:
    - channels_first=True  -> (15, 10, 9)
    - channels_first=False -> (10, 9, 15)

    canonical=True:
    - If side-to-move is BLACK, rotate board 180 degrees and swap colors before encoding.
      This makes "current player" always appear as RED in the tensor.
    - The side-to-move plane is still included (it becomes constant 1 everywhere).

    as_numpy=True:
    - Returns a `numpy.ndarray` (requires numpy installed).
    - Otherwise returns nested Python lists.
    """

    if as_numpy:
        try:
            import numpy as np  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "state_to_tensor(as_numpy=True) requires numpy. "
                "Install it first (e.g. `pip install numpy`)."
            ) from exc

        x = np.zeros((15, BOARD_ROWS, BOARD_COLS), dtype=getattr(np, dtype))
        side_val = 1.0 if state.side_to_move == Color.RED else 0.0

        flip = canonical and state.side_to_move == Color.BLACK
        if flip:
            side_val = 1.0

        x[14, :, :] = side_val

        for (r, c), piece in state.board.squares():
            if piece is None:
                continue

            rr, cc = (BOARD_ROWS - 1 - r, BOARD_COLS - 1 - c) if flip else (r, c)
            color = piece.color.other if flip else piece.color
            ch = _piece_channel_index(color, piece.kind)
            x[ch, rr, cc] = 1.0

        if channels_first:
            return x
        return np.transpose(x, (1, 2, 0))

    # Pure-Python nested lists path (no extra deps)
    x: list[list[list[float]]] = [
        [[0.0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)] for _ in range(15)
    ]

    side_val = 1.0 if state.side_to_move == Color.RED else 0.0
    flip = canonical and state.side_to_move == Color.BLACK
    if flip:
        side_val = 1.0

    for r in range(BOARD_ROWS):
        row = x[14][r]
        for c in range(BOARD_COLS):
            row[c] = side_val

    for (r, c), piece in state.board.squares():
        if piece is None:
            continue

        rr, cc = (BOARD_ROWS - 1 - r, BOARD_COLS - 1 - c) if flip else (r, c)
        color = piece.color.other if flip else piece.color
        ch = _piece_channel_index(color, piece.kind)
        x[ch][rr][cc] = 1.0

    if channels_first:
        return x

    # (C, H, W) -> (H, W, C)
    hwc: list[list[list[float]]] = [
        [[0.0 for _ in range(15)] for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)
    ]
    for ch in range(15):
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                hwc[r][c][ch] = x[ch][r][c]
    return hwc


def game_to_tensor_sequence(
    initial_state: GameState,
    moves: Sequence[Move],
    *,
    include_initial: bool = True,
    include_final: bool = True,
    channels_first: bool = True,
    canonical: bool = False,
    as_numpy: bool = False,
    dtype: Literal["float32", "float64"] = "float32",
) -> Sequence:
    """
    Encode a full game into a sequence of tensors by replaying `moves` from `initial_state`.

    By default this returns tensors for:
    - initial position (before any move)
    - each intermediate position after applying a move

    If `as_numpy=True`, returns a numpy array stack with shape:
    - channels_first=True  -> (T, 15, 10, 9)
    - channels_first=False -> (T, 10, 9, 15)
    Otherwise returns a Python list of tensors.
    """

    replay = initial_state.clone()
    seq = []

    if include_initial:
        seq.append(
            state_to_tensor(
                replay, channels_first=channels_first, canonical=canonical, as_numpy=as_numpy, dtype=dtype
            )
        )

    for mv in moves:
        replay.apply_move(Move(src=mv.src, dst=mv.dst))
        seq.append(
            state_to_tensor(
                replay, channels_first=channels_first, canonical=canonical, as_numpy=as_numpy, dtype=dtype
            )
        )

    if not include_final and seq:
        seq = seq[:-1]

    if as_numpy:
        import numpy as np  # type: ignore

        return np.stack(seq, axis=0)

    return seq

