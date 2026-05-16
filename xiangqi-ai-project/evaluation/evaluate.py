from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent, HardAgent, MediumAgent
from agents.ml_agent import MLAgent
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

def _build_ml(color: Color):
    return MLAgent(player_id=color)

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

def run_evaluation_ml_vs_random(games_per_matchup: int = 5, max_turns: int = 160) -> list[MatchRecord]:
    records: list[MatchRecord] = []
    for idx in range(1, games_per_matchup + 1):
        # ML as RED vs random BLACK
        red_a = _build_ml(Color.RED)
        black_a = RandomAgent(player_id=Color.BLACK)
        records.append(_run_one_game(red_a, black_a, idx * 2 - 1, "ML_vs_Random", max_turns))

        # random RED vs ML as BLACK
        red_b = RandomAgent(player_id=Color.RED)
        black_b = _build_ml(Color.BLACK)
        records.append(_run_one_game(red_b, black_b, idx * 2, "Random_vs_ML", max_turns))
    return records

def run_evaluation_ml_vs_search(games_per_matchup: int = 50, max_turns: int = 160) -> list[MatchRecord]:
    records: list[MatchRecord] = []
    level = "easy"
    for idx in range(1, games_per_matchup + 1):
        # ML as RED vs search BLACK
        red_a = _build_ml(Color.RED)
        black_a = _build_search(level, Color.BLACK)
        records.append(_run_one_game(red_a, black_a, idx * 2 - 1, f"ML_vs_{level}", max_turns))

        # search RED vs ML as BLACK
        red_b = _build_search(level, Color.RED)
        black_b = _build_ml(Color.BLACK)
        records.append(_run_one_game(red_b, black_b, idx * 2, f"{level}_vs_ML", max_turns))
    return records


def _save_results(records: list[MatchRecord], out_dir: Path, prefix: str) -> tuple[Path, Path]:
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


def _print_summary(records: list[MatchRecord], title: str) -> None:
    total = len(records)
    ml_wins = 0
    draws = 0
    ml_losses = 0

    for r in records:
        if r.winner == "draw":
            draws += 1
        elif r.winner == "red" and "MLAgent" in r.red_agent:
            ml_wins += 1
        elif r.winner == "black" and "MLAgent" in r.black_agent:
            ml_wins += 1
        else:
            ml_losses += 1

    avg_ms = sum(r.elapsed_ms for r in records) / max(1, total)
    avg_plies = sum(r.plies for r in records) / max(1, total)

    print(f"=== {title} ===")
    print(f"Total games: {total}")
    print(f"ML wins    : {ml_wins}")
    print(f"ML losses  : {ml_losses}")
    print(f"Draws      : {draws}")
    print(f"Avg time   : {avg_ms:.1f} ms/game")
    print(f"Avg plies  : {avg_plies:.1f}")
    
def plot_results(records: list[MatchRecord], out_dir: Path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed. Skipping plot generation.")
        return
        
    ts = time.strftime("%Y%m%d_%H%M%S")
    plot_path = out_dir / f"benchmark_plot_{ts}.png"
    
    ml_wins = sum(1 for r in records if (r.winner == "red" and "MLAgent" in r.red_agent) or (r.winner == "black" and "MLAgent" in r.black_agent))
    ml_losses = sum(1 for r in records if (r.winner == "red" and "MLAgent" not in r.red_agent) or (r.winner == "black" and "MLAgent" not in r.black_agent))
    draws = sum(1 for r in records if r.winner == "draw")
    
    labels = ['ML Wins', 'ML Losses', 'Draws']
    values = [ml_wins, ml_losses, draws]
    colors = ['#4CAF50', '#F44336', '#9E9E9E']
    
    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=colors)
    plt.title(f'MLAgent Performance ({len(records)} games)')
    plt.ylabel('Number of Games')
    for i, v in enumerate(values):
        plt.text(i, v + 1, str(v), ha='center', va='bottom')
        
    plt.savefig(plot_path)
    print(f"Plot saved : {plot_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["10-random", "100-search"], required=True, help="Benchmark mode")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent / "results"

    if args.mode == "10-random":
        print("Running 10 games: ML vs Random...")
        records = run_evaluation_ml_vs_random(games_per_matchup=5, max_turns=100) # 5 each side = 10 total
        json_file, csv_file = _save_results(records, root, "ml_vs_random_10")
        _print_summary(records, "ML vs Random (10 Games)")
        print(f"JSON saved: {json_file}")
        print(f"CSV saved : {csv_file}")
        
    elif args.mode == "100-search":
        print("Running 100 games: ML vs Search...")
        records = run_evaluation_ml_vs_search(games_per_matchup=50, max_turns=100) # 50 each side = 100 total
        json_file, csv_file = _save_results(records, root, "ml_vs_search_100")
        _print_summary(records, "ML vs Search (100 Games)")
        plot_results(records, root)
        print(f"JSON saved: {json_file}")
        print(f"CSV saved : {csv_file}")
