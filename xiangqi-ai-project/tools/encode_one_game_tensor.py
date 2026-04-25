#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent
from core.encoding import game_to_tensor_sequence
from core.rules import Color
from game.game_loop import run_game


def main() -> None:
    ap = argparse.ArgumentParser(description="Run one game and encode it to a tensor sequence.")
    ap.add_argument("--canonical", action="store_true", help="Canonicalize by side-to-move when encoding.")
    ap.add_argument("--numpy", action="store_true", help="Return numpy arrays (requires numpy).")
    ap.add_argument("--out", type=str, default="", help="Optional: save to .npz (requires numpy).")
    args = ap.parse_args()

    red = RandomAgent(player_id=Color.RED)
    black = EasyAgent(player_id=Color.BLACK)
    result = run_game(red_agent=red, black_agent=black, max_turns=80)

    moves = [tr.move for tr in result.history if tr.move is not None]
    seq = game_to_tensor_sequence(
        initial_state=__import__("core.state", fromlist=["GameState"]).GameState(),  # initial position
        moves=moves,
        canonical=args.canonical,
        as_numpy=args.numpy or bool(args.out),
        channels_first=True,
        include_initial=True,
        include_final=True,
    )

    if args.out:
        import numpy as np  # type: ignore

        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out_path, X=seq)
        print(f"Saved: {out_path}  shape={seq.shape}")
        return

    if args.numpy:
        print(f"Encoded sequence shape: {seq.shape}")
    else:
        # list path
        t = len(seq)
        c = len(seq[0])
        h = len(seq[0][0])
        w = len(seq[0][0][0])
        print(f"Encoded sequence: T={t}, shape per state=({c},{h},{w})")


if __name__ == "__main__":
    main()

