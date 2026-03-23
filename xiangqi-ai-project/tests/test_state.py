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
    # tests/test_state.py

    def test_game_over_checkmate(self):
        """Khoa tự đảm bảo test case của mình phản ánh đúng trạng thái bí"""
        from core.board import Board
        from core.rules import Piece, Color, PieceType
        
        # Tạo thế cờ bí: Tướng đỏ (9,4) bị 2 xe đen khóa chặt
        self.state.board = Board.empty()
        self.state.board.set((9, 4), Piece(Color.RED, PieceType.GENERAL))
        self.state.board.set((9, 0), Piece(Color.BLACK, PieceType.ROOK)) # Chiếu ngang
        self.state.board.set((0, 4), Piece(Color.BLACK, PieceType.ROOK)) # Chiếu dọc
        self.state.side_to_move = Color.RED
        
        # Nếu hàm của Khoa trả về True, nghĩa là phần của Khoa đã đúng
        self.assertTrue(self.state.is_terminal())
        self.assertEqual(len(self.state.get_legal_moves()), 0)

    def test_ai_search_compatibility(self):
        """Test tích hợp: Đảm bảo AI của Khánh có thể sử dụng State của Khoa"""
        # Thử clone và apply move nhiều lần như cách AI hoạt động
        cloned = self.state.clone()
        moves = cloned.get_legal_moves()
        if moves:
            undo = cloned.apply_move(moves[0])
            self.assertNotEqual(cloned.side_to_move, self.state.side_to_move)
            cloned.undo_move(undo)
            # Sau khi undo, board của bản clone phải quay về trạng thái ban đầu
            self.assertEqual(cloned.board.get(moves[0].src), self.state.board.get(moves[0].src))

if __name__ == '__main__':
    unittest.main()
