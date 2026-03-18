from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .rules import Piece, Pos


@dataclass(frozen=True, slots=True)
class Move:
    src: Pos
    dst: Pos
    capture: Optional[Piece] = None

    def __iter__(self):
        """Cho phép unpack move: src, dst = move"""
        yield from (self.src, self.dst)

    def __repr__(self) -> str:
        """Hỗ trợ Debug: In ra nước đi dưới dạng dễ đọc (ví dụ: (9,4) -> (8,4))"""
        cap_str = f" x {self.capture.kind.value}" if self.capture else ""
        return f"Move({self.src} -> {self.dst}{cap_str})"

    def is_capture(self) -> bool:
        """Kiểm tra nhanh xem nước đi này có ăn quân hay không"""
        return self.capture is not None

    @property
    def distance_squared(self) -> int:
        """Tiện ích tính khoảng cách di chuyển (hữu ích cho Bảo khi viết luật hoặc Khánh làm Heuristic)"""
        return (self.src[0] - self.dst[0])**2 + (self.src[1] - self.dst[1])**2