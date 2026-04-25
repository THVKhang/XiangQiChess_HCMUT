import unittest

from core.encoding import state_to_tensor
from core.rules import Color, PieceType
from core.state import GameState
from core.move import Move
from core.encoding import game_to_tensor_sequence


class TestEncoding(unittest.TestCase):
    def test_state_to_tensor_shape_channels_first(self):
        st = GameState()
        x = state_to_tensor(st, channels_first=True, canonical=False, as_numpy=False)
        self.assertEqual(len(x), 15)
        self.assertEqual(len(x[0]), 10)
        self.assertEqual(len(x[0][0]), 9)

    def test_initial_positions_some_spots(self):
        st = GameState()
        x = state_to_tensor(st, channels_first=True, canonical=False, as_numpy=False)

        # side-to-move is RED initially
        self.assertEqual(x[14][0][0], 1.0)
        self.assertEqual(x[14][9][8], 1.0)

        # Red rook at (9,0) -> channel red rook = 4
        self.assertEqual(x[4][9][0], 1.0)

        # Black general at (0,4) -> channel black general = 7
        self.assertEqual(x[7][0][4], 1.0)

        # Red soldiers at row 6, cols 0,2,4,6,8 -> channel red soldier = 6
        for c in (0, 2, 4, 6, 8):
            self.assertEqual(x[6][6][c], 1.0)

    def test_canonical_flips_when_black_to_move(self):
        st = GameState()
        st.side_to_move = Color.BLACK

        # In canonical view, current player becomes "red" and board is rotated.
        x = state_to_tensor(st, channels_first=True, canonical=True, as_numpy=False)

        # side plane becomes constant 1.0
        self.assertEqual(x[14][0][0], 1.0)
        self.assertEqual(x[14][9][8], 1.0)

        # Original black general at (0,4) should appear as red general at flipped (9,4) -> channel red general = 0
        self.assertEqual(x[0][9][4], 1.0)

    def test_game_to_tensor_sequence_length(self):
        st = GameState()
        # two legal-ish opening moves (soldier up), we don't validate legality here beyond engine apply_move
        moves = [Move((6, 0), (5, 0)), Move((3, 0), (4, 0))]
        seq = game_to_tensor_sequence(st, moves, include_initial=True, include_final=True, as_numpy=False)
        self.assertEqual(len(seq), 3)


if __name__ == "__main__":
    unittest.main()

