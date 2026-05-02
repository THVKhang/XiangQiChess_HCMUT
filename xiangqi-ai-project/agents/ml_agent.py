from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol, Sequence

from agents.base_agent import BaseAgent
from core.encoding import state_to_tensor
from core.move import Move
from core.move_generator import is_legal_move, legal_moves
from core.rules import BOARD_COLS, BOARD_ROWS, Color
from core.state import GameState

BOARD_SIZE = BOARD_ROWS * BOARD_COLS
POLICY_SIZE = BOARD_SIZE * BOARD_SIZE


class PolicyForwardModel(Protocol):
    """Minimal policy-network interface expected by MLAgent.

    The model receives one encoded board tensor with shape ``(15, 10, 9)`` and
    returns move scores. The preferred output shape is a flat policy vector of
    length ``90 * 90 = 8100`` where index = ``src_square * 90 + dst_square``.
    """

    def forward(self, state_tensor: Any) -> Any:
        ...


class MoveScoringModel(Protocol):
    """Backward-compatible interface from Week 1.

    Custom dummy/test models may score only the legal move list directly. The
    Week 2 path uses ``forward(state_tensor)`` first, but this interface remains
    useful for tests and for very simple heuristic baselines.
    """

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> Sequence[float]:
        ...


def _square_index(pos: tuple[int, int]) -> int:
    return pos[0] * BOARD_COLS + pos[1]


def move_to_policy_index(move: Move) -> int:
    """Map an actual board move to a flat 90x90 policy index."""
    return _square_index(move.src) * BOARD_SIZE + _square_index(move.dst)


def _to_canonical_pos(pos: tuple[int, int], side_to_move: Color) -> tuple[int, int]:
    """Match ``state_to_tensor(..., canonical=True)`` coordinate convention."""
    if side_to_move == Color.BLACK:
        return BOARD_ROWS - 1 - pos[0], BOARD_COLS - 1 - pos[1]
    return pos


def canonical_move_to_policy_index(move: Move, side_to_move: Color) -> int:
    """Map an actual move to the policy index used by the canonical tensor.

    With canonical encoding, BLACK-to-move states are rotated by 180 degrees and
    colors are swapped, so the model always sees the current player as RED.
    Legal moves from the real board must be transformed the same way before the
    policy score is read.
    """
    src = _to_canonical_pos(move.src, side_to_move)
    dst = _to_canonical_pos(move.dst, side_to_move)
    return _square_index(src) * BOARD_SIZE + _square_index(dst)


@dataclass(slots=True)
class DummyPolicyModel:
    """Deterministic dummy policy used before a trained model exists.

    This is intentionally a *model-like* object: MLAgent calls
    ``forward(state_tensor)`` and receives a full 8100-action policy vector. The
    dummy policy looks at the encoded board planes, prefers captures, avoids own
    pieces, slightly prefers central destinations, and gives a small bonus to
    forward progress. It is not smart, but it exercises the same inference path
    as a trained policy model.
    """

    capture_bonus: float = 100.0
    center_bonus: float = 1.0
    forward_bonus: float = 0.25
    invalid_score: float = -1_000_000.0

    def forward(self, state_tensor: Any) -> list[float]:
        x = state_tensor
        policy = [self.invalid_score for _ in range(POLICY_SIZE)]
        center_r = (BOARD_ROWS - 1) / 2.0
        center_c = (BOARD_COLS - 1) / 2.0

        own_piece = [[False for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        enemy_piece = [[False for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        source_value = [[0.0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        piece_values = (1.0, 0.2, 0.2, 0.45, 0.9, 0.5, 0.15)

        # Precompute occupancy from the tensor once. This keeps the dummy forward
        # pass fast enough for repeated hidden games while still returning a full
        # 8100-action policy vector.
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                for ch, value in enumerate(piece_values):
                    if float(x[ch][r][c]) > 0.5:
                        own_piece[r][c] = True
                        source_value[r][c] = value
                        break
                enemy_piece[r][c] = any(float(x[ch][r][c]) > 0.5 for ch in range(7, 14))

        dst_base = [[0.0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        for dst_r in range(BOARD_ROWS):
            for dst_c in range(BOARD_COLS):
                distance_to_center = abs(dst_r - center_r) + abs(dst_c - center_c)
                dst_base[dst_r][dst_c] = (
                    (self.capture_bonus if enemy_piece[dst_r][dst_c] else 0.0)
                    - self.center_bonus * distance_to_center
                )

        for src_r in range(BOARD_ROWS):
            for src_c in range(BOARD_COLS):
                if not own_piece[src_r][src_c]:
                    continue
                src_idx = src_r * BOARD_COLS + src_c
                row_offset = src_idx * BOARD_SIZE
                for dst_r in range(BOARD_ROWS):
                    forward_progress = src_r - dst_r  # current player is RED in canonical view
                    for dst_c in range(BOARD_COLS):
                        if (src_r == dst_r and src_c == dst_c) or own_piece[dst_r][dst_c]:
                            continue
                        dst_idx = dst_r * BOARD_COLS + dst_c
                        policy[row_offset + dst_idx] = (
                            source_value[src_r][src_c]
                            + dst_base[dst_r][dst_c]
                            + self.forward_bonus * forward_progress
                        )
        return policy

    @staticmethod
    def _source_piece_value(x: Any, r: int, c: int) -> float:
        # general, advisor, elephant, horse, rook, cannon, soldier
        values = (1.0, 0.2, 0.2, 0.45, 0.9, 0.5, 0.15)
        for ch, value in enumerate(values):
            if float(x[ch][r][c]) > 0.5:
                return value
        return 0.0

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> list[float]:
        """Compatibility helper for Week 1 tests/custom code."""
        policy = self.forward(state_tensor)
        # This method assumes RED/canonical coordinates are already aligned.
        return [float(policy[move_to_policy_index(move)]) for move in legal_move_list]


# Backward-compatible name used by Week 1 tests/docs.
DummyMoveScoringModel = DummyPolicyModel


class TorchPolicyAdapter:
    """Adapter for a PyTorch policy model saved as ``.pt``/``.pth``.

    Expected model contract:
    - input: tensor shaped ``(1, 15, 10, 9)``;
    - output: either flat policy scores of length 8100, or one score per legal
      move if the loaded object itself implements ``score_moves``.
    """

    def __init__(self, model_path: str | Path, device: str = "cpu") -> None:
        try:
            import torch  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("TorchPolicyAdapter requires PyTorch to load a .pt/.pth model.") from exc

        self._torch = torch
        self.device = device
        loaded = torch.load(str(model_path), map_location=device)
        self.model = loaded["model"] if isinstance(loaded, dict) and "model" in loaded else loaded
        if hasattr(self.model, "to"):
            self.model.to(device)
        if hasattr(self.model, "eval"):
            self.model.eval()

    def forward(self, state_tensor: Any) -> Any:
        torch = self._torch
        x = torch.tensor(state_tensor, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            output = self.model(x)
        if isinstance(output, (tuple, list)):
            output = output[0]
        return output.detach().flatten().cpu().tolist()


class MLAgent(BaseAgent):
    """ML-based agent that plugs into the existing GameLoop interface.

    GameLoop still calls only ``select_move(state)``. Inside that call, MLAgent:
    1. filters legal moves from the rule engine;
    2. encodes the board into a canonical tensor;
    3. runs model forward pass to get policy scores;
    4. reads the scores of legal moves only;
    5. returns the highest-scoring legal move.
    """

    def __init__(
        self,
        player_id: Color,
        model_path: str | Path | None = None,
        model: Optional[PolicyForwardModel | MoveScoringModel] = None,
        name: str = "MLAgent",
        device: str = "cpu",
        rng: Optional[random.Random] = None,
    ) -> None:
        super().__init__(player_id=player_id, name=name)
        self.device = device
        self.rng = rng if rng is not None else random.Random(0)
        self.model_path = Path(model_path) if model_path else None
        self.model = model if model is not None else self._load_model(self.model_path, device)

    def _load_model(self, model_path: Path | None, device: str) -> PolicyForwardModel | MoveScoringModel:
        if model_path is None:
            return DummyPolicyModel()
        if not model_path.exists():
            raise FileNotFoundError(f"ML model file not found: {model_path}")
        if model_path.suffix.lower() in {".pt", ".pth"}:
            return TorchPolicyAdapter(model_path=model_path, device=device)
        if model_path.suffix.lower() == ".json":
            config = json.loads(model_path.read_text(encoding="utf-8"))
            return DummyPolicyModel(
                capture_bonus=float(config.get("capture_bonus", config.get("prefer_capture_bonus", 100.0))),
                center_bonus=float(config.get("center_bonus", 1.0)),
                forward_bonus=float(config.get("forward_bonus", 0.25)),
            )
        raise ValueError(f"Unsupported ML model format: {model_path.suffix}")

    def _filtered_legal_moves(self, state: GameState) -> list[Move]:
        # Defensive filter: even if a future generator changes, MLAgent only returns moves accepted by rules.
        return [mv for mv in legal_moves(state) if is_legal_move(state, mv)]

    @staticmethod
    def _flatten_scores(raw_output: Any) -> list[float]:
        """Convert torch/numpy/list output to a flat Python float list."""
        if hasattr(raw_output, "detach"):
            raw_output = raw_output.detach().flatten().cpu().tolist()
        elif hasattr(raw_output, "flatten") and hasattr(raw_output, "tolist"):
            raw_output = raw_output.flatten().tolist()

        def _walk(obj: Any) -> list[float]:
            if isinstance(obj, (list, tuple)):
                out: list[float] = []
                for item in obj:
                    out.extend(_walk(item))
                return out
            try:
                value = float(obj)
            except Exception:
                value = float("-inf")
            if not math.isfinite(value):
                value = float("-inf")
            return [value]

        return _walk(raw_output)

    def _forward_policy_scores(self, state_tensor: Any) -> list[float]:
        if hasattr(self.model, "forward"):
            return self._flatten_scores(self.model.forward(state_tensor))  # type: ignore[attr-defined]
        raise AttributeError("Loaded ML model does not implement forward(state_tensor).")

    def _score_legal_moves(self, state: GameState, state_tensor: Any, moves: Sequence[Move]) -> list[float]:
        try:
            # Preferred Week 2 path: model forward returns action policy.
            policy_scores = self._forward_policy_scores(state_tensor)
            if len(policy_scores) == POLICY_SIZE:
                return [policy_scores[canonical_move_to_policy_index(mv, state.side_to_move)] for mv in moves]
            if len(policy_scores) == len(moves):
                return policy_scores
        except Exception:
            pass

        try:
            # Compatibility path for simple Week 1 score-only models.
            if hasattr(self.model, "score_moves"):
                raw_scores = self.model.score_moves(state_tensor, moves)  # type: ignore[attr-defined]
                legal_scores = self._flatten_scores(raw_scores)
                if len(legal_scores) == len(moves):
                    return legal_scores
        except Exception:
            pass

        # Safe fallback: never crash GameLoop because of a bad model output.
        return [0.0] * len(moves)

    def get_legal_move_scores(self, state: GameState) -> list[tuple[Move, float]]:
        """Debug/evaluation helper: expose the legal moves after model forward pass."""
        if state.side_to_move != self.player_id:
            raise ValueError(
                f"{self.name} was asked to evaluate {state.side_to_move.value}, "
                f"but it was initialized for {self.player_id.value}."
            )
        moves = self._filtered_legal_moves(state)
        if not moves:
            return []
        state_tensor = state_to_tensor(state, channels_first=True, canonical=True, as_numpy=False)
        scores = self._score_legal_moves(state, state_tensor, moves)
        return list(zip(moves, scores))

    def select_move(self, state: GameState) -> Optional[Move]:
        if state.side_to_move != self.player_id:
            raise ValueError(
                f"{self.name} was asked to play {state.side_to_move.value}, "
                f"but it was initialized for {self.player_id.value}."
            )

        move_scores = self.get_legal_move_scores(state)
        if not move_scores:
            return None

        # Stable argmax. If all scores are equal/invalid, Python keeps the first legal move.
        best_move, _best_score = max(move_scores, key=lambda item: item[1])
        return best_move
