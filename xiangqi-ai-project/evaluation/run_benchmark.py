"""Benchmark Script: ML Agent vs Search Agent vs Random Agent.

Generates comparison charts (matplotlib) for the final report.
Run: python evaluation/run_benchmark.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.ml_agent import MLAgent
from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent, MediumAgent, HardAgent
from core.rules import Color
from game.game_loop import run_game

import random
import gc


@dataclass
class BenchmarkResult:
    matchup: str
    games: int
    wins: int
    losses: int
    draws: int
    avg_moves: float
    avg_time_ms: float
    win_rate: float


def run_matchup(
    name: str,
    red_factory,
    black_factory,
    games: int = 10,
    max_turns: int = 200,
) -> BenchmarkResult:
    """Run N games between two agent factories."""
    wins, losses, draws = 0, 0, 0
    total_moves, total_time = 0, 0

    for i in range(games):
        red = red_factory(Color.RED, i)
        black = black_factory(Color.BLACK, i)

        t0 = time.perf_counter()
        result = run_game(red, black, max_turns=max_turns)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        winner = result.winner
        if winner is not None and winner == Color.RED:
            wins += 1
        elif winner is not None and winner == Color.BLACK:
            losses += 1
        else:
            draws += 1

        total_moves += len(result.history)
        total_time += elapsed_ms

        status = "W" if (winner == Color.RED) else ("L" if winner == Color.BLACK else "D")
        print(f"  {name} G{i+1}: {status} ({len(result.history)} moves, {elapsed_ms:.0f}ms)")
        del red, black, result
        gc.collect()

    return BenchmarkResult(
        matchup=name,
        games=games,
        wins=wins,
        losses=losses,
        draws=draws,
        avg_moves=total_moves / games,
        avg_time_ms=total_time / games,
        win_rate=wins / games * 100,
    )


def main():
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    games_per_matchup = 10
    max_turns = 200

    print("=" * 60)
    print("BENCHMARK: ML Agent vs Random / Search")
    print("=" * 60)

    # ML Hard vs Random
    print("\n>>> ML(Hard) vs Random <<<")
    r1 = run_matchup(
        "ML(Hard) vs Random",
        lambda c, i: MLAgent(c, level="Hard"),
        lambda c, i: RandomAgent(c, rng=random.Random(i * 13 + 7)),
        games=games_per_matchup,
        max_turns=max_turns,
    )

    # ML Medium vs Random
    print("\n>>> ML(Medium) vs Random <<<")
    r2 = run_matchup(
        "ML(Medium) vs Random",
        lambda c, i: MLAgent(c, level="Medium"),
        lambda c, i: RandomAgent(c, rng=random.Random(i * 17 + 3)),
        games=games_per_matchup,
        max_turns=max_turns,
    )

    # ML Easy vs Random
    print("\n>>> ML(Easy) vs Random <<<")
    r3 = run_matchup(
        "ML(Easy) vs Random",
        lambda c, i: MLAgent(c, level="Easy"),
        lambda c, i: RandomAgent(c, rng=random.Random(i * 19 + 5)),
        games=games_per_matchup,
        max_turns=max_turns,
    )

    # Search Easy vs Random (for comparison)
    print("\n>>> Search(Easy) vs Random <<<")
    r4 = run_matchup(
        "Search(Easy) vs Random",
        lambda c, i: EasyAgent(c),
        lambda c, i: RandomAgent(c, rng=random.Random(i * 23 + 11)),
        games=games_per_matchup,
        max_turns=max_turns,
    )

    # ML Hard vs Search Easy
    print("\n>>> ML(Hard) vs Search(Easy) <<<")
    r5 = run_matchup(
        "ML(Hard) vs Search(Easy)",
        lambda c, i: MLAgent(c, level="Hard"),
        lambda c, i: EasyAgent(c),
        games=games_per_matchup,
        max_turns=max_turns,
    )

    all_results = [r1, r2, r3, r4, r5]

    # Save JSON
    json_path = results_dir / "benchmark_results.json"
    json_path.write_text(
        json.dumps([asdict(r) for r in all_results], indent=2),
        encoding="utf-8",
    )
    print(f"\nJSON saved: {json_path}")

    # Print summary table
    print("\n" + "=" * 70)
    print(f"{'Matchup':<30} {'W':>3} {'L':>3} {'D':>3} {'WR%':>6} {'AvgM':>6} {'AvgT':>8}")
    print("-" * 70)
    for r in all_results:
        print(
            f"{r.matchup:<30} {r.wins:>3} {r.losses:>3} {r.draws:>3} "
            f"{r.win_rate:>5.1f}% {r.avg_moves:>6.0f} {r.avg_time_ms:>7.0f}ms"
        )
    print("=" * 70)

    # Generate chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Chart 1: Win Rate Comparison
        ax1 = axes[0]
        names = [r.matchup for r in all_results]
        win_rates = [r.win_rate for r in all_results]
        colors = ["#2ecc71", "#3498db", "#e67e22", "#9b59b6", "#e74c3c"]
        bars = ax1.barh(names, win_rates, color=colors[:len(names)])
        ax1.set_xlabel("Win Rate (%)")
        ax1.set_title("Win Rate: Red Agent vs Black Agent")
        ax1.set_xlim(0, 105)
        for bar, wr in zip(bars, win_rates):
            ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                     f"{wr:.0f}%", va='center', fontweight='bold')

        # Chart 2: Win/Loss/Draw breakdown
        ax2 = axes[1]
        x = range(len(all_results))
        w = 0.25
        ax2.bar([i - w for i in x], [r.wins for r in all_results], w, label="Wins", color="#2ecc71")
        ax2.bar(x, [r.draws for r in all_results], w, label="Draws", color="#f39c12")
        ax2.bar([i + w for i in x], [r.losses for r in all_results], w, label="Losses", color="#e74c3c")
        ax2.set_xticks(list(x))
        ax2.set_xticklabels([r.matchup.split(" vs ")[0] for r in all_results], rotation=30, ha="right")
        ax2.set_ylabel("Games")
        ax2.set_title("Win / Draw / Loss Breakdown")
        ax2.legend()

        plt.tight_layout()
        chart_path = results_dir / "benchmark_chart.png"
        plt.savefig(chart_path, dpi=150)
        print(f"Chart saved: {chart_path}")
        plt.close()

    except ImportError:
        print("matplotlib not installed — skipping chart generation.")

    print("\nBENCHMARK COMPLETE!")


if __name__ == "__main__":
    main()
