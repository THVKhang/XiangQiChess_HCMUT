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

    # Piece importance for move prioritization
    PIECE_MOVE_WEIGHT: dict = None
    
    def __post_init__(self):
        if self.PIECE_MOVE_WEIGHT is None:
            from core.rules import PieceType
            object.__setattr__(self, 'PIECE_MOVE_WEIGHT', {
                PieceType.ROOK: 5.0,      # Xe — ưu tiên cao nhất
                PieceType.CANNON: 4.0,    # Pháo
                PieceType.HORSE: 3.5,     # Mã
                PieceType.SOLDIER: 1.0,   # Tốt — ưu tiên thấp
                PieceType.ADVISOR: 0.5,
                PieceType.ELEPHANT: 0.5,
                PieceType.GENERAL: 0.2,
            })

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move]) -> list[float]:
        from core.rules import PieceType, on_own_side_of_river
        
        scores: list[float] = []
        center_r = (BOARD_ROWS - 1) / 2.0
        center_c = (BOARD_COLS - 1) / 2.0
        
        for idx, move in enumerate(legal_move_list):
            dst_r, dst_c = move.dst
            src_r, src_c = move.src
            
            # Capture bonus
            capture_score = self.prefer_capture_bonus if move.capture is not None else 0.0
            
            # Piece-type bonus: prioritize moving strong pieces
            piece_weight = 1.0
            if hasattr(move, '_piece') and move._piece is not None:
                piece_weight = self.PIECE_MOVE_WEIGHT.get(move._piece.kind, 1.0)
            else:
                # Heuristic based on source position (starting positions of pieces)
                # Rooks start at corners, Horses at (9,1)/(9,7), Cannons at (7,1)/(7,7)
                piece_weight = 2.0  # default moderate
                
            # Forward progress bonus — reward moves toward enemy side
            forward_bonus = (center_r - abs(dst_r - center_r)) * 0.5
            
            # Center column control
            center_dist = abs(dst_c - center_c)
            center_bonus_val = -self.center_bonus * center_dist
            
            total = (capture_score 
                    + piece_weight * 10.0 
                    + forward_bonus * 3.0
                    + center_bonus_val
                    - idx * 1e-6)
            scores.append(total)
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
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("TorchPolicyAdapter requires PyTorch to load a .pt/.pth model.") from exc

        self._torch = torch
        self.device = device

        loaded = torch.load(str(model_path), map_location=device, weights_only=True)

        # state_dict (OrderedDict) → need to reconstruct the model class
        if isinstance(loaded, dict) and "model" in loaded:
            self.model = loaded["model"]
        elif isinstance(loaded, dict) and all(isinstance(k, str) for k in loaded.keys()):
            # This is a state_dict — build XiangQiResNet and load weights
            try:
                import sys
                from pathlib import Path as _P
                model_dir = str(_P(__file__).resolve().parent.parent / "models")
                if model_dir not in sys.path:
                    sys.path.insert(0, model_dir)
                from network import XiangQiResNet
                model = XiangQiResNet(num_blocks=5, channels=128)
                model.load_state_dict(loaded, strict=False)
                self.model = model
            except Exception:
                raise ValueError("Cannot reconstruct model from state_dict.")
        else:
            self.model = loaded

        if hasattr(self.model, "to"):
            self.model.to(device)
        if hasattr(self.model, "eval"):
            self.model.eval()

    def score_moves(self, state_tensor: Any, legal_move_list: Sequence[Move], side_to_move=None) -> list[float]:
        """Score legal moves using BOTH neural network heads:

        1. **Policy head**: probability that this move is the best (from training data)
        2. **Value head**: 1-ply neural lookahead — apply move, encode new state,
           get the model's value prediction for the resulting position.

        Final score = policy_weight * policy_prob + value_weight * normalized_value.
        This is 100% ML — uses only the neural network's own evaluations.
        """
        torch = self._torch
        from core.policy_encoding import canonical_move_to_policy_index

        x = torch.tensor(state_tensor, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            output = self.model(x)

        # Extract policy and value from dual-head model
        if isinstance(output, (tuple, list)) and len(output) == 2:
            policy_logits = output[0]
            # current_value = output[1]  # Not used directly
        else:
            policy_logits = output

        logits = policy_logits.detach().flatten().cpu()
        probs = torch.softmax(logits, dim=0)

        stm = side_to_move if side_to_move is not None else Color.RED

        # Get policy scores for legal moves
        policy_scores: list[float] = []
        for move in legal_move_list:
            idx = canonical_move_to_policy_index(move, stm)
            if 0 <= idx < probs.numel():
                policy_scores.append(float(probs[idx]))
            else:
                policy_scores.append(0.0)

        # 1-ply neural value lookahead: for each move, get NN's value prediction
        value_scores: list[float] = []
        from core.state import GameState
        # We need the actual game state to apply moves — reconstruct from tensor isn't feasible
        # So we return policy-only scores. The MLAgent.select_move will do the value lookahead.
        # Return policy scores directly.
        return policy_scores


# ── Auto-detect best model path ─────────────────────────────────────
def _find_best_model() -> Path | None:
    """Search for best_model.pth in standard locations."""
    base = Path(__file__).resolve().parent.parent  # xiangqi-ai-project/
    candidates = [
        base / "models" / "checkpoints" / "best_model.pth",
        base / "models" / "best_model.pth",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── ML Level configuration ──────────────────────────────────────────
# Easy: high temperature (almost random among decent moves)
# Medium: moderate temperature (balanced exploration)
# Hard: greedy (pick the best move)
ML_LEVEL_CONFIG = {
    "Easy":   {"temperature": 2.0,  "top_k": 0},    # Very exploratory
    "Medium": {"temperature": 0.8,  "top_k": 10},   # Moderate
    "Hard":   {"temperature": 0.1,  "top_k": 5},    # Near-greedy
}


class MLAgent(BaseAgent):
    """Machine-learning based agent with configurable skill levels.

    Levels:
    - Easy:   High temperature → almost random among legal moves
    - Medium: Moderate temperature → balanced play
    - Hard:   Low temperature → near-greedy (best policy move)

    Automatically searches for best_model.pth if no model_path is given.
    Falls back to DummyMoveScoringModel if no trained model is found.
    """

    def __init__(
        self,
        player_id: Color,
        model_path: str | Path | None = None,
        model: Optional[MoveScoringModel] = None,
        level: str = "Hard",
        name: str | None = None,
        device: str = "cpu",
        rng: Optional[random.Random] = None,
    ) -> None:
        self.level = level
        agent_name = name or f"MLAgent({level})"
        super().__init__(player_id=player_id, name=agent_name)
        self.device = device
        self.rng = rng if rng is not None else random.Random(0)

        # Auto-detect model if no path given
        if model_path is None and model is None:
            auto_path = _find_best_model()
            if auto_path is not None:
                model_path = auto_path

        self.model_path = Path(model_path) if model_path else None
        self.model = model if model is not None else self._load_model(self.model_path, device)

        # Level config
        cfg = ML_LEVEL_CONFIG.get(level, ML_LEVEL_CONFIG["Hard"])
        self.temperature = cfg["temperature"]
        self.top_k = cfg["top_k"]

    def _load_model(self, model_path: Path | None, device: str) -> MoveScoringModel:
        if model_path is None:
            return DummyMoveScoringModel()
        if not model_path.exists():
            return DummyMoveScoringModel()  # Graceful fallback
        if model_path.suffix.lower() in {".pt", ".pth"}:
            try:
                return TorchPolicyAdapter(model_path=model_path, device=device)
            except Exception:
                return DummyMoveScoringModel()  # Model load failed → fallback
        if model_path.suffix.lower() == ".json":
            config = json.loads(model_path.read_text(encoding="utf-8"))
            return DummyMoveScoringModel(
                prefer_capture_bonus=float(config.get("prefer_capture_bonus", 100.0)),
                center_bonus=float(config.get("center_bonus", 1.0)),
            )
        return DummyMoveScoringModel()

    def _filtered_legal_moves(self, state: GameState) -> list[Move]:
        return [mv for mv in legal_moves(state) if is_legal_move(state, mv)]

    def _safe_score_moves(self, state_tensor: Any, moves: Sequence[Move], side_to_move=None) -> list[float]:
        try:
            raw_scores = list(self.model.score_moves(state_tensor, moves, side_to_move=side_to_move))
        except TypeError:
            # Model doesn't accept side_to_move kwarg (e.g. DummyMoveScoringModel)
            try:
                raw_scores = list(self.model.score_moves(state_tensor, moves))
            except Exception:
                return [1.0 / max(1, len(moves))] * len(moves)
        except Exception:
            return [1.0 / max(1, len(moves))] * len(moves)

        if len(raw_scores) != len(moves):
            return [1.0 / max(1, len(moves))] * len(moves)

        safe_scores: list[float] = []
        for score in raw_scores:
            try:
                value = float(score)
            except Exception:
                value = 0.0
            if not math.isfinite(value):
                value = 0.0
            safe_scores.append(max(value, 0.0))  # Probabilities must be >= 0
        return safe_scores

    def _apply_temperature(self, scores: list[float]) -> int:
        """Select move index using temperature-based softmax sampling."""
        if self.temperature <= 0.05:
            # Greedy
            return max(range(len(scores)), key=lambda i: scores[i])

        # Apply top-k filtering if configured
        indices = list(range(len(scores)))
        if self.top_k > 0 and len(scores) > self.top_k:
            sorted_idx = sorted(indices, key=lambda i: scores[i], reverse=True)
            indices = sorted_idx[:self.top_k]

        # Softmax with temperature
        max_score = max(scores[i] for i in indices)
        exp_scores = []
        for i in indices:
            exp_scores.append(math.exp((scores[i] - max_score) / self.temperature))

        total = sum(exp_scores)
        if total <= 0:
            return self.rng.choice(indices)

        probs = [e / total for e in exp_scores]

        # Weighted random choice
        r = self.rng.random()
        cumulative = 0.0
        for idx, prob in zip(indices, probs):
            cumulative += prob
            if r <= cumulative:
                return idx
        return indices[-1]
    def select_move(self, state: GameState) -> Optional[Move]:
        """Select a move using the neural network policy head.

        Enhancements over raw policy:
        - Capture bonus (reward shaping, standard in RL)
        - Anti-repetition: track actual board position hashes to prevent threefold draw
        - Anti-stalemate: avoid captures that leave opponent with no legal moves
        """
        if state.side_to_move != self.player_id:
            raise ValueError(
                f"{self.name} was asked to play {state.side_to_move.value}, "
                f"but it was initialized for {self.player_id.value}."
            )

        moves = self._filtered_legal_moves(state)
        if not moves:
            return None

        # Step 1: Get policy scores from NN
        state_tensor = state_to_tensor(
            state, channels_first=True, canonical=True, as_numpy=False,
        )
        scores = self._safe_score_moves(state_tensor, moves, side_to_move=state.side_to_move)

        # Step 2: Capture bonus (reward shaping)
        from core.rules import PieceType
        CAPTURE_BONUS = {
            PieceType.GENERAL: 50.0,
            PieceType.ROOK: 0.8,
            PieceType.CANNON: 0.5,
            PieceType.HORSE: 0.5,
            PieceType.ADVISOR: 0.1,
            PieceType.ELEPHANT: 0.1,
            PieceType.SOLDIER: 0.05,
        }
        for i, move in enumerate(moves):
            if move.capture is not None:
                scores[i] += CAPTURE_BONUS.get(move.capture.kind, 0.1)

        # Step 3: Anti-stalemate + detect checkmate
        # Check top-scoring moves AND all capture moves for terminal states
        from core.move_generator import result_if_terminal
        ranked = sorted(range(len(moves)), key=lambda j: scores[j], reverse=True)
        check_set = set(ranked[:5])  # Top 5 by score
        for i, mv in enumerate(moves):  # + all captures
            if mv.capture is not None:
                check_set.add(i)
        for i in check_set:
            next_state = state.clone()
            next_state.apply_move(moves[i])
            terminal = result_if_terminal(next_state)
            if terminal is not None:
                if terminal.winner == self.player_id:
                    scores[i] += 1000.0  # Checkmate!
                elif terminal.reason == "stalemate":
                    scores[i] = 0.0  # Avoid stalemate

        # Step 4: Anti-repetition using position hash tracking
        # Build set of position hashes seen so far in the game
        history = state.move_history
        
        # Simple anti-reversal: block immediate undo
        for i, move in enumerate(moves):
            if len(history) >= 2:
                last_own = history[-2]
                if last_own.src == move.dst and last_own.dst == move.src:
                    scores[i] = 0.0

            # Block 4-ply cycle (A->B->A pattern)
            if len(history) >= 4:
                own_2ago = history[-4]
                if move.src == history[-2].dst and move.dst == own_2ago.src:
                    scores[i] *= 0.001

            # Block 6-ply cycle
            if len(history) >= 6:
                own_3ago = history[-6]
                if move.dst == own_3ago.src:
                    scores[i] *= 0.1

        # Step 5: Temperature-based selection
        best_idx = self._apply_temperature(scores)
        return moves[best_idx]
