from __future__ import annotations

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


def run_evaluation(games_per_matchup: int = 4, max_turns: int = 160) -> list[MatchRecord]:
	records: list[MatchRecord] = []
	levels = ["easy", "medium", "hard"]

	for level in levels:
		for idx in range(1, games_per_matchup + 1):
			# Game A: search as RED vs random BLACK
			red_a = _build_search(level, Color.RED)
			black_a = RandomAgent(player_id=Color.BLACK)
			records.append(
				_run_one_game(
					red_agent=red_a,
					black_agent=black_a,
					game_index=idx,
					matchup=f"{level}_vs_random",
					max_turns=max_turns,
				)
			)

			# Game B: random RED vs search as BLACK (color swap for fairness)
			red_b = RandomAgent(player_id=Color.RED)
			black_b = _build_search(level, Color.BLACK)
			records.append(
				_run_one_game(
					red_agent=red_b,
					black_agent=black_b,
					game_index=idx,
					matchup=f"random_vs_{level}",
					max_turns=max_turns,
				)
			)

	return records


def _save_results(records: list[MatchRecord], out_dir: Path) -> tuple[Path, Path]:
	out_dir.mkdir(parents=True, exist_ok=True)
	ts = time.strftime("%Y%m%d_%H%M%S")

	json_path = out_dir / f"evaluate_{ts}.json"
	csv_path = out_dir / f"evaluate_{ts}.csv"

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


if __name__ == "__main__":
	records = run_evaluation(games_per_matchup=3, max_turns=140)
	root = Path(__file__).resolve().parent / "results"
	json_file, csv_file = _save_results(records, root)
	_print_summary(records)
	print(f"JSON saved: {json_file}")
	print(f"CSV saved : {csv_file}")
