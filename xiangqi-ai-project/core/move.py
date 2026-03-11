from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .rules import Piece, Pos


@dataclass(frozen=True, slots=True)
class Move:
    src: Pos
    dst: Pos
    capture: Optional[Piece] = None

    def __iter__(self):
        yield from (self.src, self.dst)

