# Team Rules - XiangQi Chess HCMUT

## 1. General Principles
- Work according to assigned files.
- Do not change another member's interface without informing the team.
- Keep code readable and modular.
- Prefer simple and stable interfaces over clever implementations.

---

## 2. File Ownership
### Trần Hoàng Vỹ Khang
- `main.py`
- `ui/game_ui.py`
- `ui/menu.py`
- `evaluation/evaluate.py`
- `evaluation/benchmark.py`
- UI/evaluation part of docs

### Other members
Follow the agreed table of responsibilities for `core/`, `agents/`, and `game/`.

---

## 3. Interface Rules

### State contract
Recommended:
- `state.board`
- `state.current_player`
- `state.apply_move(move)`
- `state.clone()`
- `state.generate_legal_moves()`
- `state.is_terminal()`
- `state.get_winner()`

### Move contract
Recommended fields:
- `from_row`
- `from_col`
- `to_row`
- `to_col`

### Agent contract
Each agent should implement:
- `select_move(state)`

---

## 4. Naming Convention
- file names: `snake_case.py`
- class names: `PascalCase`
- function names: `snake_case`
- constants: `UPPER_CASE`

Examples:
- `game_ui.py`
- `search_agent.py`
- `GameUI`
- `select_move`

---

## 5. Git Rules
- Each member works on their own branch.
- Suggested branch names:
  - `feature/ui-level1`
  - `feature/search-agent`
  - `feature/move-generator`
- Merge only when code runs without import error.
- Do not push broken code to main.

---

## 6. Commit Message Rule
Suggested format:
- `feat: add pygame main window`
- `feat: draw empty board`
- `fix: correct menu selection bug`
- `test: add UI smoke test`

---

## 7. Integration Rules
Before merging:
- check imports
- run the target file
- verify no syntax errors
- verify agreed interface is unchanged

If interface must change:
- announce in group chat
- update docs
- notify affected members

---

## 8. UI Integration Agreement
The UI team will first build a scaffold independent from `core`.
When `state.py` and `move.py` are stable, UI will connect using the agreed interface.

This avoids blocking progress in early development.

---

## 9. Testing Mindset
Minimum expectation:
- program opens without crash
- menu works
- board renders correctly
- selection highlight works

Later:
- UI reflects real state
- agents can move through UI
- benchmark runs and logs output

---

## 10. Final Submission Checklist
Before submission:
- source code is clean
- README is updated
- requirements are correct
- evaluation results are included
- demo flow is tested
- no dead files or broken imports remain