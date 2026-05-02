# XiangQiChess_HCMUT

Xiangqi (Chinese Chess) project for the Introduction to Artificial Intelligence course.

This project focuses on **search-based game AI** (no machine learning), including:
- Depth search (Minimax)
- Heuristic search (Alpha-Beta + evaluation function)

## Key Features

- Full Xiangqi rule engine: legal move generation, check/checkmate, terminal detection.
- Multiple play modes:
    - Human vs AI
    - AI vs AI
    - AI vs Random
- AI difficulty levels:
    - Easy
    - Medium
    - Hard
- Endgame notifications in UI (win/draw).
- Threefold repetition draw handling.
- Automated tests for core logic, game loop, and agents.
- Evaluation scripts to benchmark AI and export results.

## AI Setup (Current)

- Human vs AI:
    - Human: Red
    - AI: Black (search agent with selected difficulty)
- AI vs Random:
    - Red: Search AI
    - Black: Random agent
- AI vs AI:
    - Red AI: Heuristic search (Alpha-Beta)
    - Black AI: Depth search (Minimax)
    - Supports separate Red/Black difficulty selection

## Project Structure

```text
xiangqi-ai-project/
    main.py
    agents/
        base_agent.py
        human_player.py
        random_agent.py
        search_agent.py
    core/
        board.py
        move.py
        move_generator.py
        rules.py
        state.py
    game/
        game_loop.py
    ui/
        game_ui.py
        menu.py
        assets/
    evaluation/
        benchmark.py
        evaluate.py
        results/
    tests/
        test_agents.py
        test_game_loop.py
        test_moves.py
        test_rules.py
        test_state.py
    docs/
        design.md
        report_outline.md
        team_rules.md
```

## Requirements

- Python 3.10+
- pygame

Install dependencies:

```bash
pip install pygame
```

## Run The Game

```bash
cd xiangqi-ai-project
python main.py
```

## Run Tests

Run all tests:

```bash
cd xiangqi-ai-project
python -m unittest discover -s tests -p "test_*.py"
```

Run agent tests only:

```bash
python -m unittest tests.test_agents
```

## Evaluation / Benchmark

Run evaluation and save results (JSON/CSV):

```bash
cd xiangqi-ai-project
python evaluation/evaluate.py
```

Output files are saved in:

- `xiangqi-ai-project/evaluation/results/`

## Course MVP Checklist

- Rule-correct gameplay engine.
- Search-only AI (no ML).
- Multiple skill levels.
- AI evaluation workflow and reproducible test runs.

---

If you are reviewing this project for demo/presentation, start with:
1. `python main.py`
2. Switch between modes and levels
3. `python -m unittest discover -s tests -p "test_*.py"`
4. `python evaluation/evaluate.py`
