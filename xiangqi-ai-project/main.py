import sys
import pygame

from core.state import GameState
from ui.menu import Menu
from ui.game_ui import GameUI


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 760
FPS = 67


def _format_moves_for_ui(state: GameState) -> list[str]:
    return [f"{m.src} → {m.dst}" for m in state.move_history]


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
    undo_stack: list = []
    game_ui.move_undo_stack = undo_stack

    app_state = "menu"
    running = True

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
                    undo_stack.clear()
                    move_history_display.clear()
                    game_ui.set_mode_and_level(menu.selected_mode, menu.selected_level)
                    game_ui.set_state(state)
                    game_ui.move_undo_stack = undo_stack
                    game_ui.set_move_history(move_history_display)
                    app_state = "game"
                    two_player = menu.selected_mode == "Human vs Human"
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
                    if undo_stack:
                        u = undo_stack.pop()
                        state.undo_move(u)
                        move_history_display[:] = _format_moves_for_ui(state)
                        game_ui.set_move_history(move_history_display)
                        game_ui.last_move = None
                elif action == "new_game":
                    state.reset()
                    undo_stack.clear()
                    move_history_display.clear()
                    game_ui.set_state(state)
                    game_ui.move_undo_stack = undo_stack
                    game_ui.set_move_history(move_history_display)
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
            game_ui.update(dt)
            move_history_display[:] = _format_moves_for_ui(state)
            game_ui.set_move_history(move_history_display)
            game_ui.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
