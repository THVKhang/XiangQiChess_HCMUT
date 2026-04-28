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


class MoveScoringModel(Protocol):
    """Minimal inference interface expected by MLAgent.

    A future PyTorch/TensorFlow model can be wrapped to implement this method.
    It receives the encoded state tensor and legal moves, then returns one score
    per legal move. Higher score means the move is preferred.
    """

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> Sequence[float]:
        ...


@dataclass(slots=True)
class DummyMoveScoringModel:
    """Deterministic placeholder model for Week 1 integration.

    The dummy model does not try to play well. It only proves that the ML agent
    can encode a GameState, ask a model-like object for scores, and map the best
    score back to one legal Move without crashing GameLoop.
    """

    prefer_capture_bonus: float = 100.0
    center_bonus: float = 1.0

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> list[float]:
        scores: list[float] = []
        center_r = (BOARD_ROWS - 1) / 2.0
        center_c = (BOARD_COLS - 1) / 2.0
        for idx, move in enumerate(legal_move_list):
            dst_r, dst_c = move.dst
            distance_to_center = abs(dst_r - center_r) + abs(dst_c - center_c)
            capture_score = self.prefer_capture_bonus if move.capture is not None else 0.0
            # Small deterministic tie-breaker keeps repeated runs reproducible.
            scores.append(capture_score - self.center_bonus * distance_to_center - idx * 1e-6)
        return scores


class TorchPolicyAdapter:
    """Optional adapter for a torch model saved as .pt/.pth.

    Contract for Week 2+:
    - the torch model receives a tensor shaped (1, 15, 10, 9);
    - it returns either:
      1) a flat policy of length 8100 = src_square(90) x dst_square(90), or
      2) scores already aligned with the legal-move list length.
    """

    def __init__(self, model_path: str | Path, device: str = "cpu") -> None:
        try:
            import torch  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on optional torch install
            raise RuntimeError("TorchPolicyAdapter requires PyTorch to load a .pt/.pth model.") from exc

        self._torch = torch
        self.device = device
        loaded = torch.load(str(model_path), map_location=device)
        self.model = loaded["model"] if isinstance(loaded, dict) and "model" in loaded else loaded
        if hasattr(self.model, "to"):
            self.model.to(device)
        if hasattr(self.model, "eval"):
            self.model.eval()

    @staticmethod
    def _move_index(move: Move) -> int:
        src_idx = move.src[0] * BOARD_COLS + move.src[1]
        dst_idx = move.dst[0] * BOARD_COLS + move.dst[1]
        return src_idx * (BOARD_ROWS * BOARD_COLS) + dst_idx

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> list[float]:
        torch = self._torch
        x = torch.tensor(state_tensor, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            output = self.model(x)
        if isinstance(output, (tuple, list)):
            output = output[0]
        output = output.detach().flatten().cpu()

        if output.numel() == len(legal_move_list):
            return [float(output[i]) for i in range(len(legal_move_list))]
        if output.numel() >= BOARD_ROWS * BOARD_COLS * BOARD_ROWS * BOARD_COLS:
            return [float(output[self._move_index(move)]) for move in legal_move_list]
        raise ValueError(
            "Unsupported model output shape for MLAgent: expected len(legal_moves) "
            "or flat 90x90 policy scores."
        )


class MLAgent(BaseAgent):
    """Machine-learning based agent adapter for the existing GameLoop.

    Week 1 goal: provide a stable Agent interface (`select_move`) that GameLoop
    can call exactly like Random/Search agents. The model can be a dummy scorer
    now and a trained policy network later.
    """

    def __init__(
        self,
        player_id: Color,
        model_path: str | Path | None = None,
        model: Optional[MoveScoringModel] = None,
        name: str = "MLAgent",
        device: str = "cpu",
        rng: Optional[random.Random] = None,
    ) -> None:
        super().__init__(player_id=player_id, name=name)
        self.device = device
        self.rng = rng if rng is not None else random.Random(0)
        self.model_path = Path(model_path) if model_path else None
        self.model = model if model is not None else self._load_model(self.model_path, device)

    def _load_model(self, model_path: Path | None, device: str) -> MoveScoringModel:
        if model_path is None:
            return DummyMoveScoringModel()
        if not model_path.exists():
            raise FileNotFoundError(f"ML model file not found: {model_path}")
        if model_path.suffix.lower() in {".pt", ".pth"}:
            return TorchPolicyAdapter(model_path=model_path, device=device)
        if model_path.suffix.lower() == ".json":
            config = json.loads(model_path.read_text(encoding="utf-8"))
            return DummyMoveScoringModel(
                prefer_capture_bonus=float(config.get("prefer_capture_bonus", 100.0)),
                center_bonus=float(config.get("center_bonus", 1.0)),
            )
        raise ValueError(f"Unsupported ML model format: {model_path.suffix}")

    def _filtered_legal_moves(self, state: GameState) -> list[Move]:
        # Defensive filter: keep only moves accepted by the rule engine.
        return [mv for mv in legal_moves(state) if is_legal_move(state, mv)]

    def _safe_score_moves(self, state_tensor: Any, moves: Sequence[Move]) -> list[float]:
        try:
            raw_scores = list(self.model.score_moves(state_tensor, moves))
        except Exception:
            # Model failure should not break gameplay; fallback to neutral scores.
            return [0.0] * len(moves)

        if len(raw_scores) != len(moves):
            # Invalid shape from model => fallback to deterministic legal choice.
            return [0.0] * len(moves)

        safe_scores: list[float] = []
        for score in raw_scores:
            try:
                value = float(score)
            except Exception:
                value = float("-inf")
            if not math.isfinite(value):
                value = float("-inf")
            safe_scores.append(value)
        return safe_scores

    def select_move(self, state: GameState) -> Optional[Move]:
        if state.side_to_move != self.player_id:
            raise ValueError(
                f"{self.name} was asked to play {state.side_to_move.value}, "
                f"but it was initialized for {self.player_id.value}."
            )

        moves = self._filtered_legal_moves(state)
        if not moves:
            return None

        state_tensor = state_to_tensor(
            state,
            channels_first=True,
            canonical=True,
            as_numpy=False,
        )
        safe_scores = self._safe_score_moves(state_tensor, moves)
        # Stable argmax. If all scores are equal/invalid, keep the first legal move.
        best_idx = max(range(len(moves)), key=lambda i: safe_scores[i])
        return moves[best_idx]
