import unittest
from core.move import Move
from core.rules import Color, Piece, PieceType

class TestMove(unittest.TestCase):
    def test_move_creation(self):
        """Kiểm tra khởi tạo nước đi cơ bản"""
        src, dst = (9, 0), (8, 0)
        move = Move(src=src, dst=dst)
        
        self.assertEqual(move.src, (9, 0))
        self.assertEqual(move.dst, (8, 0))
        self.assertFalse(move.is_capture())

    def test_move_with_capture(self):
        """Kiểm tra nước đi có ăn quân"""
        src, dst = (7, 1), (2, 1) # Pháo ăn quân
        captured_piece = Piece(Color.BLACK, PieceType.ROOK)
        move = Move(src=src, dst=dst, capture=captured_piece)
        
        self.assertTrue(move.is_capture())
        self.assertEqual(move.capture.kind, PieceType.ROOK)

    def test_move_unpacking(self):
        """Kiểm tra tính năng unpack: src, dst = move"""
        move = Move(src=(1, 2), dst=(3, 4))
        s, d = move
        self.assertEqual(s, (1, 2))
        self.assertEqual(d, (3, 4))

    def test_distance_calculation(self):
        """Kiểm tra tính toán khoảng cách di chuyển"""
        # Di chuyển 1 ô thẳng: (9,4) -> (8,4) => dist^2 = 1
        move1 = Move(src=(9, 4), dst=(8, 4))
        self.assertEqual(move1.distance_squared, 1)
        
        # Di chuyển quân Mã (chữ L): (9,1) -> (7,2) => dist^2 = 2^2 + 1^2 = 5
        move_horse = Move(src=(9, 1), dst=(7, 2))
        self.assertEqual(move_horse.distance_squared, 5)
    def test_multiple_move_properties(self):
        """Test liên tục: Kiểm tra tính đúng đắn của thuộc tính Move"""
        # Test nước đi của Xe (thẳng)
        rook_move = Move((9, 0), (7, 0))
        self.assertEqual(rook_move.distance_squared, 4)
        
        # Sửa PAWN thành SOLDIER để khớp với rules.py của Bảo
        cannon_cap = Move((7, 1), (2, 1), capture=Piece(Color.BLACK, PieceType.SOLDIER))
        self.assertTrue(cannon_cap.is_capture())
        
        # Đảm bảo Move không bị thay đổi dữ liệu sau khi khởi tạo (Frozen)
        with self.assertRaises(Exception):
            rook_move.src = (0, 0)    

if __name__ == '__main__':
    unittest.main()