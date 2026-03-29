# Design: Xiangqi Rules Engine

This document explains **how game rules are modeled and enforced** in this project. It is intended for developers and report readers who need a precise, implementation-aligned description (not only the human rules of Xiangqi).

**Primary code locations**

- `xiangqi-ai-project/core/rules.py`: Board constants, piece types, geometric predicates (palace, river, rays), initial setup helpers, general discovery and “facing generals” detection.
- `xiangqi-ai-project/core/move_generator.py`: Pseudo-legal move generation per piece, aggregation by color, **legal** move filtering (check + facing generals), check/terminal/validation APIs.
- `xiangqi-ai-project/core/state.py`: `GameState`: board, side to move, move history; `apply_move` / `undo_move` for reversible search and legality trials.
- `xiangqi-ai-project/core/board.py`: Grid storage, `get` / `set`, `move_piece`.
- `xiangqi-ai-project/tests/test_rules.py`: Regression tests for piece rules, check, pins, long-run random play.

---

## 1. Design goals

1. **Correctness**: Moves must satisfy standard Xiangqi piece movement **and** global constraints (no self-check, no facing generals).
2. **Clarity**: Separate **piece-local** geometry (`pseudo_legal_*`) from **position-wide** legality (`legal_moves`).
3. **Search-friendly**: Legal moves are verified with **apply / undo** on the real `GameState`, so AI and game loop share one source of truth.
4. **Robustness**: `Color` / `PieceType` enums are compared with **`==`** where values may be reconstructed (e.g. from persistence), avoiding `is` identity pitfalls.

---

## 2. Coordinate system and board invariants

- **Dimensions**: 10 rows × 9 columns (`BOARD_ROWS`, `BOARD_COLS`).
- **Position**: `Pos = (row, col)` with **0-based** indices.
- **Orientation**:
  - **Black** starts near **row 0**; **Red** near **row 9**.
  - Red “forward” is **decreasing** row (−1); Black “forward” is **increasing** row (+1). This is centralized in `soldier_forward_delta(color)`.
- **River**: Conceptually between row 4 and 5. A square is on **Red’s side** if `row >= 5`, and on **Black’s side** if `row <= 4` (`on_own_side_of_river`).
- **Palaces**: 3×3 boxes at each end — Red palace rows `7–9`, cols `3–5`; Black palace rows `0–2`, cols `3–5` (`palace_contains`).

All move generation first checks `in_bounds` for destinations (and for horse legs / elephant eyes where applicable).

---

## 3. Data model (`core/rules.py`)

- **`Piece`**: `(color: Color, kind: PieceType)` — immutable.
- **`PieceType`**: one of `GENERAL`, `ADVISOR`, `ELEPHANT`, `HORSE`, `ROOK`, `CANNON`, `SOLDIER`.

**Shared helpers**

- **`same_color` / `enemy_color`**: Used to decide captures; you cannot capture a friendly piece.
- **`ray_squares(src, dr, dc)`**: Yields squares in direction `(dr, dc)` until the board edge — used by rooks, cannons, and the general’s vertical “flying” capture ray.

**Facing generals**

- **`generals_face_each_other(board_get, red_general_pos, black_general_pos)`** is true when:
  - Both generals sit on the **same column**, and
  - Every square **strictly between** them on that column is **empty**.

This predicate defines the illegal **“two generals seeing each other”** position after a move.

**Initial position**

- **`initial_setup_piece_at(pos)`** maps each coordinate to the standard starting piece, or `None`. The `Board.initial()` constructor fills the grid from this function.

---

## 4. Move representation

- **`Move`**: `(src, dst, capture=None)` — `capture` records the piece taken for undo/history; legality matching in `is_legal_move` is by **`(src, dst)`** against `legal_moves`, not by trusting external capture metadata alone.

---

## 5. Pseudo-legal move generation

**Definition**: A move is **pseudo-legal** if it obeys **piece movement and board occupancy** (empty destination or enemy capture), **without** yet enforcing:

- Whether your own general is left in check, or  
- Whether the position has facing generals.

### 5.1 Implementation structure

- **`pseudo_legal_moves_for_piece(state, src)`**: Dispatches on `piece.kind` and emits `Move` objects.
- **`pseudo_legal_moves(state, color)`**: Loops all squares; for each piece matching `color`, extends with that piece’s pseudo-legal moves.

### 5.2 Piece rules (detailed)

#### Rook (`ROOK`)

- Moves along **rank or file** (four orthogonal directions).
- Slides through **empty** squares.
- **Stops** at the **first occupied** square: if it is an **enemy**, emits one **capture** move and stops; if friendly, emits nothing beyond that square (cannot move through or onto own pieces).

#### Cannon (`CANNON`)

- **Non-capturing**: Same sliding as rook, but only onto **empty** squares (stops at any occupied square without capturing it).
- **Capturing** (along one rank/file):
  - Scan from the cannon outward.
  - The first occupied square is a **screen** (any piece). After that, continue scanning.
  - The **first** piece encountered after the screen determines the outcome:
    - If it is an **enemy**, emit **one** capture move to that square and stop.
    - If it is friendly or the ray ends, no capture along that direction beyond the screen logic.
  - There must be **exactly one** screen between cannon and captured piece — implemented by a “screened” flag: first piece blocks non-capture sliding and becomes the screen; only after that can a capture happen.

#### Horse (`HORSE`)

- Eight knight-like “L” targets.
- For each L, define the **leg** (one orthogonal step toward the landing square). If the leg is **off-board** or **occupied**, that L is **illegal** (blocked horse).
- Landing uses `_yield_if_ok`: empty or enemy capture only.

#### Elephant (`ELEPHANT`)

- Two diagonal steps from the start (four directions).
- The **elephant’s eye** — the **intermediate** diagonal square — must be **empty**.
- The **destination** must lie on **own side of the river** (`on_own_side_of_river` for the moving piece’s color). So elephants never cross the river.

#### Advisor (`ADVISOR`)

- One diagonal step.
- Destination must be **inside own palace** (`palace_contains`).

#### General (`GENERAL`)

- **Normal moves**: One orthogonal step; destination must stay **inside own palace**.
- **Flying general** (optional rule in some descriptions; implemented here as in many engines):  
  Along a **vertical** direction from the general, if the first **non-empty** square encountered is the **enemy general**, emit a **capture** move to that square. This models the situation where the two generals would face each other with no pieces between — as a **capture** of the enemy general along the file.  
  Together with the global **facing generals** filter, this keeps positions consistent with “generals cannot see each other” except as a resolved capture when such a move is pseudo-legal and not filtered out.

#### Soldier (`SOLDIER`)

- **Forward** one step using `soldier_forward_delta(color)`.
- If the soldier’s **current** square is **not** on its own side of the river (`not on_own_side_of_river(color, src)`), it may also move **one step left or right** (sideways). **Backward** moves are never generated.

---

## 6. Legal moves: global constraints

**Definition**: **`legal_moves(state)`** returns moves for **`state.side_to_move`** that are pseudo-legal **and** satisfy:

1. **No self-check**  
   After the move, the side that moved must not have its general attacked by enemy pseudo-legal moves.

2. **No facing generals**  
   After the move, `generals_face_each_other` must be false (unless your model treats bare facing as always illegal — here the implementation **rejects** any post-move position where both generals see each other on an empty file).

### 6.1 Algorithm

For each candidate `m` from `pseudo_legal_moves(state, side_to_move)`:

1. `undo = state.apply_move(m)`
2. Evaluate:
   - `_is_in_check(state, side_to_move)` — note: `apply_move` flips `side_to_move`, so the **state** after the move is with the **opponent** to move; the check function still receives the **color that just moved** for the “is my general safe?” test — as implemented, `_is_in_check(state, color)` uses the board **after** the move and tests whether that color’s general is attacked by **enemy** pseudo-moves.
3. `_violates_facing_generals(state)`
4. `state.undo_move(undo)`
5. If neither illegal flag is set, append `m`.

This **make/unmake** pattern is standard and keeps one consistent board representation.

### 6.2 Check detection

- **`_is_in_check(state, color)`**:
  - If **no general** exists for that color → treated as **in check** (useful for terminal / corrupted states).
  - Else: if **any** move in `pseudo_legal_moves(state, color.other)` has `dst == general_square`, that general is in **check**.

Because pseudo-legal moves include captures toward the general square, this captures attacks by rook, cannon, horse, soldier, advisor, elephant (within range), and flying general when applicable.

---

## 7. Terminal outcomes and validation

- **`result_if_terminal(state)`**: If `legal_moves` is **empty**:
  - If side to move is in **check** → **checkmate** (winner = opponent).
  - Else → **stalemate** (here: **draw**, `winner=None` — document this if your rules require stalemate as loss for the stalemated side; Xiangqi varies by convention).

- **`is_terminal` / `get_winner`**: Also account for **missing general** (material win/loss) in addition to checkmate/stalemate logic.

- **`is_legal_move` / `assert_legal_move`**: For UI/engine input, verify `(src, dst)` against `legal_moves` (same turn and piece at `src`).

---

## 8. Layering: `GameState` vs rules module

- **`GameState`** (`core/state.py`) owns **who moves next**, **board**, and **history**. It may delegate to `move_generator` for `get_legal_moves`, `is_check`, `is_terminal` depending on version — keep a single authoritative path for AI (`legal_moves` from `move_generator`).

- **`rules.py`** intentionally does **not** depend on `GameState` for heavy logic — it only provides **pure predicates** and **geometry**, which keeps import cycles manageable and tests simple.




