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