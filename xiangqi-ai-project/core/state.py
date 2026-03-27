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
        """Tối ưu hiệu năng: Chỉ copy history khi cần thiết"""
        return GameState(
            board=self.board.copy(),
            side_to_move=self.side_to_move,
            # AI Search thường không cần xem lại lịch sử toàn bộ trận đấu
            move_history=self.move_history.copy() 
        )

    def copy(self) -> "GameState":
        """Alias cho clone() để tương thích API cũ/tests."""
        return self.clone()

    def apply_move(self, move: Move) -> Undo:
        """Fix state bug: Kiểm tra quân cờ và lượt đi"""
        moved = self.board.get(move.src)
        if moved is None:
            raise ValueError(f"Lỗi: Không có quân cờ tại {move.src}")
        if moved.color != self.side_to_move:
            raise ValueError(f"Lỗi: Sai lượt đi. Hiện tại là lượt của {self.side_to_move}")

        captured = self.board.move_piece(move.src, move.dst)
        undo = Undo(
            src=move.src,
            dst=move.dst,
            moved=moved,
            captured=captured,
            prev_side_to_move=self.side_to_move,
        )
        self.side_to_move = self.side_to_move.other
        # Cập nhật thông tin capture vào Move để đồng bộ history
        full_move = Move(move.src, move.dst, capture=captured)
        self.move_history.append(full_move)
        return undo

    def undo_move(self, undo: Undo) -> None:
        """Khôi phục trạng thái chuẩn xác"""
        self.side_to_move = undo.prev_side_to_move
        self.board.set(undo.src, undo.moved)
        self.board.set(undo.dst, undo.captured)
        if self.move_history:
            self.move_history.pop()

    # core/state.py

    def get_legal_moves(self) -> list[Move]:
        """Đảm bảo phần của Khoa gọi đúng luật mà không bị lỗi vòng lặp"""
        import core.move_generator as mg
        return mg.legal_moves(self)

    @property
    def is_check(self) -> bool:
        """Đảm bảo thuộc tính check hoạt động độc lập"""
        import core.move_generator as mg
        return mg.is_check(self, self.side_to_move)
    
    def is_terminal(self) -> bool:
        """Kết nối với kết thúc game để hỗ trợ Search cho Khánh"""
        import core.move_generator as mg
        return mg.is_terminal(self)