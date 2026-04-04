import sys
import pygame

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


def _build_agents(mode: str, level: str, red_level: str = None, black_level: str = None):
    if mode == "Human vs AI":
        return Color.RED, None, _build_search_agent(level, Color.BLACK, algorithm="alphabeta")
    if mode == "AI vs Random":
        return None, _build_search_agent(level, Color.RED, algorithm="alphabeta"), RandomAgent(player_id=Color.BLACK)
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


def main():
    pygame.init()
    pygame.display.set_caption("XiangQi Chess - HCMUT")
    fullscreen = False
    width, height = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    menu = Menu(WINDOW_WIDTH, WINDOW_HEIGHT)
    game_ui = GameUI(WINDOW_WIDTH, WINDOW_HEIGHT)

    state = GameState()
    human_color = Color.RED
    red_agent = None
    black_agent = None

    app_state = "menu"
    running = True
    game_over_reason = None

    ai_cooldown_ms = 260
    ai_elapsed_ms = 0
    processed_plies = 0
    position_counts = {_position_key(state): 1}

    while running:
        dt = clock.tick(FPS)
        human_turn = app_state == "game" and human_color is not None and state.side_to_move == human_color

        if app_state == "game":
            game_ui.set_human_input_enabled(human_turn)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE and not fullscreen:
                width, height = event.w, event.h
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                game_ui.resize(width, height)

            if app_state == "menu":
                action = menu.handle_event(event)
                if action == "start":
                    state = GameState()
                    game_ui.set_mode_and_level(
                        menu.selected_mode,
                        menu.selected_level,
                        red_level=menu.selected_red_level,
                        black_level=menu.selected_black_level,
                    )
                    game_ui.set_state(state)
                    game_ui.set_game_over_message(None)
                    game_ui.set_move_history([])
                    human_color, red_agent, black_agent = _build_agents(
                        menu.selected_mode,
                        menu.selected_level,
                        red_level=menu.selected_red_level,
                        black_level=menu.selected_black_level,
                    )
                    ai_elapsed_ms = 0
                    processed_plies = 0
                    position_counts = {_position_key(state): 1}
                    game_over_reason = None
                    app_state = "game"
                elif action == "quit":
                    running = False

            elif app_state == "game":
                action = game_ui.handle_event(event)
                if action == "back_to_menu":
                    app_state = "menu"
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
                    state = _rebuild_state_without_last_move(state)
                    game_ui.set_state(state)
                    game_ui.set_game_over_message(None)
                    ai_elapsed_ms = 0
                    processed_plies = len(state.move_history)
                    position_counts = _rebuild_position_counts(state)
                    game_over_reason = None
                elif action == "new_game":
                    state = GameState()
                    game_ui.set_state(state)
                    game_ui.set_game_over_message(None)
                    ai_elapsed_ms = 0
                    processed_plies = 0
                    position_counts = {_position_key(state): 1}
                    game_over_reason = None

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
                if ai_elapsed_ms >= ai_cooldown_ms:
                    ai_elapsed_ms = 0
                    agent = red_agent if state.side_to_move == Color.RED else black_agent
                    if agent is not None:
                        ai_move = agent.select_move(state.clone())
                        if ai_move is None:
                            game_ui.status_message = f"{agent.name}: no legal move"
                        else:
                            try:
                                assert_legal_move(state, ai_move)
                                state.apply_move(ai_move)
                                game_ui.last_move = (ai_move.src, ai_move.dst)
                                game_ui.status_message = f"{agent.name} moved: {ai_move.src} -> {ai_move.dst}"
                            except Exception as exc:
                                game_ui.status_message = f"AI move error: {exc}"
            else:
                game_ui.set_game_over_message(None)
                ai_elapsed_ms = 0

            game_ui.set_move_history([str(m) for m in state.move_history])
            game_ui.update(dt)
            game_ui.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()