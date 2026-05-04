"""Kiểm tra đếm vị trí lặp khớp GameLoop và phạt lặp trong MLAgent."""

import unittest

from agents.ml_agent import DummyMoveScoringModel, MLAgent
from core.move_generator import legal_moves
from core.rules import Color
from core.state import GameState
from game.repetition import cumulative_position_visit_counts, game_loop_position_key


class TestRepetitionHelpers(unittest.TestCase):
    def test_initial_position_count_is_one(self):
        state = GameState()
        counts = cumulative_position_visit_counts(state)
        self.assertEqual(counts[game_loop_position_key(GameState())], 1)
        self.assertEqual(len(counts), 1)

    def test_counts_accumulate_after_moves(self):
        state = GameState()
        mv = legal_moves(state)[0]
        state.apply_move(mv)
        counts = cumulative_position_visit_counts(state)
        self.assertGreater(len(counts), 1)
        self.assertGreaterEqual(sum(counts.values()), 2)


class TestMLRepetitionPenalties(unittest.TestCase):
    def test_ml_move_scores_same_length_as_legal_moves(self):
        agent = MLAgent(player_id=Color.RED, model=DummyMoveScoringModel())
        state = GameState()
        pairs = agent.get_legal_move_scores(state)
        self.assertEqual(len(pairs), len(legal_moves(state)))

    def test_disable_repetition_heuristics_leaves_policy_only(self):
        agent_on = MLAgent(player_id=Color.RED, model=DummyMoveScoringModel(), apply_repetition_heuristics=True)
        agent_off = MLAgent(player_id=Color.RED, model=DummyMoveScoringModel(), apply_repetition_heuristics=False)
        state = GameState()
        d_on = dict(agent_on.get_legal_move_scores(state))
        d_off = dict(agent_off.get_legal_move_scores(state))
        self.assertEqual(set(d_on.keys()), set(d_off.keys()))
        # Mở đầu ván: thường không có backtrack/threefold → điểm trùng nhau.
        for mv in d_off:
            self.assertAlmostEqual(d_on[mv], d_off[mv], places=5)


if __name__ == "__main__":
    unittest.main()
