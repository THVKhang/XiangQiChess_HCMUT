import random
import unittest
from dataclasses import dataclass, field
from typing import List, Optional

from agents.random_agent import RandomAgent
from core.move import Move
from core.move_generator import legal_moves
from core.rules import Color
from core.state import GameState
from game.game_loop import run_game


@dataclass(slots=True)
class ScriptedAgent:
    moves: List[Optional[Move]]
    name: str = "ScriptedAgent"
    seen_sides: List[Color] = field(default_factory=list)

    def select_move(self, state: GameState) -> Optional[Move]:
        self.seen_sides.append(state.side_to_move)
        return self.moves.pop(0) if self.moves else None


class TestGameLoop(unittest.TestCase):
    def test_game_loop_calls_agents_by_turn(self):
        state = GameState()
        red_move = Move((6, 0), (5, 0))
        black_move = Move((3, 0), (4, 0))
        red_agent = ScriptedAgent([red_move, None], name="RedScript")
        black_agent = ScriptedAgent([black_move], name="BlackScript")

        result = run_game(red_agent, black_agent, state=state, max_turns=3)

        self.assertEqual(red_agent.seen_sides[0], Color.RED)
        self.assertEqual(black_agent.seen_sides[0], Color.BLACK)
        self.assertEqual(result.reason, "no_move_returned")
        self.assertEqual(len(result.history), 3)
        self.assertEqual(result.final_state.side_to_move, Color.RED)

    def test_random_vs_random_runs_without_crashing(self):
        result = run_game(
            RandomAgent(rng=random.Random(1)),
            RandomAgent(rng=random.Random(2)),
            max_turns=6,
        )

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(len(result.history), 6)
        self.assertIn(result.final_state.side_to_move, {Color.RED, Color.BLACK})

    def test_illegal_move_raises(self):
        red_agent = ScriptedAgent([Move((9, 0), (9, 1))])
        black_agent = ScriptedAgent([None])

        with self.assertRaises(ValueError):
            run_game(red_agent, black_agent, max_turns=1)

    def test_game_loop_applies_moves_to_state(self):
        state = GameState()
        red_move = legal_moves(state)[0]
        black_state = state.copy()
        black_state.apply_move(red_move)
        black_move = legal_moves(black_state)[0]

        result = run_game(ScriptedAgent([red_move]), ScriptedAgent([black_move]), state=state, max_turns=2)

        self.assertEqual(len(result.final_state.move_history), 2)
        self.assertEqual(result.reason, "max_turns_reached")
