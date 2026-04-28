#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path
from typing import Any

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.move import Move
from core.move_generator import legal_moves as generate_legal_moves
from tools.validate_pgn_legality import from_fen, move_notations, normalize_token


def pick_move_from_token(state: Any, token: str) -> Move | None:
    candidates = generate_legal_moves(state)

    matched_std: list[Move] = []
    for mv in candidates:
        if token in move_notations(state, mv, include_absolute=False):
            matched_std.append(mv)

    if len(matched_std) == 1:
        return matched_std[0]
    if len(matched_std) > 1:
        return None

    matched_abs: list[Move] = []
    for mv in candidates:
        if token in move_notations(state, mv, include_absolute=True):
            matched_abs.append(mv)

    if len(matched_abs) == 1:
        return matched_abs[0]
    return None


def label_one_game(obj: dict[str, Any]) -> dict[str, Any]:
    fen = obj.get("fen", "")
    moves = obj.get("moves", [])
    labels: list[dict[str, Any]] = []

    try:
        state = from_fen(fen)
    except Exception:
        obj["move_labels"] = [{"move": m, "is_legal": False, "reason": "invalid_fen"} for m in moves]
        obj["all_moves_legal"] = False
        return obj

    all_ok = True
    for raw in moves:
        token = normalize_token(raw)
        if not token:
            labels.append({"move": raw, "is_legal": False, "reason": "empty_token"})
            all_ok = False
            continue

        mv = pick_move_from_token(state, token)
        if mv is None:
            labels.append({"move": raw, "is_legal": False, "reason": "no_unique_legal_match"})
            all_ok = False
            continue

        state.apply_move(mv)
        labels.append({"move": raw, "is_legal": True, "reason": "matched"})

    obj["move_labels"] = labels
    obj["all_moves_legal"] = all_ok
    return obj


def _iter_input_lines(in_path: Path, limit: int) -> Any:
    with in_path.open("r", encoding="utf-8") as fin:
        yielded = 0
        for line in fin:
            if not line.strip():
                continue
            if limit > 0 and yielded >= limit:
                break
            yield line
            yielded += 1


def _process_line(line: str) -> tuple[str, bool] | None:
    try:
        obj = json.loads(line)
    except Exception:
        return None

    labeled = label_one_game(obj)
    out_line = json.dumps(labeled, ensure_ascii=False) + "\n"
    return out_line, bool(labeled.get("all_moves_legal"))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Label each move as legal/illegal using old generate_legal_moves-style API."
    )
    ap.add_argument("--input", required=True, help="Input parsed JSONL (e.g., ccpd_parsed.jsonl)")
    ap.add_argument("--output", required=True, help="Output JSONL with move_labels")
    ap.add_argument("--limit", type=int, default=0, help="Process only first N lines (0 = all)")
    ap.add_argument(
        "--workers",
        type=int,
        default=max(1, (mp.cpu_count() or 1) - 1),
        help="Number of worker processes (default: CPU-1)",
    )
    ap.add_argument(
        "--chunksize",
        type=int,
        default=64,
        help="Chunk size for multiprocessing map",
    )
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    legal_games = 0

    workers = max(1, int(args.workers))
    chunksize = max(1, int(args.chunksize))

    with out_path.open("w", encoding="utf-8") as fout:
        line_iter = _iter_input_lines(in_path, args.limit)
        if workers == 1:
            for line in line_iter:
                result = _process_line(line)
                if result is None:
                    continue
                out_line, all_legal = result
                fout.write(out_line)
                processed += 1
                if all_legal:
                    legal_games += 1
        else:
            with mp.Pool(processes=workers) as pool:
                for result in pool.imap(_process_line, line_iter, chunksize=chunksize):
                    if result is None:
                        continue
                    out_line, all_legal = result
                    fout.write(out_line)
                    processed += 1
                    if all_legal:
                        legal_games += 1

    print(f"Processed games: {processed}")
    print(f"Games with all moves legal: {legal_games}")
    print(f"Output: {out_path}")
    print(f"Workers: {workers}  Chunksize: {chunksize}")


if __name__ == "__main__":
    main()
