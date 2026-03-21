from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from agents.base_agent import Agent
from core.move import Move
from core.move_generator import assert_legal_move, get_winner, is_terminal, result_if_terminal
from core.rules import Color
from core.state import GameState


@dataclass(slots=True)
class TurnRecord:
    ply: int
    side: Color
    agent_name: str
    move: Optional[Move]


@dataclass(slots=True)
class GameLoopResult:
    final_state: GameState
    winner: Optional[Color]
    reason: str
    history: List[TurnRecord] = field(default_factory=list)


class GameLoop:
    """Game loop backend tối thiểu cho Human/Random/Search agents."""

    def __init__(
        self,
        red_agent: Agent,
        black_agent: Agent,
        state: Optional[GameState] = None,
        max_turns: int = 200,
    ) -> None:
        self.red_agent = red_agent
        self.black_agent = black_agent
        self.state = state.copy() if state is not None else GameState()
        self.max_turns = max_turns

    def current_agent(self) -> Agent:
        return self.red_agent if self.state.side_to_move == Color.RED else self.black_agent

    def play(self) -> GameLoopResult:
        history: list[TurnRecord] = []

        for ply in range(self.max_turns):
            terminal = result_if_terminal(self.state)
            if terminal is not None:
                return GameLoopResult(
                    final_state=self.state,
                    winner=terminal.winner,
                    reason=terminal.reason,
                    history=history,
                )
            if is_terminal(self.state):
                return GameLoopResult(
                    final_state=self.state,
                    winner=get_winner(self.state),
                    reason="terminal_position",
                    history=history,
                )

            agent = self.current_agent()
            side = self.state.side_to_move
            move = agent.select_move(self.state.copy())
            history.append(
                TurnRecord(
                    ply=ply,
                    side=side,
                    agent_name=getattr(agent, "name", agent.__class__.__name__),
                    move=move,
                )
            )

            if move is None:
                return GameLoopResult(
                    final_state=self.state,
                    winner=side.other,
                    reason="no_move_returned",
                    history=history,
                )

            assert_legal_move(self.state, move)
            self.state.apply_move(move)

        return GameLoopResult(
            final_state=self.state,
            winner=None,
            reason="max_turns_reached",
            history=history,
        )


def run_game(
    red_agent: Agent,
    black_agent: Agent,
    state: Optional[GameState] = None,
    max_turns: int = 200,
) -> GameLoopResult:
    return GameLoop(red_agent=red_agent, black_agent=black_agent, state=state, max_turns=max_turns).play()
