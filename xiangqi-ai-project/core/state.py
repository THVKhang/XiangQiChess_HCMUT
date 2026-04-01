from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING 

if TYPE_CHECKING:
    from .move_generator import legal_moves, is_check, result_if_terminal

from .board import Board
from .move import Move
from .rules import Color, Piece, Pos

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