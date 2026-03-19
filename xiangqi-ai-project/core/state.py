from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .board import Board
from .move import Move
from .rules import Color, Piece, Pos, find_general


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

   
    def copy(self) -> "GameState":
        return GameState(
            board=self.board.copy(),
            side_to_move=self.side_to_move,
            move_history=list(self.move_history),
        )

   
    def clone(self) -> "GameState":
        return self.copy()

    def apply_move(self, move: Move) -> Undo:
        moved = self.board.get(move.src)
        if moved is None:
            raise ValueError("invalid move: empty src")
        captured = self.board.move_piece(move.src, move.dst)
        undo = Undo(
            src=move.src,
            dst=move.dst,
            moved=moved,
            captured=captured,
            prev_side_to_move=self.side_to_move,
        )
        self.side_to_move = self.side_to_move.other
        self.move_history.append(Move(move.src, move.dst, capture=captured))
        return undo

   
    def undo_move(self, undo: Undo) -> None:
      
        self.side_to_move = undo.prev_side_to_move
        self.board.set(undo.src, undo.moved)
        self.board.set(undo.dst, undo.captured)
        if self.move_history:
            self.move_history.pop()

    
    def is_terminal(self) -> bool:
        """Kiểm tra xem game đã kết thúc chưa (mất tướng hoặc lộ mặt tướng)"""
        red_gen = find_general(self.board.get, Color.RED)
        black_gen = find_general(self.board.get, Color.BLACK)
        
        if red_gen is None or black_gen is None:
            return True
        return False
