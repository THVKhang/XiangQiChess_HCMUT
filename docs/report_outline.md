# Project Report — Outline

This document is a skeleton for the final report. The **Rules** section below is written in full detail; other sections can be expanded similarly.

---

## 1. Introduction

*(Project goals, team roles, repository layout — to be completed.)*

---

## 2. Game Rules Engine

This subsection explains how Xiangqi (Chinese chess) rules are represented and enforced in the codebase (`xiangqi-ai-project/core/rules.py`, `xiangqi-ai-project/core/move_generator.py`, and related tests).

### 2.1 Coordinate System and Board Model

- The board is a **10 × 9** grid: `BOARD_ROWS = 10`, `BOARD_COLS = 9`.
- Positions are tuples **`(row, col)`** with **0-based indexing**:
  - **Row 0** is the **Black** side (north); **row 9** is the **Red** side (south).
  - **Columns** run **0–8** (west to east).
- The **river** lies between **row 4** and **row 5** (i.e. pieces on rows `0–4` are on Black’s side; rows `5–9` on Red’s side, with the gap between 4 and 5 representing the river).

This convention matches the standard initial setup: Black general at `(0, 4)`, Red general at `(9, 4)`.

### 2.2 Core Data Types (`core/rules.py`)

- **`Color`**: `RED` / `BLACK`. The property `other` returns the opponent color. Enum members are compared with **`==`**  so that deserialized or reconstructed values still behave correctly.
- **`PieceType`**: `GENERAL`, `ADVISOR`, `ELEPHANT`, `HORSE`, `ROOK`, `CANNON`, `SOLDIER`.
- **`Piece`**: immutable `color` + `kind`.

Helper predicates used by move generation:

- `in_bounds(pos)`: Ensures `(row, col)` stays inside the board.
- `palace_contains(color, pos)`: **Palace (3×3)** for Red: rows `7–9`, cols `3–5`; for Black: rows `0–2`, cols `3–5`.
- `on_own_side_of_river(color, pos)`: Red: `row >= 5`; Black: `row <= 4`. Used for elephant river rule and soldier sideways moves.
- `soldier_forward_delta(color)`: Red moves “up” toward Black: **−1** row; Black moves “down”: **+1** row.
- `ray_squares(src, dr, dc)`: Iterates squares along a direction (rooks, cannons, flying general).
- `generals_face_each_other(board_get, red_g, black_g)`: True if both generals share a **file** (same column) and every square **strictly between** them is empty.
- `find_general(board_get, color)`: Locates the general’s square for a side.

**`initial_setup_piece_at(pos)`** returns the standard piece at each square, or `None` — used by `Board.initial()`.

### 2.3 Two-Stage Move Generation (`core/move_generator.py`)

The engine separates **geometric / piece rules** from **global Xiangqi constraints**.

#### Pseudo-legal moves

- **`pseudo_legal_moves_for_piece(state, src)`** generates moves for one piece according to its type only (including captures), **without** filtering:
  - leaving one’s own general in check, or  
  - creating **facing generals** (two generals on the same file with no piece between).

- **`pseudo_legal_moves(state, color)`** aggregates pseudo-legal moves for all pieces of that color.

#### Legal moves

- **`legal_moves(state)`** keeps only moves for **`state.side_to_move`** that, after a **trial** `apply_move` / `undo_move`, satisfy:
  1. **`not _is_in_check(state, side_to_move)`** — the moving side’s general must not be attacked after the move (no self-check, includes pinned pieces).
  2. **`not _violates_facing_generals(state)`** — the position must not have both generals “staring” at each other on an empty file.

#### Check detection

- **`_is_in_check(state, color)`**:
  - If that side has **no general** on the board, it is treated as **in check** (a practical terminal / illegal state flag).
  - Otherwise, if **any enemy pseudo-legal move** has destination equal to the friendly general’s square, the general is **in check**.
- **`is_check(state, color=None)`** exposes this for the side to move (or an explicit color).

**Note:** “Check” from **facing generals** is included because enemy pseudo-moves include the **flying general** capture along the file when the path is clear; thus both generals can be considered “in check” in that configuration, which matches the rule that such a position is forbidden for the side to move.

### 2.4 Piece-Specific Movement Rules (Implementation Summary)

All piece branches use **`enemy_color`** for captures and **`_yield_if_ok`** for empty squares or enemy captures (never friendly capture).

- **Rook**: Slides orthogonally; **stops** at first occupied square; may capture first enemy on that ray.
- **Cannon**: Non-capture: slides like a rook on **empty** squares only. Capture: along a rank/file, there must be **exactly one** “screen” piece (any color) between cannon and **first** enemy piece captured; cannot jump multiple screens or capture without a screen.
- **Horse**: Eight “L” destinations; each has a **leg** square (one step orthogonally toward the destination). If the leg is occupied or out of bounds, that L is blocked.
- **Elephant**: Two diagonal steps; **elephant’s eye** (intermediate diagonal cell) must be empty; destination must remain on **own side of the river** (`on_own_side_of_river`).
- **Advisor**: One diagonal step; destination must lie inside **own palace**.
- **General**: One orthogonal step inside own palace; plus **flying general**: along the **vertical** file, if the first piece encountered is the **enemy general**, that capture is generated (only when the entire segment between the two generals has no other pieces — ensured by scanning ray until first blocker).
- **Soldier**: One step forward (`soldier_forward_delta`); after **crossing the river** (i.e. when not on own side), may also move one step **left or right** (not backward).

### 2.5 Terminal State, Winner, and Move Validation

- **`result_if_terminal(state)`**: If there are **no legal moves** for the side to move:
  - If that side is **in check** → **checkmate** (winner = opponent).
  - Else → **stalemate** (implemented as draw: winner `None`).
- **`is_terminal(state)`**: True if a general is **missing** or `result_if_terminal` applies.
- **`get_winner(state)`**: Derives winner from missing general or from `result_if_terminal`.
- **`is_legal_move` / `assert_legal_move`**: Validate a proposed `Move` against **`legal_moves`** (by `src`/`dst`), for UI or engine input.

### 2.6 Implementation Notes and Pitfalls

- **Enum comparison**: `PieceType` / `Color` comparisons use **`==`** in move logic to avoid subtle bugs when values are reconstructed from external data.
- **`GameState.copy()`** aliases **`clone()`** for compatibility with older code/tests.
- **Separation of concerns**: `core/rules.py` holds **board geometry and shared predicates**; `core/move_generator.py` holds **move generation, legality filtering, and game outcome helpers**.

### 2.7 Testing Strategy (`tests/test_rules.py`)

Tests cover:

- Per-piece behaviour (rook block, horse leg, elephant river/eye, cannon screen, soldier directions, palace bounds).
- **Legal move filtering** (e.g. pinned rook, flying general capture when file is clear).
- **Check** scenarios (rook, cannon, horse, soldier, facing generals).
- **Long-run random play** with `legal_moves` + `apply_move` / `undo` to stress invariant “no illegal post-move state.”

---

## 3. Search / AI *(outline)*

*(Minimax, alpha-beta, heuristics, transposition table — to be completed.)*

---

## 4. User Interface / Game Loop *(outline)*

*(CLI, pygame, or web — to be completed.)*

---

## 5. Conclusion and Future Work *(outline)*

*(Performance, stronger evaluation, opening book — to be completed.)*

---

## References *(optional)*

- Xiangqi rules (e.g. Wikipedia, official federation rules) for human-readable rule description.
- Project source: `xiangqi-ai-project/core/rules.py`, `xiangqi-ai-project/core/move_generator.py`.
