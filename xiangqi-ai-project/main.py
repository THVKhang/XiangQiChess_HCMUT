import sys
import pygame

from ui.menu import Menu
from ui.game_ui import GameUI


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 760
FPS = 67
#SIX XSEVEN

class DemoState:
    """
    State giả để test UI bước 2 trước khi nhóm bạn cắm core/state.py thật.
    Khi có GameState thật, chỉ cần thay class này bằng import từ core.state.
    """

    def __init__(self):
        self.current_player = "red"
        self.board = [[None for _ in range(9)] for _ in range(10)]
        self._setup_initial_board()

    def _setup_initial_board(self):
        # Black side
        self.board[0][0] = "bR"
        self.board[0][1] = "bH"
        self.board[0][2] = "bE"
        self.board[0][3] = "bA"
        self.board[0][4] = "bK"
        self.board[0][5] = "bA"
        self.board[0][6] = "bE"
        self.board[0][7] = "bH"
        self.board[0][8] = "bR"
        self.board[2][1] = "bC"
        self.board[2][7] = "bC"
        self.board[3][0] = "bP"
        self.board[3][2] = "bP"
        self.board[3][4] = "bP"
        self.board[3][6] = "bP"
        self.board[3][8] = "bP"

        # Red side
        self.board[9][0] = "rR"
        self.board[9][1] = "rH"
        self.board[9][2] = "rE"
        self.board[9][3] = "rA"
        self.board[9][4] = "rK"
        self.board[9][5] = "rA"
        self.board[9][6] = "rE"
        self.board[9][7] = "rH"
        self.board[9][8] = "rR"
        self.board[7][1] = "rC"
        self.board[7][7] = "rC"
        self.board[6][0] = "rP"
        self.board[6][2] = "rP"
        self.board[6][4] = "rP"
        self.board[6][6] = "rP"
        self.board[6][8] = "rP"

    def reset(self):
        self.current_player = "red"
        self.board = [[None for _ in range(9)] for _ in range(10)]
        self._setup_initial_board()

    def move_piece(self, from_row, from_col, to_row, to_col):
        piece = self.board[from_row][from_col]
        if piece is None:
            return False

        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        self.current_player = "black" if self.current_player == "red" else "red"
        return True


def main():
    pygame.init()
    pygame.display.set_caption("XiangQi Chess - HCMUT")
    fullscreen = False
    width, height = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    menu = Menu(WINDOW_WIDTH, WINDOW_HEIGHT)
    game_ui = GameUI(WINDOW_WIDTH, WINDOW_HEIGHT)

    state = DemoState()
    app_state = "menu"
    running = True

    move_history = []  # Lưu lịch sử nước đi
    undo_stack = []
    redo_stack = []
    theme_dark = {
        'background_color': (40, 40, 40),
        'panel_color': (60, 60, 60),
        'line_color': (200, 200, 200),
        'red_color': (255, 80, 80),
        'black_color': (200, 200, 200),
    }
    theme_light = {
        'background_color': (242, 210, 140),
        'panel_color': (245, 240, 230),
        'line_color': (70, 40, 20),
        'red_color': (180, 40, 40),
        'black_color': (30, 30, 30),
    }
    current_theme = theme_light
    replay_mode = False
    replay_index = 0
    saved_game = None
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
                    state.reset()
                    move_history.clear()
                    undo_stack.clear()
                    redo_stack.clear()
                    game_ui.set_mode_and_level(menu.selected_mode, menu.selected_level)
                    game_ui.set_state(state)
                    game_ui.set_move_history(move_history)
                    app_state = "game"
                    two_player = (menu.selected_mode == "Human vs Human")
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
                    if move_history:
                        redo_stack.append(move_history.pop())
                        # TODO: gọi state.undo_move nếu có
                        game_ui.set_move_history(move_history)
                elif action == "new_game":
                    state.reset()
                    move_history.clear()
                    undo_stack.clear()
                    redo_stack.clear()
                    game_ui.set_state(state)
                    game_ui.set_move_history(move_history)
                elif action == "save_game" or (event.type == pygame.KEYDOWN and event.key == pygame.K_s):
                    saved_game = (state.current_player, [row[:] for row in state.board], move_history[:])
                elif action == "load_game" or (event.type == pygame.KEYDOWN and event.key == pygame.K_l):
                    if saved_game:
                        state.current_player, state.board, move_history = saved_game[0], [row[:] for row in saved_game[1]], saved_game[2][:]
                        game_ui.set_state(state)
                        game_ui.set_move_history(move_history)
                elif action == "replay" or (event.type == pygame.KEYDOWN and event.key == pygame.K_t):
                    replay_mode = True
                    replay_index = 0
                elif action == "change_theme" or (event.type == pygame.KEYDOWN and event.key == pygame.K_h):
                    current_theme = theme_dark if current_theme == theme_light else theme_light
                    game_ui.set_theme(current_theme)
                # Xử lý nước đi
                if event.type == pygame.MOUSEBUTTONDOWN and not replay_mode:
                    # TODO: kiểm tra hợp lệ, cập nhật move_history
                    pass
                # Chế độ replay
                if replay_mode:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                        if replay_index < len(move_history):
                            # TODO: cập nhật state theo move_history[replay_index]
                            replay_index += 1
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                        if replay_index > 0:
                            # TODO: cập nhật state về move_history[replay_index-1]
                            replay_index -= 1
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        replay_mode = False

        if app_state == "menu":
            menu.draw(screen)
        elif app_state == "game":
            game_ui.update(dt)
            game_ui.set_move_history(move_history)
            game_ui.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()