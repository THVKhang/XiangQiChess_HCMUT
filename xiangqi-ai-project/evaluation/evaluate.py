from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.ml_agent import MLAgent
from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent, HardAgent, MediumAgent
from core.rules import Color
from game.game_loop import run_game


@dataclass(slots=True)
class MatchRecord:
    matchup: str
    game_index: int
    red_agent: str
    black_agent: str
    winner: str
    reason: str
    plies: int
    elapsed_ms: int


def _build_search(level: str, color: Color):
    level_map = {
        "easy": EasyAgent,
        "medium": MediumAgent,
        "hard": HardAgent,
    }
    cls = level_map[level]
    return cls(player_id=color)


def _run_one_game(red_agent, black_agent, game_index: int, matchup: str, max_turns: int) -> MatchRecord:
    start = time.perf_counter()
    result = run_game(red_agent=red_agent, black_agent=black_agent, max_turns=max_turns)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    winner = "draw" if result.winner is None else result.winner.value
    return MatchRecord(
        matchup=matchup,
        game_index=game_index,
        red_agent=red_agent.name,
        black_agent=black_agent.name,
        winner=winner,
        reason=result.reason,
        plies=len(result.history),
        elapsed_ms=elapsed_ms,
    )


def run_ml_vs_random(games: int = 10, max_turns: int = 160, model_path: str | None = None) -> list[MatchRecord]:
    """Run hidden/headless MLAgent vs RandomAgent matches.

    This is the Week 2 checkpoint scenario: MLAgent can load the dummy policy,
    run model forward, choose only legal moves, and finish games without UI.
    Colors are swapped every game for a basic sanity check.
    """
    records: list[MatchRecord] = []
    for idx in range(1, games + 1):
        if idx % 2 == 1:
            red_agent = MLAgent(player_id=Color.RED, model_path=model_path, name="MLAgent")
            black_agent = RandomAgent(player_id=Color.BLACK)
            matchup = "ml_vs_random"
        else:
            red_agent = RandomAgent(player_id=Color.RED)
            black_agent = MLAgent(player_id=Color.BLACK, model_path=model_path, name="MLAgent")
            matchup = "random_vs_ml"
        records.append(_run_one_game(red_agent, black_agent, idx, matchup, max_turns))
    return records


def run_search_vs_random(games_per_matchup: int = 4, max_turns: int = 160) -> list[MatchRecord]:
    records: list[MatchRecord] = []
    levels = ["easy", "medium", "hard"]

    for level in levels:
        for idx in range(1, games_per_matchup + 1):
            records.append(
                _run_one_game(
                    red_agent=_build_search(level, Color.RED),
                    black_agent=RandomAgent(player_id=Color.BLACK),
                    game_index=idx,
                    matchup=f"{level}_vs_random",
                    max_turns=max_turns,
                )
            )
            records.append(
                _run_one_game(
                    red_agent=RandomAgent(player_id=Color.RED),
                    black_agent=_build_search(level, Color.BLACK),
                    game_index=idx,
                    matchup=f"random_vs_{level}",
                    max_turns=max_turns,
                )
            )
    return records


def run_evaluation(games_per_matchup: int = 4, max_turns: int = 160) -> list[MatchRecord]:
    """Default mixed evaluation kept for backward compatibility."""
    return run_search_vs_random(games_per_matchup=games_per_matchup, max_turns=max_turns)


def _save_results(records: list[MatchRecord], out_dir: Path, prefix: str = "evaluate") -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    json_path = out_dir / f"{prefix}_{ts}.json"
    csv_path = out_dir / f"{prefix}_{ts}.csv"

    payload = {
        "timestamp": ts,
        "total_games": len(records),
        "records": [asdict(r) for r in records],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "matchup",
                "game_index",
                "red_agent",
                "black_agent",
                "winner",
                "reason",
                "plies",
                "elapsed_ms",
            ],
        )
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))

    return json_path, csv_path


def _print_summary(records: list[MatchRecord]) -> None:
    total = len(records)
    red_wins = sum(1 for r in records if r.winner == "red")
    black_wins = sum(1 for r in records if r.winner == "black")
    draws = sum(1 for r in records if r.winner == "draw")
    avg_ms = sum(r.elapsed_ms for r in records) / max(1, total)

    print("=== Evaluation Summary ===")
    print(f"Total games: {total}")
    print(f"Red wins : {red_wins}")
    print(f"Black wins: {black_wins}")
    print(f"Draws    : {draws}")
    print(f"Avg time : {avg_ms:.1f} ms/game")

    by_matchup: dict[str, int] = {}
    for record in records:
        by_matchup[record.matchup] = by_matchup.get(record.matchup, 0) + 1
    print("Matchups : " + ", ".join(f"{k}={v}" for k, v in sorted(by_matchup.items())))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run headless Xiangqi agent evaluation.")
    parser.add_argument("--mode", choices=["ml-vs-random", "search-vs-random"], default="ml-vs-random")
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=160)
    parser.add_argument("--model-path", type=str, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "results")
    args = parser.parse_args()

    if args.mode == "ml-vs-random":
        records = run_ml_vs_random(games=args.games, max_turns=args.max_turns, model_path=args.model_path)
        prefix = "ml_vs_random"
    else:
        records = run_search_vs_random(games_per_matchup=args.games, max_turns=args.max_turns)
        prefix = "search_vs_random"

    json_file, csv_file = _save_results(records, args.out_dir, prefix=prefix)
    _print_summary(records)
    print(f"JSON saved: {json_file}")
    print(f"CSV saved : {csv_file}")


if __name__ == "__main__":
    main()
