import unittest
from core.state import GameState
from core.move import Move
from core.board import Board
from core.rules import Color, Piece, PieceType

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.state = GameState()

    def test_initial_setup(self):
        red_rook = self.state.board.get((9, 0))
        self.assertIsNotNone(red_rook)
        self.assertEqual(red_rook.color, Color.RED)
        self.assertEqual(red_rook.kind, PieceType.ROOK)
        self.assertEqual(self.state.side_to_move, Color.RED)

    def test_apply_move_logic(self):
        src, dst = (6, 0), (5, 0)
        move = Move(src=src, dst=dst)
        self.state.apply_move(move)
        self.assertIsNone(self.state.board.get(src))
        self.assertEqual(self.state.board.get(dst).kind, PieceType.SOLDIER)
        self.assertEqual(self.state.side_to_move, Color.BLACK)

    def test_undo_move_logic(self):
        src, dst = (9, 0), (0, 0) 
        captured_piece = self.state.board.get(dst)
        move = Move(src=src, dst=dst, capture=captured_piece)
        undo_data = self.state.apply_move(move)
        self.state.undo_move(undo_data)
        self.assertIsNotNone(self.state.board.get(src))
        self.assertEqual(self.state.board.get(dst), captured_piece)
        self.assertEqual(self.state.side_to_move, Color.RED)

    def test_clone_independence(self):
        cloned_state = self.state.clone()
        cloned_state.board.set((9, 4), None) 
        self.assertIsNotNone(self.state.board.get((9, 4)))
        self.assertIsNone(cloned_state.board.get((9, 4)))

    def test_game_over_checkmate(self):
        self.state.board = Board.empty()
        self.state.board.set((9, 4), Piece(Color.RED, PieceType.GENERAL))
        self.state.board.set((9, 0), Piece(Color.BLACK, PieceType.ROOK)) 
        self.state.board.set((0, 4), Piece(Color.BLACK, PieceType.ROOK)) 
        self.state.side_to_move = Color.RED
        self.assertTrue(self.state.is_terminal())
        self.assertEqual(len(self.state.get_legal_moves()), 0)


    def test_apply_undo_consistency(self):
        """Hỗ trợ test: Đảm bảo dữ liệu đồng nhất sau chuỗi hành động thay đổi lượt"""
        initial_repr = repr(self.state.board)
        undos = []
        
        # Thực hiện 3 nước đi, mỗi bước đều lấy nước đi hợp lệ mới nhất
        for _ in range(3):
            moves = self.state.get_legal_moves()
            if not moves: break
            # Luôn chọn nước đi đầu tiên của phe đang đến lượt
            undo = self.state.apply_move(moves[0])
            undos.append(undo)
            
        # Hoàn tác toàn bộ theo thứ tự ngược lại
        for u in reversed(undos):
            self.state.undo_move(u)
            
        # Bàn cờ phải quay về trạng thái gốc 100%
        self.assertEqual(repr(self.state.board), initial_repr)

    def test_ai_search_compatibility(self):
        cloned = self.state.clone()
        for _ in range(10): # Mô phỏng AI duyệt sâu
            moves = cloned.get_legal_moves()
            if not moves: break
            move = moves[0]
            undo = cloned.apply_move(move)
            cloned.undo_move(undo)
        self.assertEqual(cloned.side_to_move, self.state.side_to_move)
    def test_continuous_game_simulation(self):
        """Test liên tục nhiều ván: Mô phỏng 50 nước đi ngẫu nhiên"""
        initial_state = self.state.clone()
        
        # Chạy vòng lặp mô phỏng nước đi liên tục
        for i in range(50):
            moves = self.state.get_legal_moves()
            if not moves:
                break
                
            # Chọn nước đi đầu tiên để đảm bảo tính ổn định của test
            move = moves[0]
            self.state.apply_move(move)
            
            # Kiểm tra: Sau mỗi nước đi, lượt phải đổi
            expected_color = Color.BLACK if (i % 2 == 0) else Color.RED
            self.assertEqual(self.state.side_to_move, expected_color)
            
        # Kiểm tra lịch sử nước đi có khớp với số lượt đã đi không
        self.assertLessEqual(len(self.state.move_history), 50)
if __name__ == '__main__':
    unittest.main()