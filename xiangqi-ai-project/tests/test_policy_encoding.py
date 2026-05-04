import unittest

from core.move import Move
from core.policy_encoding import (
    BOARD_SQUARES,
    POLICY_FLAT_LEN,
    canonical_move_to_policy_index,
    canonical_square,
    move_to_policy_index,
    square_index,
)
from core.rules import Color


class TestPolicyEncoding(unittest.TestCase):
    def test_square_and_policy_sizes_match_board_rules(self):
        self.assertEqual(BOARD_SQUARES, 90)
        self.assertEqual(POLICY_FLAT_LEN, 90 * 90)

    def test_move_roundtrip_index_monotonic(self):
        mv = Move((0, 0), (9, 8))
        idx = move_to_policy_index(mv)
        self.assertEqual(idx, square_index((0, 0)) * BOARD_SQUARES + square_index((9, 8)))

    def test_canonical_black_matches_tensor_flip(self):
        mv = Move((9, 4), (8, 4))
        # Đen đi: canonicalSquare giống encoding xoay 180°.
        self.assertEqual(canonical_square((9, 4), Color.BLACK), (0, 4))
        self.assertEqual(canonical_square((8, 4), Color.BLACK), (1, 4))
        i0 = canonical_move_to_policy_index(mv, Color.BLACK)
        i1 = move_to_policy_index(Move((0, 4), (1, 4)))
        self.assertEqual(i0, i1)


if __name__ == "__main__":
    unittest.main()
