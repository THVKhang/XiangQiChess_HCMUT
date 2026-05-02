from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from core.move import Move
from core.move_generator import assert_legal_move, get_winner, is_terminal, result_if_terminal
from core.rules import Color
from core.state import GameState


class AgentLike(Protocol):
    """Minimal interface shared by Human, Random, Search, and ML agents."""

    name: str
    player_id: Color

    def select_move(self, state: GameState) -> Optional[Move]:
        ...


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
    """Pure backend engine for XiangQi matches.

    This class intentionally has **no pygame/UI dependency**. UI mode, evaluation,
    and training/inference experiments can all reuse the same turn execution path:

    1. choose the current agent from ``state.side_to_move``;
    2. pass a cloned state to the agent;
    3. validate the returned move with the rule engine;
    4. apply the move to the internal state;
    5. stop on terminal states, threefold repetition, no-move, or max turns.

    ``play()`` is convenient for fully hidden/headless matches.
    ``step()`` is useful when a UI wants to advance exactly one AI turn while still
    delegating move validation and terminal checks to the same backend loop.
    """

    def __init__(
        self,
        red_agent: AgentLike,
        black_agent: AgentLike,
        state: Optional[GameState] = None,
        max_turns: int = 200,
    ) -> None:
        if max_turns <= 0:
            raise ValueError("max_turns must be positive")
        if red_agent.player_id != Color.RED:
            raise ValueError("red_agent.player_id must be Color.RED")
        if black_agent.player_id != Color.BLACK:
            raise ValueError("black_agent.player_id must be Color.BLACK")

        self.red_agent = red_agent
        self.black_agent = black_agent
        self.state = state.clone() if state is not None else GameState()
        self.max_turns = max_turns
        self.history: list[TurnRecord] = []
        self._position_counts: dict[
            tuple[str, tuple[tuple[tuple[int, int], str, str], ...]], int
        ] = {self._position_key(): 1}
        self._finished_result: Optional[GameLoopResult] = None

    @property
    def ply_count(self) -> int:
        return len(self.history)

    def current_agent(self) -> AgentLike:
        return self.red_agent if self.state.side_to_move == Color.RED else self.black_agent

    def _position_key(self) -> tuple[str, tuple[tuple[tuple[int, int], str, str], ...]]:
        pieces: list[tuple[tuple[int, int], str, str]] = []
        for pos, piece in self.state.board.squares():
            if piece is None:
                continue
            pieces.append((pos, piece.color.value, piece.kind.value))
        pieces.sort()
        return self.state.side_to_move.value, tuple(pieces)

    def _build_result(self, winner: Optional[Color], reason: str) -> GameLoopResult:
        result = GameLoopResult(
            final_state=self.state,
            winner=winner,
            reason=reason,
            history=self.history.copy(),
        )
        self._finished_result = result
        return result

    def _terminal_result_if_any(self) -> Optional[GameLoopResult]:
        terminal = result_if_terminal(self.state)
        if terminal is not None:
            return self._build_result(winner=terminal.winner, reason=terminal.reason)

        # Kept for compatibility with older terminal logic in core.move_generator.
        if is_terminal(self.state):
            return self._build_result(winner=get_winner(self.state), reason="terminal_position")

        return None

    def step(self) -> Optional[GameLoopResult]:
        """Advance one backend turn.

        Returns:
            ``None`` if the match should continue; otherwise a ``GameLoopResult``.

        Raises:
            ValueError: if an agent returns an illegal move. This mirrors the old
            GameLoop behavior, making integration bugs fail loudly during tests.
        """
        if self._finished_result is not None:
            return self._finished_result

        terminal = self._terminal_result_if_any()
        if terminal is not None:
            return terminal

        if self.ply_count >= self.max_turns:
            return self._build_result(winner=None, reason="max_turns_reached")

        agent = self.current_agent()
        side = self.state.side_to_move
        move = agent.select_move(self.state.clone())
        self.history.append(TurnRecord(ply=self.ply_count, side=side, agent_name=agent.name, move=move))

        if move is None:
            return self._build_result(winner=side.other, reason="no_move_returned")

        assert_legal_move(self.state, move)
        self.state.apply_move(move)

        key = self._position_key()
        self._position_counts[key] = self._position_counts.get(key, 0) + 1
        if self._position_counts[key] >= 3:
            return self._build_result(winner=None, reason="threefold_repetition")

        terminal = self._terminal_result_if_any()
        if terminal is not None:
            return terminal

        if self.ply_count >= self.max_turns:
            return self._build_result(winner=None, reason="max_turns_reached")

        return None

    def play(self) -> GameLoopResult:
        """Run a complete hidden/headless match until a stop condition is met."""
        while True:
            result = self.step()
            if result is not None:
                return result


def run_game(
    red_agent: AgentLike,
    black_agent: AgentLike,
    state: Optional[GameState] = None,
    max_turns: int = 200,
) -> GameLoopResult:
    """Backward-compatible helper for running one complete backend match."""
    return GameLoop(red_agent=red_agent, black_agent=black_agent, state=state, max_turns=max_turns).play()


def run_headless_game(
    red_agent: AgentLike,
    black_agent: AgentLike,
    state: Optional[GameState] = None,
    max_turns: int = 200,
) -> GameLoopResult:
    """Explicit Week 2 alias: run a match without pygame/UI."""
    return run_game(red_agent=red_agent, black_agent=black_agent, state=state, max_turns=max_turns)
