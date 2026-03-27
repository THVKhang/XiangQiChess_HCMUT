import random
import unittest

from core.board import Board
from core.move import Move
from core.move_generator import (
    assert_legal_move,
    get_winner,
    is_check,
    is_legal_move,
    is_terminal,
    legal_moves,
)
from core.rules import Color, Piece, PieceType
from core.state import GameState


def mk_state(side: Color = Color.RED, *, blocker_pos=(4, 4)) -> GameState:
    s = GameState(board=Board.empty(), side_to_move=side)
    # Luôn đặt đủ 2 tướng để trạng thái không bị coi là terminal.
    s.board.set((9, 4), Piece(Color.RED, PieceType.GENERAL))
    s.board.set((0, 4), Piece(Color.BLACK, PieceType.GENERAL))
    # Luôn có 1 quân chắn để không bị "tướng đối mặt"/chiếu ngay từ đầu.
    if blocker_pos is not None:
        s.board.set(blocker_pos, Piece(Color.RED, PieceType.SOLDIER))
    return s


def moves_as_tuples(moves):
    return {(m.src, m.dst) for m in moves}


class TestRookHorse(unittest.TestCase):
    def test_rook_block_and_capture(self):
        s = mk_state(Color.RED, blocker_pos=(1, 4))
        s.board.set((5, 4), Piece(Color.RED, PieceType.ROOK))
        s.board.set((5, 6), Piece(Color.RED, PieceType.SOLDIER))  # block to the right
        s.board.set((2, 4), Piece(Color.BLACK, PieceType.SOLDIER))  # capturable upward
        ms = legal_moves(s)
        t = moves_as_tuples(ms)

        # rook can go up until capture at (2,4) but not beyond
        self.assertIn(((5, 4), (4, 4)), t)
        self.assertIn(((5, 4), (3, 4)), t)
        self.assertIn(((5, 4), (2, 4)), t)
        self.assertNotIn(((5, 4), (1, 4)), t)

        # rook cannot move onto own piece, nor beyond it
        self.assertNotIn(((5, 4), (5, 6)), t)
        self.assertNotIn(((5, 4), (5, 7)), t)

    def test_horse_leg_block(self):
        s = mk_state(Color.RED)
        s.board.set((5, 4), Piece(Color.RED, PieceType.HORSE))
        # block the leg for (-2, -1) and (-2, +1): leg is (4,4)
        s.board.set((4, 4), Piece(Color.RED, PieceType.SOLDIER))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)

        self.assertNotIn(((5, 4), (3, 3)), t)
        self.assertNotIn(((5, 4), (3, 5)), t)
        # still can go to other L moves (if in bounds)
        self.assertIn(((5, 4), (6, 2)), t)
        self.assertIn(((5, 4), (4, 2)), t)


class TestGeneralAdvisor(unittest.TestCase):
    def test_general_stays_in_palace(self):
        s = mk_state(Color.RED)
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((9, 4), (8, 4)), t)
        self.assertIn(((9, 4), (9, 3)), t)
        self.assertIn(((9, 4), (9, 5)), t)
        self.assertNotIn(((9, 4), (9, 6)), t)
        self.assertNotIn(((9, 4), (7, 4)), t)

    def test_advisor_diagonal_in_palace(self):
        s = mk_state(Color.RED)
        s.board.set((9, 3), Piece(Color.RED, PieceType.ADVISOR))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((9, 3), (8, 4)), t)
        self.assertNotIn(((9, 3), (9, 4)), t)  # cannot move orthogonal
        self.assertNotIn(((9, 3), (8, 2)), t)  # outside palace

    def test_facing_generals_is_illegal(self):
        # Two generals on same file with a blocking piece; moving it away is illegal.
        s = mk_state(Color.RED, blocker_pos=(5, 4))
        s.board.set((5, 4), Piece(Color.RED, PieceType.ROOK))  # screen (can move sideways)
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertNotIn(((5, 4), (5, 3)), t)  # would open facing generals


class TestElephantCannonSoldier(unittest.TestCase):
    def test_elephant_cannot_cross_river_and_eye_block(self):
        s = mk_state(Color.RED)
        s.board.set((9, 2), Piece(Color.RED, PieceType.ELEPHANT))
        # eye block for move to (7,4) is (8,3)
        s.board.set((8, 3), Piece(Color.RED, PieceType.SOLDIER))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertNotIn(((9, 2), (7, 4)), t)  # eye blocked
        self.assertIn(((9, 2), (7, 0)), t)  # other diagonal ok

        # place elephant near river; crossing should be disallowed
        s2 = mk_state(Color.RED)
        s2.board.set((5, 2), Piece(Color.RED, PieceType.ELEPHANT))
        ms2 = legal_moves(s2)
        t2 = moves_as_tuples(ms2)
        self.assertNotIn(((5, 2), (3, 4)), t2)  # would cross river

    def test_cannon_capture_requires_one_screen(self):
        s = mk_state(Color.RED)
        s.board.set((7, 1), Piece(Color.RED, PieceType.CANNON))
        s.board.set((5, 1), Piece(Color.RED, PieceType.SOLDIER))  # screen
        s.board.set((3, 1), Piece(Color.BLACK, PieceType.ROOK))  # target
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((7, 1), (3, 1)), t)  # capture ok
        self.assertNotIn(((7, 1), (2, 1)), t)  # cannot go past captured piece

        # without screen, capture should be illegal
        s2 = mk_state(Color.RED)
        s2.board.set((7, 1), Piece(Color.RED, PieceType.CANNON))
        s2.board.set((3, 1), Piece(Color.BLACK, PieceType.ROOK))
        ms2 = legal_moves(s2)
        t2 = moves_as_tuples(ms2)
        self.assertNotIn(((7, 1), (3, 1)), t2)

    def test_soldier_forward_then_sideways_after_river(self):
        s = mk_state(Color.RED, blocker_pos=(2, 4))
        s.board.set((6, 4), Piece(Color.RED, PieceType.SOLDIER))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((6, 4), (5, 4)), t)
        self.assertNotIn(((6, 4), (6, 3)), t)
        self.assertNotIn(((6, 4), (6, 5)), t)

        s2 = mk_state(Color.RED, blocker_pos=(2, 4))
        s2.board.set((4, 4), Piece(Color.RED, PieceType.SOLDIER))  # crossed river already
        ms2 = legal_moves(s2)
        t2 = moves_as_tuples(ms2)
        self.assertIn(((4, 4), (3, 4)), t2)
        self.assertIn(((4, 4), (4, 3)), t2)
        self.assertIn(((4, 4), (4, 5)), t2)
        self.assertNotIn(((4, 4), (5, 4)), t2)  # cannot go backward


class TestTerminalWinner(unittest.TestCase):
    def test_not_terminal_in_normal_state(self):
        s = mk_state(Color.RED)
        self.assertFalse(is_terminal(s))
        self.assertIsNone(get_winner(s))

    def test_terminal_when_general_missing(self):
        s = GameState(board=Board.empty(), side_to_move=Color.RED)
        # Only keep black general -> red has "lost general"
        s.board.set((0, 4), Piece(Color.BLACK, PieceType.GENERAL))
        self.assertTrue(is_terminal(s))
        self.assertEqual(get_winner(s), Color.BLACK)


class TestIllegalMoveValidation(unittest.TestCase):
    def test_reject_move_to_own_piece(self):
        s = mk_state(Color.RED, blocker_pos=(2, 4))
        s.board.set((5, 4), Piece(Color.RED, PieceType.ROOK))
        s.board.set((5, 5), Piece(Color.RED, PieceType.SOLDIER))
        mv = (5, 4), (5, 5)
        self.assertFalse(is_legal_move(s, Move(*mv)))
        with self.assertRaises(ValueError):
            assert_legal_move(s, Move(*mv))


class TestBasicCheck(unittest.TestCase):
    def test_rook_gives_check(self):
        s = mk_state(Color.RED, blocker_pos=None)
        # Black rook on same file, unobstructed -> red is in check.
        s.board.set((5, 4), Piece(Color.BLACK, PieceType.ROOK))
        self.assertTrue(is_check(s, Color.RED))

    def test_cannon_gives_check_with_one_screen(self):
        s = mk_state(Color.RED, blocker_pos=None)
        s.board.set((5, 4), Piece(Color.BLACK, PieceType.CANNON))
        s.board.set((7, 4), Piece(Color.RED, PieceType.SOLDIER))  # screen
        self.assertTrue(is_check(s, Color.RED))

    def test_horse_gives_check_if_leg_free(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        # Put black horse so that it attacks (9,4): from (7,3) -> (9,4) with leg at (8,3)
        s.board.set((7, 3), Piece(Color.BLACK, PieceType.HORSE))
        self.assertTrue(is_check(s, Color.RED))

        # Block the leg -> no check.
        s2 = mk_state(Color.RED, blocker_pos=(4, 4))
        s2.board.set((7, 3), Piece(Color.BLACK, PieceType.HORSE))
        s2.board.set((8, 3), Piece(Color.RED, PieceType.SOLDIER))  # leg block
        self.assertFalse(is_check(s2, Color.RED))

    def test_soldier_gives_check_forward(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        s.board.set((8, 4), Piece(Color.BLACK, PieceType.SOLDIER))
        self.assertTrue(is_check(s, Color.RED))

    def test_facing_generals_counts_as_check(self):
        s = mk_state(Color.RED, blocker_pos=None)
        self.assertTrue(is_check(s, Color.RED))
        self.assertTrue(is_check(s, Color.BLACK))


class TestLongRunRules(unittest.TestCase):
    def test_random_play_does_not_break_invariants(self):
        rng = random.Random(20260327)
        s = GameState()  # initial setup

        for _ in range(400):
            # Nếu terminal thì dừng (checkmate/stalemate hoặc mất tướng).
            if is_terminal(s) or get_winner(s) is not None:
                break

            ms = legal_moves(s)
            self.assertTrue(ms, "Non-terminal state must have legal moves")

            m = rng.choice(ms)
            assert_legal_move(s, Move(m.src, m.dst, capture=m.capture))

            undo = s.apply_move(m)

            # Sau khi đi xong, trạng thái không được là illegal (tự chiếu / tướng đối mặt).
            self.assertFalse(is_check(s, s.side_to_move.other), "Move must not leave mover in check")

            # Thỉnh thoảng undo để kiểm tra tính ổn định khi chạy dài.
            if rng.random() < 0.1:
                s.undo_move(undo)


class TestLegalMoveFiltering(unittest.TestCase):
    def test_move_exposing_check_is_filtered(self):
        # Red rook is pinned: moving it away would expose check from black rook.
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        s.board.set((9, 8), Piece(Color.BLACK, PieceType.ROOK))
        s.board.set((9, 6), Piece(Color.RED, PieceType.ROOK))  # pinned blocker

        ms = legal_moves(s)
        t = moves_as_tuples(ms)

        # Moving the pinned rook off row 9 would expose red general -> illegal.
        self.assertNotIn(((9, 6), (8, 6)), t)
        self.assertNotIn(((9, 6), (7, 6)), t)

    def test_flying_general_capture_when_clear(self):
        # Two generals face each other with empty file: capture should be a legal move.
        s = GameState(board=Board.empty(), side_to_move=Color.RED)
        s.board.set((9, 4), Piece(Color.RED, PieceType.GENERAL))
        s.board.set((0, 4), Piece(Color.BLACK, PieceType.GENERAL))

        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((9, 4), (0, 4)), t)


class TestEachPieceRules(unittest.TestCase):
    def test_rook_cannot_jump(self):
        s = mk_state(Color.RED, blocker_pos=(1, 4))
        s.board.set((5, 0), Piece(Color.RED, PieceType.ROOK))
        s.board.set((5, 2), Piece(Color.RED, PieceType.SOLDIER))  # block
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((5, 0), (5, 1)), t)
        self.assertNotIn(((5, 0), (5, 3)), t)

    def test_horse_can_capture_when_leg_free(self):
        # Ensure leg squares are free (do not block at (4,4)),
        # and keep file 4 blocked so moving the horse doesn't open facing generals.
        s = mk_state(Color.RED, blocker_pos=(6, 4))
        s.board.set((5, 4), Piece(Color.RED, PieceType.HORSE))
        s.board.set((3, 3), Piece(Color.BLACK, PieceType.SOLDIER))  # capturable
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((5, 4), (3, 3)), t)

    def test_elephant_can_capture_and_cannot_cross_river(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        s.board.set((9, 2), Piece(Color.RED, PieceType.ELEPHANT))
        s.board.set((7, 4), Piece(Color.BLACK, PieceType.SOLDIER))  # capturable
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((9, 2), (7, 4)), t)

        s2 = mk_state(Color.RED, blocker_pos=(4, 4))
        s2.board.set((5, 2), Piece(Color.RED, PieceType.ELEPHANT))
        ms2 = legal_moves(s2)
        t2 = moves_as_tuples(ms2)
        self.assertNotIn(((5, 2), (3, 4)), t2)  # would cross river

    def test_advisor_only_diagonal_and_stays_in_palace(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        s.board.set((8, 4), Piece(Color.RED, PieceType.ADVISOR))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertIn(((8, 4), (9, 3)), t)
        self.assertIn(((8, 4), (9, 5)), t)
        self.assertNotIn(((8, 4), (8, 5)), t)  # orthogonal
        self.assertNotIn(((8, 4), (7, 2)), t)  # outside palace

    def test_general_cannot_leave_palace(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        # Put general at (7,4) is inside palace, moving to (6,4) would leave palace -> illegal
        s.board.set((9, 4), None)
        s.board.set((7, 4), Piece(Color.RED, PieceType.GENERAL))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertNotIn(((7, 4), (6, 4)), t)

    def test_cannon_capture_requires_exactly_one_screen(self):
        s = mk_state(Color.RED, blocker_pos=(4, 4))
        s.board.set((7, 1), Piece(Color.RED, PieceType.CANNON))
        s.board.set((6, 1), Piece(Color.RED, PieceType.SOLDIER))  # screen 1
        s.board.set((5, 1), Piece(Color.BLACK, PieceType.SOLDIER))  # screen 2 (extra)
        s.board.set((3, 1), Piece(Color.BLACK, PieceType.ROOK))  # target
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertNotIn(((7, 1), (3, 1)), t)  # 2 screens => cannot capture

    def test_soldier_cannot_move_backward(self):
        s = mk_state(Color.RED, blocker_pos=(2, 4))
        s.board.set((4, 4), Piece(Color.RED, PieceType.SOLDIER))
        ms = legal_moves(s)
        t = moves_as_tuples(ms)
        self.assertNotIn(((4, 4), (5, 4)), t)


if __name__ == "__main__":
    unittest.main()

