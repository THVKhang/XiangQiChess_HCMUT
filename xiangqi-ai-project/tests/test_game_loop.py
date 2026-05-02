import random
import unittest
from dataclasses import dataclass, field
from typing import List, Optional

from agents.human_player import HumanPlayer
from agents.ml_agent import DummyMoveScoringModel, MLAgent
from agents.random_agent import RandomAgent
from core.move import Move
from core.move_generator import legal_moves
from core.rules import Color
from core.state import GameState
from game.game_loop import GameLoop, run_game


@dataclass(slots=True)
class ScriptedAgent:
    player_id: Color
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
        red_agent = ScriptedAgent(player_id=Color.RED, moves=[red_move, None], name="RedScript")
        black_agent = ScriptedAgent(player_id=Color.BLACK, moves=[black_move], name="BlackScript")

        result = run_game(red_agent, black_agent, state=state, max_turns=3)

        self.assertEqual(red_agent.seen_sides[0], Color.RED)
        self.assertEqual(black_agent.seen_sides[0], Color.BLACK)
        self.assertEqual(result.reason, "no_move_returned")
        self.assertEqual(len(result.history), 3)
        self.assertEqual(result.final_state.side_to_move, Color.RED)

    def test_random_vs_random_runs_without_crashing(self):
        result = run_game(
            RandomAgent(player_id=Color.RED, rng=random.Random(1)),
            RandomAgent(player_id=Color.BLACK, rng=random.Random(2)),
            max_turns=6,
        )

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(len(result.history), 6)
        self.assertIn(result.final_state.side_to_move, {Color.RED, Color.BLACK})

    def test_illegal_move_raises(self):
        red_agent = ScriptedAgent(player_id=Color.RED, moves=[Move((9, 4), (8, 6))])
        black_agent = ScriptedAgent(player_id=Color.BLACK, moves=[None])

        with self.assertRaises(ValueError):
            run_game(red_agent, black_agent, max_turns=1)

    def test_game_loop_applies_moves_to_state(self):
        state = GameState()
        red_move = legal_moves(state)[0]
        black_state = state.clone()
        black_state.apply_move(red_move)
        black_move = legal_moves(black_state)[0]

        result = run_game(
            ScriptedAgent(player_id=Color.RED, moves=[red_move]),
            ScriptedAgent(player_id=Color.BLACK, moves=[black_move]),
            state=state,
            max_turns=2,
        )

        self.assertEqual(len(result.final_state.move_history), 2)
        self.assertEqual(result.reason, "max_turns_reached")

    def test_human_player_retries_until_legal_move(self):
        prompts: list[str] = []
        outputs: list[str] = []
        scripted_inputs = iter([
            "bad input",
            "9 4 8 6",
            "6 0 5 0",
        ])

        human = HumanPlayer(
            player_id=Color.RED,
            input_func=lambda prompt: prompts.append(prompt) or next(scripted_inputs),
            output_func=outputs.append,
        )

        move = human.select_move(GameState())

        self.assertEqual(move, Move((6, 0), (5, 0)))
        self.assertEqual(len(prompts), 3)
        self.assertTrue(any("exactly 4 integers" in message for message in outputs))
        self.assertTrue(any("Illegal move" in message for message in outputs))

    def test_human_vs_ai_mode_runs(self):
        scripted_inputs = iter(["6 0 5 0"])
        human = HumanPlayer(
            player_id=Color.RED,
            input_func=lambda _prompt: next(scripted_inputs),
            output_func=lambda _message: None,
        )
        ai = ScriptedAgent(player_id=Color.BLACK, moves=[Move((3, 0), (4, 0))], name="EasyAI")

        result = run_game(human, ai, max_turns=2)

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(len(result.history), 2)
        self.assertEqual(result.history[0].agent_name, "HumanPlayer")
        self.assertEqual(result.history[1].agent_name, "EasyAI")

    def test_ai_vs_random_mode_runs(self):
        ai = ScriptedAgent(player_id=Color.RED, moves=[Move((6, 0), (5, 0))], name="EasyAI")
        random_agent = RandomAgent(player_id=Color.BLACK, rng=random.Random(7))

        result = run_game(ai, random_agent, max_turns=2)

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(result.history[0].agent_name, "EasyAI")
        self.assertEqual(result.history[1].agent_name, "RandomAgent")

    def test_ai_vs_ai_mode_runs(self):
        red_ai = ScriptedAgent(player_id=Color.RED, moves=[Move((6, 0), (5, 0))], name="EasyAI")
        black_ai = ScriptedAgent(player_id=Color.BLACK, moves=[Move((3, 0), (4, 0))], name="MediumAI")

        result = run_game(red_ai, black_ai, max_turns=2)

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual([record.agent_name for record in result.history], ["EasyAI", "MediumAI"])

    def test_game_loop_current_agent_matches_side_to_move(self):
        loop = GameLoop(
            red_agent=ScriptedAgent(player_id=Color.RED, moves=[]),
            black_agent=ScriptedAgent(player_id=Color.BLACK, moves=[]),
        )
        self.assertEqual(loop.current_agent().player_id, Color.RED)

        loop.state.side_to_move = Color.BLACK
        self.assertEqual(loop.current_agent().player_id, Color.BLACK)


    def test_ml_agent_dummy_model_returns_legal_move(self):
        state = GameState()
        agent = MLAgent(player_id=Color.RED, model=DummyMoveScoringModel())

        move = agent.select_move(state)

        self.assertIn(move, legal_moves(state))

    def test_ml_agent_runs_inside_headless_game_loop(self):
        result = run_game(
            MLAgent(player_id=Color.RED, model=DummyMoveScoringModel()),
            RandomAgent(player_id=Color.BLACK, rng=random.Random(11)),
            max_turns=4,
        )

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(len(result.history), 4)
        self.assertEqual(result.history[0].agent_name, "MLAgent")

    def test_ml_agent_rejects_wrong_turn_color(self):
        agent = MLAgent(player_id=Color.BLACK, model=DummyMoveScoringModel())

        with self.assertRaises(ValueError):
            agent.select_move(GameState())


class TestHeadlessGameLoopWeek2(unittest.TestCase):
    def test_run_headless_game_alias_does_not_need_ui(self):
        from game.game_loop import run_headless_game

        result = run_headless_game(
            RandomAgent(player_id=Color.RED, rng=random.Random(21)),
            RandomAgent(player_id=Color.BLACK, rng=random.Random(22)),
            max_turns=3,
        )

        self.assertEqual(result.reason, "max_turns_reached")
        self.assertEqual(len(result.history), 3)

    def test_step_api_advances_one_hidden_turn(self):
        loop = GameLoop(
            red_agent=ScriptedAgent(player_id=Color.RED, moves=[Move((6, 0), (5, 0))], name="RedScript"),
            black_agent=ScriptedAgent(player_id=Color.BLACK, moves=[Move((3, 0), (4, 0))], name="BlackScript"),
            max_turns=2,
        )

        first_result = loop.step()
        self.assertIsNone(first_result)
        self.assertEqual(loop.ply_count, 1)
        self.assertEqual(loop.state.side_to_move, Color.BLACK)

        final_result = loop.step()
        self.assertIsNotNone(final_result)
        self.assertEqual(final_result.reason, "max_turns_reached")
        self.assertEqual(len(final_result.history), 2)

    def test_game_loop_backend_has_no_pygame_dependency(self):
        import game.game_loop as backend_loop

        self.assertFalse(hasattr(backend_loop, "pygame"))

    def test_headless_ml_vs_random_short_match(self):
        from evaluation.headless_match import run_ml_vs_random

        records = run_ml_vs_random(games=1, max_turns=1, seed=99)

        self.assertEqual(len(records), 1)
        self.assertTrue(all(record.red_agent == "MLAgent" for record in records))
        self.assertTrue(all(record.black_agent == "RandomAgent" for record in records))
        self.assertTrue(all(record.plies == 1 for record in records))

if __name__ == "__main__":
    unittest.main()
