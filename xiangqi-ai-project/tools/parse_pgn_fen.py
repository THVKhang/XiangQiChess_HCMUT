#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ENCODINGS_TO_TRY = [
    "utf-8",
    "utf-8-sig",
    "cp950",
    "big5",
    "gb18030",
    "gbk",
]

HEADER_RE = re.compile(r'^\[(?P<key>[^\s]+)\s+"(?P<value>.*)"\]$')
MOVE_NUM_RE = re.compile(r'^\d+\.{1,3}$')
RESULT_TOKENS = {"1-0", "0-1", "1/2-1/2", "*"}


@dataclass
class ParsedPGN:
    source_file: str
    encoding: str
    headers: dict[str, str]
    fen: Optional[str]
    moves: list[str]


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    last_error: Optional[Exception] = None
    for enc in ENCODINGS_TO_TRY:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise UnicodeDecodeError(
            last_error.encoding,
            last_error.object,
            last_error.start,
            last_error.end,
            f"Cannot decode {path} with supported encodings.",
        )
    raise ValueError(f"Cannot decode {path}")


def parse_pgn_text(text: str, source_file: str, encoding: str) -> ParsedPGN:
    headers: dict[str, str] = {}
    move_lines: list[str] = []
    in_move_section = False

    for line in text.splitlines():
        striped = line.strip().replace("﻿", "")
        if not striped:
            if headers:
                in_move_section = True
            continue

        if not in_move_section and striped.startswith("[") and striped.endswith("]"):
            m = HEADER_RE.match(striped)
            if m:
                headers[m.group("key")] = m.group("value")
            continue

        in_move_section = True
        move_lines.append(striped)

    move_text = " ".join(move_lines)
    move_text = re.sub(r"\{[^}]*\}", " ", move_text)
    move_text = re.sub(r"\([^)]*\)", " ", move_text)
    move_text = move_text.replace("…", " ")

    tokens = [tok for tok in re.split(r"\s+", move_text) if tok]
    cleaned_moves: list[str] = []

    for tok in tokens:
        token = tok.strip()
        token = token.replace("．", ".")
        token = token.rstrip(".") if token.endswith("....") else token

        if token in RESULT_TOKENS:
            continue
        if MOVE_NUM_RE.match(token):
            continue
        if re.fullmatch(r"\d+\.", token):
            continue
        if re.fullmatch(r"\d+", token):
            continue

        if token.startswith("..."):
            token = token[3:]
        token = token.strip()
        if not token:
            continue
        cleaned_moves.append(token)

    return ParsedPGN(
        source_file=source_file,
        encoding=encoding,
        headers=headers,
        fen=headers.get("FEN"),
        moves=cleaned_moves,
    )


def parse_file(path: Path, root: Path) -> ParsedPGN:
    text, encoding = read_text_with_fallback(path)
    rel_path = str(path.relative_to(root))
    return parse_pgn_text(text, rel_path, encoding)


def iter_pgn_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob("*.pgn"))


def write_jsonl(items: list[ParsedPGN], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for item in items:
            payload = {
                "source_file": item.source_file,
                "encoding": item.encoding,
                "headers": item.headers,
                "fen": item.fen,
                "moves": item.moves,
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse Xiangqi PGN/FEN files to structured move lists with encoding fallback."
    )
    parser.add_argument("input", help="PGN file or directory")
    parser.add_argument(
        "-o",
        "--output",
        default="parsed_pgn.jsonl",
        help="Output JSONL file path (UTF-8)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional: parse only first N files (0 = all)",
    )

    args = parser.parse_args()
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    files = iter_pgn_files(input_path)
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        raise ValueError("No .pgn files found.")

    root = input_path if input_path.is_dir() else input_path.parent
    parsed_items: list[ParsedPGN] = []

    for path in files:
        parsed_items.append(parse_file(path, root))

    output_path = Path(args.output).resolve()
    write_jsonl(parsed_items, output_path)

    print(f"Parsed files: {len(parsed_items)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
