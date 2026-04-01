# XiangQi Chess HCMUT - Design Draft

## 1. Project Goal
Build a XiangQi (Chinese Chess) game for the AI assignment with:
- legal move generation
- multiple agents
- search-based AI with 3 difficulty levels
- playable user mode
- basic evaluation and benchmarking
- UI demo using Pygame

---

## 2. Folder Responsibilities

### `core/`
Responsible for game data and rules:
- `board.py`: board representation
- `move.py`: move object
- `move_generator.py`: generate legal moves
- `rules.py`: piece movement rules
- `state.py`: full game state and transitions

### `agents/`
Responsible for move decision logic:
- `base_agent.py`: common agent interface
- `human_player.py`: move comes from UI input
- `random_agent.py`: choose legal move randomly
- `search_agent.py`: minimax / alpha-beta / heuristic

### `game/`
Responsible for match flow:
- `game_loop.py`: manages turns, applies moves, checks game over

### `ui/`
Responsible for display and interaction:
- `game_ui.py`: draw board, pieces, status, clicks
- `menu.py`: choose mode and difficulty
- `assets/`: images, icons, optional audio

### `evaluation/`
Responsible for benchmarking:
- `benchmark.py`
- `evaluate.py`
- `results/`

### `docs/`
Project design and report materials.

---

## 3. Level 1 UI Scope
This Level 1 scaffold focuses on:
- creating a Pygame window
- creating a main loop
- drawing an empty XiangQi board
- drawing demo pieces
- selecting cells by mouse
- highlighting selected cells
- selecting mode and level in menu
- reset and back-to-menu actions

This level is intentionally independent from the actual `core/` implementation.

---

## 4. Expected Interfaces for Integration

### Game State
Suggested minimum interface:
- `state.board`
- `state.current_player`
- `state.apply_move(move)`
- `state.clone()`
- `state.generate_legal_moves()`
- `state.is_terminal()`
- `state.get_winner()`

### Move
Suggested minimum fields:
- `from_row`
- `from_col`
- `to_row`
- `to_col`

### Agent
Suggested minimum interface:
- `select_move(state) -> Move`

---

## 5. Main Flow
1. `main.py` starts Pygame
2. App enters menu state
3. User selects mode and level
4. App enters game state
5. `GameUI` draws board and pieces
6. In later stages, UI connects to `game_loop.py` and `core/state.py`

---

## 6. Future UI Integration Plan
Level 2:
- replace demo pieces with real `state.board`
- support real legal moves from `move_generator.py`
- apply moves through `game_loop.py`

Level 3:
- integrate Human vs AI / AI vs AI / AI vs Random
- show game over result
- add evaluation buttons or benchmark launching hooks

---

## 7. Current Limitations
- no real game logic yet
- no rule validation yet
- demo movement currently allows moving any displayed piece
- no actual AI integration yet

This is acceptable for Level 1 because the focus is UI scaffold and structure.

---

## 8. AI Architecture & Strategy Pattern

### Core Agent Design
The decision-making process is abstracted using the **Strategy Pattern**. The overarching base class for both human inputs and programmatic intelligent models is located in `agents/base_agent.py`. It establishes a unified interface:
- `select_move(state) -> Move`: A strict requirement where the agent absorbs the current `state` of the board and synchronously outputs a valid `Move`. This architectural guarantee ensures the core game loop operates completely agnostically of the agent's identity (human vs machine).

### Agent Types
- **Human Player (`human_player.py`)**: Interfaces tightly with the UI. The `select_move` function asynchronously utilizes Pygame events and user interactions to parse cell selections and dispatch the user's intentional move.
- **Random Baseline (`random_agent.py`)**: Acts as a chaotic, zero-tier algorithmic opponent. It inherently requests all legal moves and uniformly selects a random index. This is fundamentally useful for early-stage framework validation and as a low-bar opponent for AI benchmarking (`AI vs Random`).
- **Search AI Engine (`search_agent.py`)**: The primary intellectual adversary. It incorporates a sophisticated, multi-layered approach using deterministic Game Tree navigation:
  - **Minimax with Alpha-Beta Pruning**: Drastically reduces the exponential search space, mathematically pruning sub-optimal transpositions to search deeper efficiently.
  - **Dynamic Depth Constraints**: Difficulty configurations automatically dictate how far ahead the AI simulates the game tree (e.g., Depth 2 vs Depth 5+).
  - **Heuristic Evaluation**: Upon reaching a terminal search leaf (or maximum depth constraint), it mathematically evaluates the board's positional score alongside individual unit structural strengths (e.g., Rook > Cannon > Pawn), calculating an overarching localized board score.

### Lifecycle of AI Execution
1. The Game Loop queries the current player for an action.
2. `agent.select_move(state)` is natively invoked.
3. The `search_agent` executes `state.clone()` multiple times to safely instantiate isolated virtual game spaces.
4. Through internal mechanisms like `state.generate_legal_moves()`, it retrieves the action space bounds.
5. In the virtual clone space, it simulates tactical branches sequentially via `state.apply_move(move)`.
6. Once the search mechanism exhausts its search depth boundary or isolates a specific checkmate state, the highest evaluated `Move` propagates upward.
7. The returned move is structurally transmitted back to the core `game_loop.py`, which securely updates the primary `state.board` and subsequently cues the UI to render the modified state.

---

## 9. Rules Engine Architecture

This section explains **how game rules are modeled and enforced** in this project. It is intended for developers and report readers who need a precise, implementation-aligned description (not only the human rules of Xiangqi).

**Primary code locations**

- `xiangqi-ai-project/core/rules.py`: Board constants, piece types, geometric predicates (palace, river, rays), initial setup helpers, general discovery and “facing generals” detection.
- `xiangqi-ai-project/core/move_generator.py`: Pseudo-legal move generation per piece, aggregation by color, **legal** move filtering (check + facing generals), check/terminal/validation APIs.
- `xiangqi-ai-project/core/state.py`: `GameState`: board, side to move, move history; `apply_move` / `undo_move` for reversible search and legality trials.
- `xiangqi-ai-project/core/board.py`: Grid storage, `get` / `set`, `move_piece`.
- `xiangqi-ai-project/tests/test_rules.py`: Regression tests for piece rules, check, pins, long-run random play.

### 9.1 Design Goals

1. **Correctness**: Moves must satisfy standard Xiangqi piece movement **and** global constraints (no self-check, no facing generals).
2. **Clarity**: Separate **piece-local** geometry (`pseudo_legal_*`) from **position-wide** legality (`legal_moves`).
3. **Search-friendly**: Legal moves are verified with **apply / undo** on the real `GameState`, so AI and game loop share one source of truth.
4. **Robustness**: `Color` / `PieceType` enums are compared with **`==`** where values may be reconstructed (e.g. from persistence), avoiding `is` identity pitfalls.

### 9.2 Coordinate System and Board Invariants

- **Dimensions**: 10 rows × 9 columns (`BOARD_ROWS`, `BOARD_COLS`).
- **Position**: `Pos = (row, col)` with **0-based** indices.
- **Orientation**:
  - **Black** starts near **row 0**; **Red** near **row 9**.
  - Red “forward” is **decreasing** row (−1); Black “forward” is **increasing** row (+1). This is centralized in `soldier_forward_delta(color)`.
- **River**: Conceptually between row 4 and 5. A square is on **Red’s side** if `row >= 5`, and on **Black’s side** if `row <= 4` (`on_own_side_of_river`).
- **Palaces**: 3×3 boxes at each end — Red palace rows `7–9`, cols `3–5`; Black palace rows `0–2`, cols `3–5` (`palace_contains`).

All move generation first checks `in_bounds` for destinations (and for horse legs / elephant eyes where applicable).

### 9.3 Data Model (`core/rules.py`)

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

### 9.4 Move Representation

- **`Move`**: `(src, dst, capture=None)` — `capture` records the piece taken for undo/history; legality matching in `is_legal_move` is by **`(src, dst)`** against `legal_moves`, not by trusting external capture metadata alone.

### 9.5 Pseudo-Legal Move Generation

**Definition**: A move is **pseudo-legal** if it obeys **piece movement and board occupancy** (empty destination or enemy capture), **without** yet enforcing:

- Whether your own general is left in check, or  
- Whether the position has facing generals.

#### 9.5.1 Implementation Structure

- **`pseudo_legal_moves_for_piece(state, src)`**: Dispatches on `piece.kind` and emits `Move` objects.
- **`pseudo_legal_moves(state, color)`**: Loops all squares; for each piece matching `color`, extends with that piece’s pseudo-legal moves.

#### 9.5.2 Piece Rules (Detailed)

##### Rook (`ROOK`)
- Moves along **rank or file** (four orthogonal directions).
- Slides through **empty** squares.
- **Stops** at the **first occupied** square: if it is an **enemy**, emits one **capture** move and stops; if friendly, emits nothing beyond that square (cannot move through or onto own pieces).

##### Cannon (`CANNON`)
- **Non-capturing**: Same sliding as rook, but only onto **empty** squares (stops at any occupied square without capturing it).
- **Capturing** (along one rank/file):
  - Scan from the cannon outward.
  - The first occupied square is a **screen** (any piece). After that, continue scanning.
  - The **first** piece encountered after the screen determines the outcome:
    - If it is an **enemy**, emit **one** capture move to that square and stop.
    - If it is friendly or the ray ends, no capture along that direction beyond the screen logic.
  - There must be **exactly one** screen between cannon and captured piece — implemented by a “screened” flag: first piece blocks non-capture sliding and becomes the screen; only after that can a capture happen.

##### Horse (`HORSE`)
- Eight knight-like “L” targets.
- For each L, define the **leg** (one orthogonal step toward the landing square). If the leg is **off-board** or **occupied**, that L is **illegal** (blocked horse).
- Landing uses `_yield_if_ok`: empty or enemy capture only.

##### Elephant (`ELEPHANT`)
- Two diagonal steps from the start (four directions).
- The **elephant’s eye** — the **intermediate** diagonal square — must be **empty**.
- The **destination** must lie on **own side of the river** (`on_own_side_of_river` for the moving piece’s color). So elephants never cross the river.

##### Advisor (`ADVISOR`)
- One diagonal step.
- Destination must be **inside own palace** (`palace_contains`).

##### General (`GENERAL`)
- **Normal moves**: One orthogonal step; destination must stay **inside own palace**.
- **Flying general**:  
  Along a **vertical** direction from the general, if the first **non-empty** square encountered is the **enemy general**, emit a **capture** move to that square. This models the situation where the two generals would face each other with no pieces between — as a **capture** of the enemy general along the file.  
  Together with the global **facing generals** filter, this keeps positions consistent with “generals cannot see each other” except as a resolved capture when such a move is pseudo-legal and not filtered out.

##### Soldier (`SOLDIER`)
- **Forward** one step using `soldier_forward_delta(color)`.
- If the soldier’s **current** square is **not** on its own side of the river (`not on_own_side_of_river(color, src)`), it may also move **one step left or right** (sideways). **Backward** moves are never generated.

### 9.6 Legal Moves: Global Constraints

**Definition**: **`legal_moves(state)`** returns moves for **`state.side_to_move`** that are pseudo-legal **and** satisfy:

1. **No self-check**  
   After the move, the side that moved must not have its general attacked by enemy pseudo-legal moves.
2. **No facing generals**  
   After the move, `generals_face_each_other` must be false (the implementation **rejects** any post-move position where both generals see each other on an empty file).

#### 9.6.1 Algorithm

For each candidate `m` from `pseudo_legal_moves(state, side_to_move)`:
1. `undo = state.apply_move(m)`
2. Evaluate:
   - `_is_in_check(state, side_to_move)`
3. `_violates_facing_generals(state)`
4. `state.undo_move(undo)`
5. If neither illegal flag is set, append `m`.

#### 9.6.2 Check Detection

- **`_is_in_check(state, color)`**:
  - If **no general** exists for that color → treated as **in check** (useful for terminal / corrupted states).
  - Else: if **any** move in `pseudo_legal_moves(state, color.other)` has `dst == general_square`, that general is in **check**.

### 9.7 Terminal Outcomes and Validation

- **`result_if_terminal(state)`**: If `legal_moves` is **empty**:
  - If side to move is in **check** → **checkmate** (winner = opponent).
  - Else → **stalemate** (implemented as draw, `winner=None`).
- **`is_terminal` / `get_winner`**: Also account for **missing general** (material win/loss) in addition to checkmate/stalemate logic.
- **`is_legal_move` / `assert_legal_move`**: For UI/engine input, verify `(src, dst)` against `legal_moves` (same turn and piece at `src`).

### 9.8 Layering: GameState vs Rules Module

- **`GameState`** (`core/state.py`) owns **who moves next**, **board**, and **history**. It may delegate to `move_generator` for `get_legal_moves`, `is_check`, `is_terminal` depending on version — keep a single authoritative path for AI (`legal_moves` from `move_generator`).
- **`rules.py`** intentionally does **not** depend on `GameState` for heavy logic — it only provides **pure predicates** and **geometry**, which keeps import cycles manageable and tests simple.

---

## 10. Demo Human Mode

This section clarifies the demo flow for the backend Human mode that is already supported by the current code.

### 10.1 Goal
The purpose of the demo is to show that a human player can participate in the game loop by entering moves from the terminal, while the opponent is controlled by another agent such as a random agent or a search-based AI.

### 10.2 Files Involved
- `agents/human_player.py`: reads and validates terminal input.
- `game/game_loop.py`: dispatches turns to the correct side, validates moves, and applies them to the game state.
- `agents/random_agent.py` or `agents/search_agent.py`: provides the opponent for the demo.

### 10.3 Demo Flow
1. Initialize a `HumanPlayer` for one side, typically Red.
2. Initialize an opponent agent for the other side.
3. Start the backend game loop with `run_game(red_agent, black_agent, ...)`.
4. When it is the human player’s turn, the terminal prompts for input in the format:
   - `src_row src_col dst_row dst_col`
5. If the input is malformed, the human agent prints an error and requests input again.
6. If the parsed move is not in the legal move set, the human agent reports an illegal move and asks again.
7. When a valid move is entered, the game loop applies it and switches to the opponent’s turn.
8. The process continues until a terminal result or the configured turn limit is reached.

### 10.4 Example Demo Configuration
A simple backend demo can use:
- Red: `HumanPlayer`
- Black: `RandomAgent`

This is sufficient to demonstrate human interaction, legal-move validation, and stable turn switching even before the full UI integration is completed.

### 10.5 Scope Note
This Human mode demo currently describes the backend / terminal flow rather than a full Pygame click-based interface. That is intentional: the backend path is already implemented and testable, while richer UI interaction can be integrated later without changing the core agent/game-loop contract.