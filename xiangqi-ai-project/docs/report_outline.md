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

### 2.2 Game State and Board Management (`core/state.py`, `core/board.py`)

This subsection details the architectural design of the game’s "backbone," responsible for maintaining the board's integrity, handling move transitions, and providing efficient snapshots for the AI search engine.

#### 2.2.1 The Board Model (`core/board.py`)
The `Board` class encapsulates the physical grid and provides low-level manipulation methods:
* **Grid Storage**: Implemented as a 2D list `List[List[Optional[Piece]]]` to store piece objects or `None`.
* **Encapsulated Mutation**: Methods like `get(pos)`, `set(pos, piece)`, and `move_piece(src, dst)` centralize board changes.
* **Efficient Copying**: The `copy()` method performs a shallow copy of the grid rows, providing a fast way to duplicate states.

#### 2.2.2 The GameState Container (`core/state.py`)
The `GameState` class acts as the primary coordinator for the engine's status:
* **Status Tracking**: Maintains the current `Board`, `side_to_move`, and `move_history`.
* **Move Execution (`apply_move`)**: Updates the state by moving pieces and switching the active player, with strict validation for turn order.
* **State Reversion (`undo_move`)**: Restores the board and player turn using an `Undo` dataclass to support Alpha-Beta backtracking efficiently.

#### 2.2.3 Performance Optimizations for AI
Several optimizations were implemented to support the high-frequency requirements of the `SearchAgent`:
* **Lazy Importing**: Resolves **circular dependencies** between `state.py` and `move_generator.py` using local imports within methods.
* **Optimized Cloning**: The `clone()` method duplicates the board and history efficiently for independent search simulations.
* **Memory Efficiency**: Use of `__slots__` in `Undo` and `GameState` to reduce memory footprint.

### 2.3 Core Data Types (`core/rules.py`)

- **`Color`**: `RED` / `BLACK`. The property `other` returns the opponent color. Enum members are compared with **`==`** so that deserialized or reconstructed values still behave correctly.
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

### 2.4 Two-Stage Move Generation (`core/move_generator.py`)

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

### 2.5 Piece-Specific Movement Rules (Implementation Summary)

All piece branches use **`enemy_color`** for captures and **`_yield_if_ok`** for empty squares or enemy captures (never friendly capture).

- **Rook**: Slides orthogonally; **stops** at first occupied square; may capture first enemy on that ray.
- **Cannon**: Non-capture: slides like a rook on **empty** squares only. Capture: along a rank/file, there must be **exactly one** “screen” piece (any color) between cannon and **first** enemy piece captured; cannot jump multiple screens or capture without a screen.
- **Horse**: Eight “L” destinations; each has a **leg** square (one step orthogonally toward the destination). If the leg is occupied or out of bounds, that L is blocked.
- **Elephant**: Two diagonal steps; **elephant’s eye** (intermediate diagonal cell) must be empty; destination must remain on **own side of the river** (`on_own_side_of_river`).
- **Advisor**: One diagonal step; destination must lie inside **own palace**.
- **General**: One orthogonal step inside own palace; plus **flying general**: along the **vertical** file, if the first piece encountered is the **enemy general**, that capture is generated (only when the entire segment between the two generals has no other pieces — ensured by scanning ray until first blocker).
- **Soldier**: One step forward (`soldier_forward_delta`); after **crossing the river** (i.e. when not on own side), may also move one step **left or right** (not weapon backward).

### 2.6 Terminal State, Winner, and Move Validation

- **`result_if_terminal(state)`**: If there are **no legal moves** for the side to move:
  - If that side is **in check** → **checkmate** (winner = opponent).
  - Else → **stalemate** (implemented as draw: winner `None`).
- **`is_terminal(state)`**: True if a general is **missing** or `result_if_terminal` applies.
- **`get_winner(state)`**: Derives winner from missing general or from `result_if_terminal`.
- **`is_legal_move` / `assert_legal_move`**: Validate a proposed `Move` against **`legal_moves`** (by `src`/`dst`), for UI or engine input.

### 2.7 Implementation Notes and Pitfalls

- **Enum comparison**: `PieceType` / `Color` comparisons use **`==`** in move logic to avoid subtle bugs when values are reconstructed from external data.
- **`GameState.copy()`** aliases **`clone()`** for compatibility with older code/tests.
- **Separation of concerns**: `core/rules.py` holds **board geometry and shared predicates**; `core/move_generator.py` holds **move generation, legality filtering, and game outcome helpers**.
- **Circular Imports**: Managed by performing local imports within `GameState` methods to break the dependency cycle with `move_generator.py`.

### 2.8 Testing Strategy (`tests/test_rules.py`, `tests/test_state.py`)

Tests cover:

- Per-piece behaviour (rook block, horse leg, elephant river/eye, cannon screen, soldier directions, palace bounds).
- **Legal move filtering** (e.g. pinned rook, flying general capture when file is clear).
- **Check** scenarios (rook, cannon, horse, soldier, facing generals).
- **Apply/Undo Invariance**: Ensures board returns to initial state after sequence of actions.
- **Long-run random play**: Stress tests invariants during extended sessions.

---

## 3. Search / AI *(outline)*
### 3.1 Searching Algorithms

The decision-making core of the intelligent adversary relies on advanced game-tree exploration utilizing adversarial search paradigms.

#### 3.1.1 Minimax and Alpha-Beta Pruning
The foundational algorithmic framework is anchored upon the **Minimax algorithm**, strategically designed to simulate deterministic zero-sum outcomes. To radically mitigate the exponential combinatorial explosion intrinsic to the game tree of Xiangqi, **Alpha-Beta pruning** is intrinsically applied. This optimization mathematically eliminates sub-optimal tree branches, ensuring deeper computational foresight and drastically reduced inference latency without compromising decision integrity.

#### 3.1.2 Advanced Search Optimizations
To further amplify the temporal efficiency of the Alpha-Beta exploration, several auxiliary optimizations are implemented:
* **Heuristic Move Ordering (MVV-LVA)**: Employs the Most Valuable Victim - Least Valuable Attacker (MVV-LVA) sorting mechanism. By intuitively evaluating highly potent captures chronologically earlier in the search iteration, the model reliably incites early Alpha-Beta cut-offs.
* **Transposition Table and Zobrist Hashing**: To cleanly circumvent the computational redundancy of traversing identical board topologies reached through diverse transpositions (move permutations), the agent leverages continuous stochastic Zobrist Hashing. This reliably caches meticulously derived $\alpha/\beta$ bounds, traversed depth metrics, and specific terminal scores within an asynchronous dictionary framework.
* **Evaluation Caching**: Identical terminal node arrays are autonomously cached to mathematically bypass the repetitive infrastructural overhead of recalculating complex static positional evaluations.

#### 3.1.3 Static Evaluation Heuristics
The non-terminal leaf nodes of the bounded search tree are uniformly quantified utilizing deterministic static heuristics.
* **Material Matrix (Basic)**: A linear aggregation derived from globally empirical piece values: General (10,000), Rook (900), Cannon (450), Horse (400), Elephant/Advisor (200), Soldier (100).
* **Positional Strategy (Advanced)**: Dynamic mathematical multipliers are functionally integrated into the baseline material score to prioritize tactical variables: pawn river crossings, central file rook control, knight mobility constrictions, and explicit palace architectural defense arrays.

#### 3.1.4 Difficulty Stratification (Levels)
The cognitive proficiency of the agent is dynamically regulated through the rigorous parameterization of adversarial traversal depths and heuristic utilization constraints:
* **Level 1 (Novice)**: Radically restricts the traversal depth horizon to precisely $(d=1)$. Evaluates exclusively under the Basic Material Matrix, inherently facilitating accessible, highly reactive play without structured strategic foresight.
* **Level 2 (Intermediate)**: Traversal depth is marginally expanded $(d=2 \to d=3)$ alongside activation of the Advanced Positional Heuristics. The agent formulates fundamental forcing sequences whilst balancing mathematical execution time.
* **Level 3 (Advanced/Expert)**: The theoretical capacity apex of the implemented search architecture. Temporal depth is strictly maximized ($d \ge 4$). Synthesizes the complete Transposition Table, strict Move Ordering validations, and comprehensive positional strategies to manifest highly unyielding, deeply calculative adversarial intelligence.

### 3.2 Modes and Agents

This subsection summarizes how the gameplay modes are organized and how each agent interacts with the game loop.

### 3.2.1 Common Agent Interface

All playable entities are treated as agents that expose a common method:

- `select_move(state) -> Optional[Move]`

The method receives the current `GameState` (cloned by the game loop before dispatch) and returns either:

- a legal `Move`, or
- `None` if the agent cannot provide a move.

This lightweight interface allows the same backend loop to run human-controlled play, random baseline play, and search-based AI play.

### 3.2.2 RandomAgent

`agents/random_agent.py` implements the baseline random rule-based agent required by the assignment. Its behavior is:

1. obtain all legal moves from the current state,
2. return `None` if no legal move exists,
3. otherwise choose one move uniformly at random.

Because the move is sampled only from `legal_moves(state)`, this agent is random but still rule-compliant. It is therefore suitable as the baseline opponent for later evaluation.

### 3.2.3 HumanPlayer

`agents/human_player.py` implements a terminal-based human agent. The player enters a move in the form:

`src_row src_col dst_row dst_col`

The agent then:

1. parses the input string,
2. converts it into a `Move` object,
3. compares the move against the current legal move set,
4. asks for another input if the format is invalid or the move is illegal.

This design keeps input validation inside the human agent while leaving turn management to the central game loop.

### 3.2.4 Game Modes

With a unified agent interface, the backend can support multiple gameplay modes by simply plugging different agents into the red and black sides:

- **Human vs AI**: one `HumanPlayer` and one search agent,
- **AI vs Random**: one search agent and one `RandomAgent`,
- **AI vs AI**: two search agents with possibly different levels.

The current backend is intentionally mode-agnostic: a mode is defined by the pair of agents passed to the loop, not by separate duplicated logic.

### 3.2.5 Game Loop Integration

`game/game_loop.py` is the coordinator for all modes. For each turn, it:

1. checks terminal conditions,
2. selects the current agent based on `state.side_to_move`,
3. requests a move from that agent,
4. validates the returned move with `assert_legal_move`,
5. applies the move and records the turn in history.

This keeps move generation, validation, and turn switching centralized in one backend path, which reduces mode-specific bugs and makes testing easier.

### 3.2.6 Testing Strategy for Modes

`tests/test_game_loop.py` focuses on behavior at the integration level:

- the correct agent is called on the correct turn,
- random vs random can run stably for multiple plies,
- invalid moves are rejected,
- human input can be retried until a valid legal move is entered,
- backend configurations corresponding to Human vs AI, AI vs Random, and AI vs AI all execute without crashing.

These tests do not attempt to measure playing strength. Instead, they verify that the backend mode wiring is correct before stronger search agents are integrated.

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