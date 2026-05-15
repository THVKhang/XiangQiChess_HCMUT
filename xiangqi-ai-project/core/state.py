from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, TYPE_CHECKING 

if TYPE_CHECKING:
    from .move_generator import legal_moves, is_check, result_if_terminal

from .board import Board
from .move import Move
from .rules import (
    BOARD_COLS,
    BOARD_ROWS,
    Color,
    Piece,
    PieceType,
    Pos,
    in_bounds,
)

@dataclass(slots=True)
class Undo:
    src: Pos
    dst: Pos
    moved: Piece
    captured: Optional[Piece]
    prev_side_to_move: Color

@dataclass(slots=True)
class GameState:
    board: Board = field(default_factory=Board.initial)
    side_to_move: Color = Color.RED
    move_history: List[Move] = field(default_factory=list)

    def clone(self) -> "GameState":
        return GameState(
            board=self.board.copy(),
            side_to_move=self.side_to_move,
            move_history=self.move_history.copy() 
        )

    def copy(self) -> "GameState":
        return self.clone()

    def to_tensor(
        self,
        *,
        channels_first: bool = True,
        canonical: bool = False,
        as_numpy: bool = False,
        dtype: str = "float32",
    ) -> "Sequence[Sequence[Sequence[float]]]":
        """Encode this game state directly into a tensor."""
        from .encoding import state_to_tensor

        return state_to_tensor(
            self,
            channels_first=channels_first,
            canonical=canonical,
            as_numpy=as_numpy,
            dtype=dtype,
        )

    def tensor_sequence(
        self,
        moves: Sequence[Move],
        *,
        include_initial: bool = True,
        include_final: bool = True,
        channels_first: bool = True,
        canonical: bool = False,
        as_numpy: bool = False,
        dtype: str = "float32",
    ) -> "Sequence":
        """Encode a game trajectory starting from this state."""
        from .encoding import game_to_tensor_sequence

        return game_to_tensor_sequence(
            self,
            moves,
            include_initial=include_initial,
            include_final=include_final,
            channels_first=channels_first,
            canonical=canonical,
            as_numpy=as_numpy,
            dtype=dtype,
        )

    def validate(self) -> None:
        """Verify the internal consistency of the game state for debugging."""
        if not isinstance(self.board, Board):
            raise TypeError(f"GameState.board must be Board, got {type(self.board).__name__}")
        if len(self.board.grid) != BOARD_ROWS or any(len(row) != BOARD_COLS for row in self.board.grid):
            raise ValueError(f"Board grid must be {BOARD_ROWS}x{BOARD_COLS}")

        red_generals = 0
        black_generals = 0
        for r, row in enumerate(self.board.grid):
            for c, piece in enumerate(row):
                if piece is None:
                    continue
                if not isinstance(piece, Piece):
                    raise TypeError(f"Board cell {(r, c)} must be Piece or None, got {type(piece).__name__}")
                if not in_bounds((r, c)):
                    raise ValueError(f"Piece position out of bounds: {(r, c)}")
                if piece.kind == PieceType.GENERAL:
                    if piece.color == Color.RED:
                        red_generals += 1
                    elif piece.color == Color.BLACK:
                        black_generals += 1

        if red_generals > 1:
            raise ValueError(f"Invalid state: {red_generals} red generals found")
        if black_generals > 1:
            raise ValueError(f"Invalid state: {black_generals} black generals found")

        if not isinstance(self.move_history, list):
            raise TypeError(f"GameState.move_history must be a list, got {type(self.move_history).__name__}")
        for move in self.move_history:
            if not isinstance(move, Move):
                raise TypeError(f"move_history elements must be Move, got {type(move).__name__}")
            if not in_bounds(move.src) or not in_bounds(move.dst):
                raise ValueError(f"Move in history has out-of-bounds position: {move}")

    def apply_move(self, move: Move) -> Undo:
        piece = self.board.get(move.src)
        if piece is None or piece.color != self.side_to_move:
            raise ValueError(f"Lỗi tích hợp: Chọn sai quân hoặc sai lượt tại {move.src}")

        captured = self.board.move_piece(move.src, move.dst)
        undo = Undo(
            src=move.src,
            dst=move.dst,
            moved=piece,
            captured=captured,
            prev_side_to_move=self.side_to_move,
        )
        
        full_move = Move(move.src, move.dst, capture=captured)
        self.move_history.append(full_move)
        
        self.side_to_move = self.side_to_move.other
        return undo

    def undo_move(self, undo: Undo) -> None:
        self.side_to_move = undo.prev_side_to_move
        self.board.set(undo.src, undo.moved)
        self.board.set(undo.dst, undo.captured)
        if self.move_history:
            self.move_history.pop()

    def get_legal_moves(self) -> list[Move]:
        from .move_generator import legal_moves
        return legal_moves(self)

    @property
    def is_check(self) -> bool:
        from .move_generator import is_check
        return is_check(self, self.side_to_move)
    
    def is_terminal(self) -> bool:
        from .move_generator import is_terminal
        return is_terminal(self)