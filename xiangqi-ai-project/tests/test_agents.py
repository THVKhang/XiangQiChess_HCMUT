import unittest

from agents.search_agent import EasyAgent, HardAgent, LevelAgent, MediumAgent
from core.move_generator import is_legal_move
from core.rules import Color
from core.state import GameState


class TestSearchAgents(unittest.TestCase):
    def setUp(self):
        self.state = GameState()

    def test_easy_agent_returns_legal_move(self):
        agent = EasyAgent(player_id=Color.RED, algorithm="alphabeta")
        move = agent.select_move(self.state.clone())
        self.assertIsNotNone(move)
        self.assertTrue(is_legal_move(self.state, move))

    def test_medium_agent_returns_legal_move(self):
        agent = MediumAgent(player_id=Color.RED, algorithm="alphabeta")
        move = agent.select_move(self.state.clone())
        self.assertIsNotNone(move)
        self.assertTrue(is_legal_move(self.state, move))

    def test_hard_agent_returns_legal_move(self):
        agent = HardAgent(player_id=Color.RED, algorithm="alphabeta")
        move = agent.select_move(self.state.clone())
        self.assertIsNotNone(move)
        self.assertTrue(is_legal_move(self.state, move))

    def test_minimax_mode_returns_legal_move(self):
        agent = LevelAgent(player_id=Color.RED, algorithm="minimax", level=3)
        move = agent.select_move(self.state.clone())
        self.assertIsNotNone(move)
        self.assertTrue(is_legal_move(self.state, move))

    def test_level_range_returns_legal_move(self):
        for lvl in [1, 4, 8, 10]:
            with self.subTest(level=lvl):
                agent = LevelAgent(player_id=Color.RED, algorithm="alphabeta", level=lvl)
                move = agent.select_move(self.state.clone())
                self.assertIsNotNone(move)
                self.assertTrue(is_legal_move(self.state, move))


if __name__ == "__main__":
    unittest.main()
