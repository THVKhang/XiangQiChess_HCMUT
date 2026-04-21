#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.board import Board
from core.move import Move
from core.move_generator import legal_moves
from core.rules import Color, Piece, PieceType
from core.state import GameState
from tools.parse_pgn_fen import parse_file

FEN_PIECE_MAP = {
    "k": (Color.BLACK, PieceType.GENERAL),
    "a": (Color.BLACK, PieceType.ADVISOR),
    "b": (Color.BLACK, PieceType.ELEPHANT),
    "n": (Color.BLACK, PieceType.HORSE),
    "r": (Color.BLACK, PieceType.ROOK),
    "c": (Color.BLACK, PieceType.CANNON),
    "p": (Color.BLACK, PieceType.SOLDIER),
    "K": (Color.RED, PieceType.GENERAL),
    "A": (Color.RED, PieceType.ADVISOR),
    "B": (Color.RED, PieceType.ELEPHANT),
    "N": (Color.RED, PieceType.HORSE),
    "R": (Color.RED, PieceType.ROOK),
    "C": (Color.RED, PieceType.CANNON),
    "P": (Color.RED, PieceType.SOLDIER),
}

PIECE_CHARS = {
    PieceType.GENERAL: ["帅", "將", "将", "帥"],
    PieceType.ADVISOR: ["仕", "士"],
    PieceType.ELEPHANT: ["相", "象"],
    PieceType.HORSE: ["傌", "馬", "马"],
    PieceType.ROOK: ["俥", "車", "车"],
    PieceType.CANNON: ["炮", "砲"],
    PieceType.SOLDIER: ["兵", "卒"],
}

DIGIT_TO_CH = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}
CH_TO_INT = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "１": 1, "２": 2, "３": 3, "４": 4, "５": 5, "６": 6, "７": 7, "８": 8, "９": 9,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}

SIMPLIFY_MAP = str.maketrans({
    "將": "将", "帥": "帅", "馬": "马", "車": "车", "俥": "车", "砲": "炮", "傌": "马",
    "進": "进", "退": "退", "平": "平", "前": "前", "後": "后", "中": "中",
    "１": "1", "２": "2", "３": "3", "４": "4", "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
    "．": ".",
})


@dataclass
class Failure:
    source_file: str
    ply: int
    move_text: str
    reason: str


def normalize_token(tok: str) -> str:
    t = tok.strip().replace(" ", "")
    t = t.translate(SIMPLIFY_MAP)
    t = t.replace("...", "")
    t = re.sub(r"^\d+\.*", "", t)
    return t


def file_num_from_col_standard(col: int, color: Color) -> int:
    # Quy ước phổ biến trong ký pháp Trung:
    # - Red: lộ 1 ở cột phải (từ góc nhìn Red) => col 8 -> 1, col 0 -> 9
    # - Black: lộ 1 ở cột trái (từ góc nhìn Black) => col 0 -> 1, col 8 -> 9
    return (9 - col) if color == Color.RED else (col + 1)


def file_num_from_col_absolute(col: int, color: Color) -> int:
    # Một số nguồn dữ liệu dùng đánh số tuyệt đối trái->phải cho cả hai bên.
    return col + 1




def front_back_prefix(state: GameState, src: tuple[int, int], piece: Piece) -> Optional[str]:
    same_file: list[tuple[int, int]] = []
    _, col = src
    for r in range(10):
        q = state.board.get((r, col))
        if q is not None and q.color == piece.color and q.kind == piece.kind:
            same_file.append((r, col))

    if len(same_file) <= 1:
        return None

    # Sắp từ "trước" -> "sau" theo hướng tấn công của bên đang đi.
    if piece.color == Color.RED:
        ordered = sorted(same_file, key=lambda x: x[0])
    else:
        ordered = sorted(same_file, key=lambda x: -x[0])

    idx = ordered.index(src)
    if len(ordered) == 2:
        return "前" if idx == 0 else "后"
    if len(ordered) == 3:
        return ["前", "中", "后"][idx]
    return None

def move_notations(state: GameState, move: Move, *, include_absolute: bool = True) -> set[str]:
    p = state.board.get(move.src)
    if p is None:
        return set()

    (sr, sc), (dr, dc) = move.src, move.dst
    action: str
    out: set[str] = set()

    funcs = [file_num_from_col_standard]
    if include_absolute:
        funcs.append(file_num_from_col_absolute)

    for file_num_func in funcs:
        file_num = file_num_func(sc, p.color)

        if dc == sc:
            forward = (dr < sr) if p.color == Color.RED else (dr > sr)
            action = "进" if forward else "退"
            if p.kind in {PieceType.HORSE, PieceType.ELEPHANT, PieceType.ADVISOR}:
                target_num = file_num_func(dc, p.color)
            else:
                target_num = abs(dr - sr)
        elif dr == sr:
            action = "平"
            target_num = file_num_func(dc, p.color)
        else:
            forward = (dr < sr) if p.color == Color.RED else (dr > sr)
            action = "进" if forward else "退"
            target_num = file_num_func(dc, p.color)

        prefix = front_back_prefix(state, move.src, p)
        for ch in PIECE_CHARS[p.kind]:
            out.add(normalize_token(f"{ch}{file_num}{action}{target_num}"))
            out.add(normalize_token(f"{ch}{DIGIT_TO_CH[file_num]}{action}{DIGIT_TO_CH[target_num]}"))
            if prefix is not None:
                out.add(normalize_token(f"{prefix}{ch}{action}{target_num}"))
                out.add(normalize_token(f"{prefix}{ch}{action}{DIGIT_TO_CH[target_num]}"))

    return out


def from_fen(fen: str) -> GameState:
    parts = fen.split()
    if len(parts) < 2:
        raise ValueError(f"Invalid FEN: {fen}")
    board_part, stm = parts[0], parts[1]
    rows = board_part.split("/")
    if len(rows) != 10:
        raise ValueError(f"Invalid Xiangqi FEN rows: {fen}")

    board = Board.empty()
    for r, row in enumerate(rows):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
                continue
            if ch not in FEN_PIECE_MAP:
                raise ValueError(f"Unknown piece char in FEN: {ch}")
            color, kind = FEN_PIECE_MAP[ch]
            board.set((r, c), Piece(color, kind))
            c += 1
        if c != 9:
            raise ValueError(f"Invalid row width in FEN row: {row}")

    side = Color.RED if stm == "w" else Color.BLACK
    return GameState(board=board, side_to_move=side)


def validate_game(source_file: str, fen: str, moves: list[str]) -> list[Failure]:
    state = from_fen(fen)
    failures: list[Failure] = []

    for idx, raw in enumerate(moves, start=1):
        token = normalize_token(raw)
        if not token:
            continue

        candidates = legal_moves(state)

        matched_std: list[Move] = []
        for mv in candidates:
            if token in move_notations(state, mv, include_absolute=False):
                matched_std.append(mv)

        if len(matched_std) == 1:
            state.apply_move(matched_std[0])
            continue
        if len(matched_std) > 1:
            failures.append(Failure(source_file, idx, raw, "ambiguous_notation"))
            break

        matched_abs: list[Move] = []
        for mv in candidates:
            if token in move_notations(state, mv, include_absolute=True):
                matched_abs.append(mv)

        if len(matched_abs) == 1:
            state.apply_move(matched_abs[0])
            continue
        if len(matched_abs) > 1:
            failures.append(Failure(source_file, idx, raw, "ambiguous_notation"))
            break

        failures.append(Failure(source_file, idx, raw, "no_legal_move_match"))
        break

    return failures


def iter_pgn(path: Path) -> list[Path]:
    return [path] if path.is_file() else sorted(path.rglob("*.pgn"))


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate Xiangqi PGN moves against engine legality.")
    ap.add_argument("input", help="PGN file or directory")
    ap.add_argument("-o", "--output", default="validation_report.json", help="Output JSON report")
    ap.add_argument("--limit", type=int, default=0, help="Only validate first N files")
    ap.add_argument("--offset", type=int, default=0, help="Skip first N files before validating")
    ap.add_argument(
        "--checkpoint-every",
        type=int,
        default=500,
        help="Write intermediate report every N processed files (0 to disable)",
    )
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    files = iter_pgn(in_path)
    if args.offset > 0:
        files = files[args.offset :]
    if args.limit > 0:
        files = files[: args.limit]

    report = {
        "total_files": len(files),
        "clean_files": 0,
        "invalid_files": 0,
        "failures": [],
    }

    root = in_path if in_path.is_dir() else in_path.parent
    out = Path(args.output).resolve()

    for idx, p in enumerate(files, start=1):
        parsed = parse_file(p, root)
        if not parsed.fen:
            report["invalid_files"] += 1
            report["failures"].append({
                "source_file": parsed.source_file,
                "ply": 0,
                "move_text": "",
                "reason": "missing_fen",
            })
            continue

        try:
            fails = validate_game(parsed.source_file, parsed.fen, parsed.moves)
        except Exception as exc:
            report["invalid_files"] += 1
            report["failures"].append({
                "source_file": parsed.source_file,
                "ply": 0,
                "move_text": "",
                "reason": f"exception:{type(exc).__name__}",
            })
            continue

        if fails:
            report["invalid_files"] += 1
            for f in fails:
                report["failures"].append(f.__dict__)
        else:
            report["clean_files"] += 1

        if args.checkpoint_every > 0 and idx % args.checkpoint_every == 0:
            write_report(report, out)
            print(
                f"[checkpoint] {idx}/{report['total_files']} "
                f"clean={report['clean_files']} invalid={report['invalid_files']}",
                flush=True,
            )

    write_report(report, out)

    print(f"Validated files: {report['total_files']}")
    print(f"Clean files: {report['clean_files']}")
    print(f"Invalid files: {report['invalid_files']}")
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
