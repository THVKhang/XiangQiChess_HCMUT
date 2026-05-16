from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.ml_agent import MLAgent
from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent, MediumAgent, HardAgent
from core.rules import Color
from game.game_loop import run_headless_game


@dataclass(slots=True)
class HeadlessMatchRecord:
    game_index: int
    red_agent: str
    black_agent: str
    winner: str
    reason: str
    plies: int
    elapsed_ms: int


def run_ml_vs_random(
    games: int = 10,
    max_turns: int = 160,
    seed: int = 2026,
    ml_level: str = "Hard",
) -> list[HeadlessMatchRecord]:
    """Run MLAgent vs RandomAgent fully hidden, without importing/starting UI."""
    records: list[HeadlessMatchRecord] = []
    for idx in range(1, games + 1):
        red_agent = MLAgent(player_id=Color.RED, level=ml_level)
        black_agent = RandomAgent(player_id=Color.BLACK, rng=random.Random(seed + idx))

        start = time.perf_counter()
        result = run_headless_game(red_agent, black_agent, max_turns=max_turns)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        records.append(
            HeadlessMatchRecord(
                game_index=idx,
                red_agent=red_agent.name,
                black_agent=black_agent.name,
                winner="draw" if result.winner is None else result.winner.value,
                reason=result.reason,
                plies=len(result.history),
                elapsed_ms=elapsed_ms,
            )
        )
    return records


_SEARCH_LEVEL_MAP = {"Easy": EasyAgent, "Medium": MediumAgent, "Hard": HardAgent}


def run_ml_vs_search(
    games: int = 10,
    max_turns: int = 160,
    seed: int = 2026,
    ml_level: str = "Hard",
    search_level: str = "Easy",
    search_algorithm: str = "minimax",
) -> list[HeadlessMatchRecord]:
    """Run MLAgent (Red) vs Search/Minimax agent (Black) fully hidden."""
    search_cls = _SEARCH_LEVEL_MAP.get(search_level, EasyAgent)
    records: list[HeadlessMatchRecord] = []
    for idx in range(1, games + 1):
        red_agent = MLAgent(player_id=Color.RED, level=ml_level)
        black_agent = search_cls(player_id=Color.BLACK, algorithm=search_algorithm)

        start = time.perf_counter()
        result = run_headless_game(red_agent, black_agent, max_turns=max_turns)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        records.append(
            HeadlessMatchRecord(
                game_index=idx,
                red_agent=red_agent.name,
                black_agent=black_agent.name,
                winner="draw" if result.winner is None else result.winner.value,
                reason=result.reason,
                plies=len(result.history),
                elapsed_ms=elapsed_ms,
            )
        )
    return records


def print_summary(records: list[HeadlessMatchRecord]) -> None:
    total = len(records)
    red_wins = sum(1 for r in records if r.winner == "red")
    black_wins = sum(1 for r in records if r.winner == "black")
    draws = sum(1 for r in records if r.winner == "draw")
    avg_ms = sum(r.elapsed_ms for r in records) / max(1, total)

    print("=== Headless ML vs Random Summary ===")
    print(f"Total games: {total}")
    print(f"ML/red wins : {red_wins}")
    print(f"Random wins : {black_wins}")
    print(f"Draws       : {draws}")
    print(f"Avg time    : {avg_ms:.1f} ms/game")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run hidden/headless matches (ML vs Random or ML vs Search).")
    parser.add_argument("--mode", choices=["ml-vs-random", "ml-vs-search"], default="ml-vs-random")
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=160)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--ml-level", choices=["Easy", "Medium", "Hard"], default="Hard")
    parser.add_argument("--search-level", choices=["Easy", "Medium", "Hard"], default="Easy")
    parser.add_argument("--search-algorithm", choices=["minimax", "alphabeta"], default="minimax")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "ml-vs-search":
        records = run_ml_vs_search(
            games=args.games,
            max_turns=args.max_turns,
            seed=args.seed,
            ml_level=args.ml_level,
            search_level=args.search_level,
            search_algorithm=args.search_algorithm,
        )
    else:
        records = run_ml_vs_random(
            games=args.games,
            max_turns=args.max_turns,
            seed=args.seed,
            ml_level=args.ml_level,
        )

    print_summary(records)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(r) for r in records]
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON saved: {args.json_out}")


if __name__ == "__main__":
    main()
