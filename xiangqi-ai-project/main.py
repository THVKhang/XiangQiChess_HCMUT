import sys
import threading
import pygame

from agents.ml_agent import MLAgent
from agents.random_agent import RandomAgent
from agents.search_agent import EasyAgent, HardAgent, MediumAgent
from core.move import Move
from core.move_generator import assert_legal_move, result_if_terminal
from core.rules import Color
from core.state import GameState
from ui.game_ui import GameUI
from ui.menu import Menu


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 760
FPS = 67


def _build_search_agent(level: str, color: Color, algorithm: str = "alphabeta"):
    level_map = {
        "Easy": EasyAgent,
        "Medium": MediumAgent,
        "Hard": HardAgent,
    }
    agent_cls = level_map.get(level, EasyAgent)
    return agent_cls(player_id=color, algorithm=algorithm)

def _build_ml_agent(color: Color, ml_level: str = "Hard", model_path: str = None):
    return MLAgent(player_id=color, level=ml_level, model_path=model_path)


def _build_agents(mode: str, level: str, red_level: str = None, black_level: str = None, ml_level: str = "Hard"):
    if mode == "Human vs AI":
        return Color.RED, None, _build_search_agent(level, Color.BLACK, algorithm="alphabeta")
    if mode == "Human vs ML":
        return Color.RED, None, _build_ml_agent(Color.BLACK, ml_level=ml_level)
    if mode == "AI vs Random":
        return None, _build_search_agent(level, Color.RED, algorithm="alphabeta"), RandomAgent(player_id=Color.BLACK)
    if mode == "ML vs Random":
        return None, _build_ml_agent(Color.RED, ml_level=ml_level), RandomAgent(player_id=Color.BLACK)
    if mode == "ML vs Search":
        return None, _build_ml_agent(Color.RED, ml_level=ml_level), _build_search_agent(level, Color.BLACK, algorithm="alphabeta")
    if mode == "AI vs AI":
        red_lv = red_level or level
        black_lv = black_level or level
        red_agent = _build_search_agent(red_lv, Color.RED, algorithm="alphabeta")
        black_agent = _build_search_agent(black_lv, Color.BLACK, algorithm="minimax")
        return None, red_agent, black_agent

    return Color.RED, None, _build_search_agent(level, Color.BLACK, algorithm="alphabeta")


def _rebuild_state_without_last_move(state: GameState) -> GameState:
    if not state.move_history:
        return GameState()

    rebuilt = GameState()
    for mv in state.move_history[:-1]:
        rebuilt.apply_move(Move(src=mv.src, dst=mv.dst))
    return rebuilt


def _position_key(state: GameState):
    pieces = []
    for pos, piece in state.board.squares():
        if piece is None:
            continue
        pieces.append((pos, piece.color.value, piece.kind.value))
    pieces.sort()
    return state.side_to_move.value, tuple(pieces)


def _rebuild_position_counts(state: GameState):
    replay = GameState()
    counts = {_position_key(replay): 1}
    for mv in state.move_history:
        replay.apply_move(Move(src=mv.src, dst=mv.dst))
        key = _position_key(replay)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _format_moves_for_ui(state: GameState) -> list[str]:
    return [f"{m.src} → {m.dst}" for m in state.move_history]

def _start_ai_worker(agent, state_snapshot, request_id, result_store):
    """Run AI search in background and store result with request id."""
    try:
        move = agent.select_move(state_snapshot)
        result_store["move"] = move
        result_store["error"] = None
    except Exception as exc:
        result_store["move"] = None
        result_store["error"] = str(exc)
    result_store["request_id"] = request_id


def main():
    pygame.init()
    pygame.display.set_caption("XiangQi Chess - HCMUT")
    fullscreen = False
    width, height = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    ai_thread = None
    ai_move_result = {"move": None, "error": None, "request_id": 0}
    ai_thinking = False
    ai_agent = None
    ai_request_id = 0

    menu = Menu(WINDOW_WIDTH, WINDOW_HEIGHT)
    game_ui = GameUI(WINDOW_WIDTH, WINDOW_HEIGHT)

    state = GameState()
    human_color = Color.RED
    red_agent = None
    black_agent = None
    undo_stack: list = []
    game_ui.move_undo_stack = undo_stack

    app_state = "menu"
    running = True
    game_over_reason = None

    ai_cooldown_ms = 260
    ai_elapsed_ms = 0
    processed_plies = 0
    position_counts = {_position_key(state): 1}

    move_history_display: list[str] = []
    saved_game = None
    theme_dark = {
        "background_color": (40, 40, 40),
        "panel_color": (60, 60, 60),
        "line_color": (200, 200, 200),
        "red_color": (255, 80, 80),
        "black_color": (200, 200, 200),
    }
    theme_light = {
        "background_color": (242, 210, 140),
        "panel_color": (245, 240, 230),
        "line_color": (70, 40, 20),
        "red_color": (180, 40, 40),
        "black_color": (30, 30, 30),
    }
    current_theme = theme_light
    replay_mode = False
    replay_index = 0
    two_player = False

    while running:
        dt = clock.tick(FPS)
        human_turn = app_state == "game" and human_color is not None and state.side_to_move == human_color

        if app_state == "game":
            game_ui.set_human_input_enabled(human_turn)

        # Check if AI thread finished and ignore stale results.
        if app_state == "game" and not human_turn and ai_thinking and ai_thread is not None:
            if not ai_thread.is_alive():
                ai_thinking = False
                ai_thread = None
                if ai_move_result["request_id"] != ai_request_id:
                    pass
                elif ai_move_result["error"] is not None:
                    game_ui.status_message = f"AI move error: {ai_move_result['error']}"
                elif ai_move_result["move"] is None:
                    game_ui.status_message = f"{ai_agent.name}: no legal move"
                else:
                    try:
                        assert_legal_move(state, ai_move_result["move"])
                        state.apply_move(ai_move_result["move"])
                        game_ui.last_move = (ai_move_result["move"].src, ai_move_result["move"].dst)
                        game_ui.status_message = f"{ai_agent.name} moved: {ai_move_result['move'].src} -> {ai_move_result['move'].dst}"
                    except Exception as exc:
                        game_ui.status_message = f"AI move error: {exc}"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE and not fullscreen:
                width, height = event.w, event.h
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                game_ui.resize(width, height)
                menu.resize(width, height)

            if app_state == "menu":
                action = menu.handle_event(event)
                if action == "start":
                    state = GameState()
                    undo_stack.clear()
                    move_history_display.clear()
                    game_ui.set_mode_and_level(
                        menu.selected_mode,
                        menu.selected_level,
                        red_level=menu.selected_red_level,
                        black_level=menu.selected_black_level,
                    )
                    game_ui.set_state(state)
                    game_ui.set_game_over_message(None)
                    game_ui.move_undo_stack = undo_stack
                    game_ui.set_move_history(move_history_display)
                    human_color, red_agent, black_agent = _build_agents(
                        menu.selected_mode,
                        menu.selected_level,
                        red_level=menu.selected_red_level,
                        black_level=menu.selected_black_level,
                        ml_level=menu.selected_ml_level,
                    )
                    ai_elapsed_ms = 0
                    processed_plies = 0
                    position_counts = {_position_key(state): 1}
                    game_over_reason = None
                    app_state = "game"
                    two_player = menu.selected_mode == "Human vs Human"
                elif action == "quit":
                    running = False

            elif app_state == "game":
                action = game_ui.handle_event(event)
                if action == "back_to_menu":
                    app_state = "menu"
                    ai_request_id += 1
                    ai_thinking = False
                    ai_thread = None
                elif action == "toggle_fullscreen":
                    fullscreen = not fullscreen
                    if fullscreen:
                        info = pygame.display.Info()
                        width, height = info.current_w, info.current_h
                        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                    else:
                        width, height = WINDOW_WIDTH, WINDOW_HEIGHT
                        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                    game_ui.resize(width, height)
                elif action == "undo_move":
                    if undo_stack:
                        u = undo_stack.pop()
                        state.undo_move(u)
                        move_history_display[:] = _format_moves_for_ui(state)
                        game_ui.set_move_history(move_history_display)
                        game_ui.last_move = None
                        game_ui.set_game_over_message(None)
                        ai_elapsed_ms = 0
                        processed_plies = len(state.move_history)
                        position_counts = _rebuild_position_counts(state)
                        game_over_reason = None
                        ai_request_id += 1
                        ai_thinking = False
                        ai_thread = None
                elif action == "new_game":
                    state.reset()
                    undo_stack.clear()
                    move_history_display.clear()
                    game_ui.set_state(state)
                    game_ui.move_undo_stack = undo_stack
                    game_ui.set_move_history(move_history_display)
                    game_ui.set_game_over_message(None)
                    ai_elapsed_ms = 0
                    processed_plies = 0
                    position_counts = {_position_key(state): 1}
                    game_over_reason = None
                    ai_request_id += 1
                    ai_thinking = False
                    ai_thread = None
                elif action == "save_game" or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_s
                ):
                    saved_game = (state.clone(), list(undo_stack))
                elif action == "load_game" or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_l
                ):
                    if saved_game:
                        state = saved_game[0].clone()
                        undo_stack.clear()
                        undo_stack.extend(saved_game[1])
                        move_history_display[:] = _format_moves_for_ui(state)
                        game_ui.set_state(state)
                        game_ui.move_undo_stack = undo_stack
                        game_ui.set_move_history(move_history_display)
                elif action == "replay" or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_t
                ):
                    replay_mode = True
                    replay_index = 0
                elif action == "change_theme" or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_h
                ):
                    current_theme = (
                        theme_dark if current_theme == theme_light else theme_light
                    )
                    game_ui.set_theme(current_theme)
                if replay_mode:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                        if replay_index < len(move_history_display):
                            replay_index += 1
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                        if replay_index > 0:
                            replay_index -= 1
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        replay_mode = False

        if app_state == "menu":
            menu.draw(screen)
        elif app_state == "game":
            if len(state.move_history) != processed_plies:
                processed_plies = len(state.move_history)
                position_counts = _rebuild_position_counts(state)
                current_key = _position_key(state)
                if position_counts.get(current_key, 0) >= 3:
                    game_over_reason = "threefold_repetition"

            terminal = result_if_terminal(state)
            human_turn = human_color is not None and state.side_to_move == human_color
            game_ui.set_human_input_enabled(human_turn and terminal is None and game_over_reason is None)

            if game_over_reason == "threefold_repetition":
                game_ui.status_message = "Game over: draw (threefold repetition)"
                game_ui.set_game_over_message("DRAW - THREEFOLD REPETITION")
            elif terminal is not None:
                if terminal.winner is None:
                    game_ui.status_message = "Game over: draw (stalemate)"
                    game_ui.set_game_over_message("DRAW")
                else:
                    game_ui.status_message = f"Game over: {terminal.winner.value} wins ({terminal.reason})"
                    game_ui.set_game_over_message(f"{terminal.winner.value.upper()} WINS")
            elif not human_turn:
                game_ui.set_game_over_message(None)
                ai_elapsed_ms += dt
                if ai_thinking:
                    game_ui.status_message = "AI is thinking..."
                if ai_elapsed_ms >= ai_cooldown_ms and not ai_thinking and ai_thread is None and terminal is None and game_over_reason is None:
                    ai_elapsed_ms = 0
                    ai_agent = red_agent if state.side_to_move == Color.RED else black_agent
                    ai_request_id += 1
                    ai_move_result["move"] = None
                    ai_move_result["error"] = None
                    ai_move_result["request_id"] = 0
                    ai_state_snapshot = state.clone()
                    ai_thread = threading.Thread(
                        target=_start_ai_worker,
                        args=(ai_agent, ai_state_snapshot, ai_request_id, ai_move_result),
                        daemon=True,
                    )
                    ai_thread.start()
                    ai_thinking = True
            else:
                game_ui.set_game_over_message(None)
                ai_elapsed_ms = 0

            game_ui.set_move_history([str(m) for m in state.move_history])
            game_ui.update(dt)
            move_history_display[:] = _format_moves_for_ui(state)
            game_ui.set_move_history(move_history_display)
            game_ui.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
