import unittest
from core.state import GameState
from core.move import Move
from core.board import Board
from core.rules import Color, Piece, PieceType

class TestGameState(unittest.TestCase):
    def setUp(self):
        """Khởi tạo trạng thái ban đầu trước mỗi bài test"""
        self.state = GameState()

    def test_initial_setup(self):
        """Kiểm tra bàn cờ có xếp đúng vị trí quân cờ ban đầu không"""
        # Kiểm tra Xe đỏ ở góc dưới bên trái (hàng 9, cột 0)
        red_rook = self.state.board.get((9, 0))
        self.assertIsNotNone(red_rook)
        self.assertEqual(red_rook.color, Color.RED)
        self.assertEqual(red_rook.kind, PieceType.ROOK)
        
        # Kiểm tra lượt đi đầu tiên là phe Đỏ
        self.assertEqual(self.state.side_to_move, Color.RED)

    def test_apply_move_logic(self):
        """Kiểm tra logic di chuyển quân và đổi lượt"""
        # Giả định di chuyển Tốt đỏ (6, 0) tiến lên (5, 0)
        src, dst = (6, 0), (5, 0)
        move = Move(src=src, dst=dst)
        
        self.state.apply_move(move)
        
        # Kiểm tra quân đã đến vị trí mới và vị trí cũ trống
        self.assertIsNone(self.state.board.get(src))
        self.assertEqual(self.state.board.get(dst).kind, PieceType.SOLDIER)
        
        # Kiểm tra lượt đi đã đổi sang phe Đen
        self.assertEqual(self.state.side_to_move, Color.BLACK)

    def test_undo_move_logic(self):
        """Kiểm tra tính năng Undo có khôi phục đúng trạng thái cũ không"""
        # Thực hiện một nước đi ăn quân (giả định)
        src, dst = (9, 0), (0, 0) # Xe đỏ ăn Xe đen (test logic)
        captured_piece = self.state.board.get(dst)
        move = Move(src=src, dst=dst, capture=captured_piece)
        
        undo_data = self.state.apply_move(move)
        self.state.undo_move(undo_data)
        
        # Kiểm tra quân cờ trở về vị trí cũ
        self.assertIsNotNone(self.state.board.get(src))
        self.assertEqual(self.state.board.get(dst), captured_piece)
        
        # Kiểm tra lượt đi trở về phe Đỏ
        self.assertEqual(self.state.side_to_move, Color.RED)

    def test_clone_independence(self):
        """Kiểm tra hàm clone tạo ra bản sao độc lập hoàn toàn"""
        cloned_state = self.state.clone()
        
        # Thay đổi trên bản clone không được ảnh hưởng bản gốc
        cloned_state.board.set((9, 4), None) # Xóa tướng đỏ trên bản clone
        
        self.assertIsNotNone(self.state.board.get((9, 4)))
        self.assertIsNone(cloned_state.board.get((9, 4)))

    def test_is_terminal_not_triggered_by_facing_generals(self):
        s = GameState(board=Board.empty(), side_to_move=Color.RED)
        s.board.set((9, 4), Piece(Color.RED, PieceType.GENERAL))
        s.board.set((0, 4), Piece(Color.BLACK, PieceType.GENERAL))
        # "Tướng đối mặt" là trạng thái không hợp lệ, nhưng không phải terminal ở cấp GameState.
        self.assertFalse(s.is_terminal())

if __name__ == '__main__':
    unittest.main()
