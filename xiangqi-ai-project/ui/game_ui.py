import os
import math
import pygame


class GameUI:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.background_color = (242, 210, 140)
        self.line_color = (70, 40, 20)
        self.red_color = (180, 40, 40)
        self.black_color = (30, 30, 30)
        self.highlight_color = (255, 215, 0)
        self.hover_color = (180, 180, 180)
        self.panel_color = (245, 240, 230)

        self.cols = 9
        self.rows = 10

        self.mode = "Human vs AI"
        self.level = "Easy"
        self.status_message = "Waiting for game state..."
        self.selected_cell = None
        self.hover_cell = None
        self.hovered_button = None
        self.pressed_button = None
        self.pressed_button_timer_ms = 0
        self.button_press_feedback_ms = 90
        self.legal_moves = []
        self.move_history = []
        self.last_move = None
        self.animating_piece = None
        self.move_anim_duration_ms = 140
        self.theme_transition_duration_ms = 220
        self.theme_transition_timer_ms = 0
        self.ui_time_ms = 0
        self.legal_moves_anim_ms = 0
        self.legal_moves_anim_duration_ms = 170

        self.state = None
        self.piece_images = {}
        self.piece_themes = ["classic", "flat", "wood"]
        self.piece_theme_index = 0
        self.piece_theme = self.piece_themes[self.piece_theme_index]
        self.cjk_font_candidates = [
            "Microsoft YaHei",
            "SimSun",
            "KaiTi",
            "Noto Sans CJK SC",
            "Arial Unicode MS",
            "segoeui",
        ]
        self.supports_cjk = False

        self.resize(width, height)

    def set_move_history(self, move_history):
        self.move_history = move_history

    def set_theme(self, theme):
        for k, v in theme.items():
            setattr(self, k, v)

    def cycle_piece_theme(self):
        self.piece_theme_index = (self.piece_theme_index + 1) % len(self.piece_themes)
        self.piece_theme = self.piece_themes[self.piece_theme_index]
        self.load_piece_images()
        self.theme_transition_timer_ms = self.theme_transition_duration_ms
        self.status_message = f"Theme quân: {self.piece_theme}"

    def set_mode_and_level(self, mode: str, level: str):
        self.mode = mode
        self.level = level

    def set_state(self, state):
        self.state = state
        self.selected_cell = None
        self.hover_cell = None
        self.legal_moves = []
        self.legal_moves_anim_ms = 0
        self.last_move = None
        self.animating_piece = None
        self.status_message = "State connected to UI"

    def reset_game(self):
        if self.state is not None and hasattr(self.state, "reset"):
            self.state.reset()
        self.selected_cell = None
        self.hover_cell = None
        self.legal_moves = []
        self.legal_moves_anim_ms = 0
        self.last_move = None
        self.animating_piece = None
        self.status_message = "Game reset"

    def update(self, dt: int):
        self.ui_time_ms += dt

        if self.pressed_button_timer_ms > 0:
            self.pressed_button_timer_ms = max(0, self.pressed_button_timer_ms - dt)
            if self.pressed_button_timer_ms == 0:
                self.pressed_button = None

        if self.theme_transition_timer_ms > 0:
            self.theme_transition_timer_ms = max(0, self.theme_transition_timer_ms - dt)

        if self.legal_moves:
            self.legal_moves_anim_ms = min(self.legal_moves_anim_duration_ms, self.legal_moves_anim_ms + dt)
        else:
            self.legal_moves_anim_ms = 0

        if self.animating_piece is None:
            return

        self.animating_piece["elapsed"] += dt
        if self.animating_piece["elapsed"] >= self.animating_piece["duration"]:
            self.animating_piece = None

    def resize(self, width, height):
        self.width = width
        self.height = height
        dashboard_scale = 0.90

        margin = max(14, int(min(width, height) * 0.018))
        gap = max(10, int(width * 0.012))

        # Compact dashboard: always smaller and anchored to the right.
        panel_w = int(width * 0.24 * dashboard_scale)
        panel_w = max(165, min(255, panel_w))
        self.side_panel_w = panel_w
        self.side_panel_y = margin
        self.side_panel_h = max(250, height - 2 * margin)

        # Board must fit in the remaining area and never overlap panel.
        # 8.8 and 9.8 include piece overhang around board edges.
        board_space_w = max(8 * 20, width - 2 * margin - gap - self.side_panel_w)
        board_space_h = max(9 * 20, height - 2 * margin)
        max_cell_w = int(board_space_w / 8.8)
        max_cell_h = int(board_space_h / 9.8)
        self.cell_size = max(18, min(max_cell_w, max_cell_h))

        self.board_width = (self.cols - 1) * self.cell_size
        self.board_height = (self.rows - 1) * self.cell_size

        piece_pad = max(6, int(self.cell_size * 0.34))
        self.board_top = margin + piece_pad

        # Keep board+panel centered horizontally when there is extra width.
        board_outer_w = self.board_width + piece_pad * 2
        content_w = board_outer_w + gap + self.side_panel_w
        centered_left = (width - content_w) // 2
        min_left = margin
        max_left = max(margin, width - margin - content_w)
        content_left = max(min_left, min(centered_left, max_left))

        self.board_left = content_left + piece_pad
        self.side_panel_x = content_left + board_outer_w + gap

        title_size = max(15, int(self.cell_size * 0.50 * dashboard_scale))
        text_size = max(12, int(self.cell_size * 0.31 * dashboard_scale))
        small_size = max(11, int(self.cell_size * 0.25 * dashboard_scale))
        piece_size = max(18, int(self.cell_size * 0.5))
        self.title_font = self._get_title_font(title_size, bold=True)
        self.text_font = self._get_font(text_size)
        self.small_font = self._get_font(small_size)
        self.piece_font = self._get_font(piece_size, bold=True, prefer_cjk=True)
        self.river_font = self._get_font(max(14, int(self.cell_size * 0.46)), bold=True, prefer_cjk=True)
        self.supports_cjk = self._supports_cjk(self.river_font)

        btn_w = max(96, int((self.side_panel_w - 2 * 14) * dashboard_scale))
        btn_h = max(20, min(34, int(self.cell_size * 0.62 * dashboard_scale)))
        bottom_pad = 16
        btn_spacing = 8
        total_btn_h = btn_h * 6 + btn_spacing * 5
        y0 = self.side_panel_y + self.side_panel_h - bottom_pad - total_btn_h

        min_text_top = self.side_panel_y + 120
        if y0 < min_text_top:
            available_h = self.side_panel_h - bottom_pad - min_text_top - btn_spacing * 5
            btn_h = max(18, available_h // 6)
            total_btn_h = btn_h * 6 + btn_spacing * 5
            y0 = self.side_panel_y + self.side_panel_h - bottom_pad - total_btn_h

        bx = self.side_panel_x + 16
        self.reset_button = pygame.Rect(bx, y0, btn_w, btn_h)
        self.undo_button = pygame.Rect(bx, y0 + btn_h + btn_spacing, btn_w, btn_h)
        self.newgame_button = pygame.Rect(bx, y0 + (btn_h + btn_spacing) * 2, btn_w, btn_h)
        self.back_button = pygame.Rect(bx, y0 + (btn_h + btn_spacing) * 3, btn_w, btn_h)
        self.fullscreen_button = pygame.Rect(bx, y0 + (btn_h + btn_spacing) * 4, btn_w, btn_h)
        self.theme_button = pygame.Rect(bx, y0 + (btn_h + btn_spacing) * 5, btn_w, btn_h)

        self.load_piece_images()

    def load_piece_images(self):
        self.piece_images = {}
        base_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(base_dir, "assets")
        theme_dir = os.path.join(assets_dir, self.piece_theme)
        piece_aliases = {
            "K": ["general", "king"],
            "A": ["advisor", "guard"],
            "E": ["elephant", "bishop"],
            "H": ["knight", "horse"],
            "R": ["rook", "chariot"],
            "C": ["cannon"],
            "P": ["pawn", "soldier"],
        }
        color_aliases = {
            "red": ["red", "r"],
            "black": ["black", "b"],
        }
        image_size = int(self.cell_size * 0.9)
        for code, names in piece_aliases.items():
            for color, c_aliases in color_aliases.items():
                loaded = None
                for name in names:
                    for c_name in c_aliases:
                        for root in [theme_dir, assets_dir]:
                            path = os.path.join(root, f"{name}_{c_name}.png")
                            if os.path.exists(path):
                                loaded = pygame.image.load(path).convert_alpha()
                                break
                        if loaded is not None:
                            break
                    if loaded is not None:
                        break
                if loaded is not None:
                    self.piece_images[(code, color)] = pygame.transform.smoothscale(
                        loaded,
                        (image_size, image_size),
                    )

    def _get_font(self, size: int, bold: bool = False, prefer_cjk: bool = False):
        if prefer_cjk:
            for name in self.cjk_font_candidates:
                try:
                    return pygame.font.SysFont(name, size, bold=bold)
                except Exception:
                    continue
        return pygame.font.SysFont("segoeui", size, bold=bold)

    def _get_title_font(self, size: int, bold: bool = False):
        for name in ["cambria", "constantia", "georgia", "timesnewroman"]:
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                continue
        return self._get_font(size, bold=bold)

    def _supports_cjk(self, font):
        # Heuristic: if multiple CJK chars produce distinct glyph bitmaps, CJK likely works.
        chars = ["楚", "漢", "帥", "將"]
        blobs = []
        for ch in chars:
            surf = font.render(ch, True, (20, 20, 20))
            blobs.append(pygame.image.tostring(surf, "RGBA"))
        return len(set(blobs)) > 1

    def board_to_screen(self, row: int, col: int):
        x = self.board_left + col * self.cell_size
        y = self.board_top + row * self.cell_size
        return x, y

    def screen_to_board(self, pos):
        mx, my = pos
        threshold = self.cell_size // 2
        for row in range(self.rows):
            for col in range(self.cols):
                x, y = self.board_to_screen(row, col)
                if abs(mx - x) <= threshold and abs(my - y) <= threshold:
                    return row, col
        return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_cell = self.screen_to_board(event.pos)
            self.hovered_button = None
            for btn in [
                self.reset_button,
                self.undo_button,
                self.newgame_button,
                self.back_button,
                self.fullscreen_button,
                self.theme_button,
            ]:
                if btn.collidepoint(event.pos):
                    self.hovered_button = btn
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.reset_button.collidepoint(mouse_pos):
                self.pressed_button = self.reset_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                self.reset_game()
                return None
            if self.undo_button.collidepoint(mouse_pos):
                self.pressed_button = self.undo_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                return "undo_move"
            if self.newgame_button.collidepoint(mouse_pos):
                self.pressed_button = self.newgame_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                return "new_game"
            if self.back_button.collidepoint(mouse_pos):
                self.pressed_button = self.back_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                return "back_to_menu"
            if self.fullscreen_button.collidepoint(mouse_pos):
                self.pressed_button = self.fullscreen_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                return "toggle_fullscreen"
            if self.theme_button.collidepoint(mouse_pos):
                self.pressed_button = self.theme_button
                self.pressed_button_timer_ms = self.button_press_feedback_ms
                self.cycle_piece_theme()
                return None

            clicked_cell = self.screen_to_board(mouse_pos)
            if clicked_cell is not None:
                self._handle_board_click(clicked_cell)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_ESCAPE:
                return "back_to_menu"
            elif event.key == pygame.K_F11:
                return "toggle_fullscreen"
            elif event.key == pygame.K_g:
                self.cycle_piece_theme()
        return None

    def _handle_board_click(self, cell):
        if self.state is None:
            self.status_message = "State is not connected"
            return

        row, col = cell
        piece = self._get_piece_at(row, col)

        if self.selected_cell is None:
            if piece is None:
                self.status_message = f"Empty cell: {cell}"
                return
            self.selected_cell = cell
            if self.state and hasattr(self.state, "get_legal_moves"):
                try:
                    self.legal_moves = self.state.get_legal_moves(cell)
                    self.legal_moves_anim_ms = 0
                except Exception:
                    self.legal_moves = []
                    self.legal_moves_anim_ms = 0
            else:
                self.legal_moves = []
                self.legal_moves_anim_ms = 0
            self.status_message = f"Selected piece at {cell}"
            return

        if cell == self.selected_cell:
            self.selected_cell = None
            self.legal_moves = []
            self.legal_moves_anim_ms = 0
            self.status_message = "Selection cleared"
            return

        from_row, from_col = self.selected_cell
        moved = self._apply_ui_move(from_row, from_col, row, col)
        self.legal_moves = []
        self.legal_moves_anim_ms = 0
        self.selected_cell = None
        self.status_message = "Move success" if moved else "Move failed"

    def _apply_ui_move(self, from_row, from_col, to_row, to_col):
        if self.state is None:
            return False

        moving_piece = self._get_piece_at(from_row, from_col)
        if moving_piece is not None:
            label, color_name, hanzi = self._extract_piece_info(moving_piece)
            self.animating_piece = {
                "label": label,
                "color": color_name,
                "hanzi": hanzi,
                "from": self.board_to_screen(from_row, from_col),
                "to": self.board_to_screen(to_row, to_col),
                "elapsed": 0,
                "duration": self.move_anim_duration_ms,
                "to_cell": (to_row, to_col),
            }
        else:
            self.animating_piece = None

        if hasattr(self.state, "move_piece"):
            moved = self.state.move_piece(from_row, from_col, to_row, to_col)
            if moved:
                self.last_move = ((from_row, from_col), (to_row, to_col))
            else:
                self.animating_piece = None
            return moved

        if hasattr(self.state, "apply_move"):
            move_obj = self._build_simple_move(from_row, from_col, to_row, to_col)
            try:
                result = self.state.apply_move(move_obj)
                if hasattr(self.state, "current_player"):
                    self.state.current_player = "black" if self.state.current_player == "red" else "red"
                moved = result if isinstance(result, bool) else True
                if moved:
                    self.last_move = ((from_row, from_col), (to_row, to_col))
                else:
                    self.animating_piece = None
                return moved
            except Exception:
                self.animating_piece = None
                return False

        if hasattr(self.state, "board"):
            piece = self.state.board[from_row][from_col]
            if piece is None:
                return False
            self.state.board[to_row][to_col] = piece
            self.state.board[from_row][from_col] = None
            if hasattr(self.state, "current_player"):
                self.state.current_player = "black" if self.state.current_player == "red" else "red"
            self.last_move = ((from_row, from_col), (to_row, to_col))
            return True

        return False

    def _build_simple_move(self, from_row, from_col, to_row, to_col):
        class SimpleMove:
            def __init__(self, fr, fc, tr, tc):
                self.from_row = fr
                self.from_col = fc
                self.to_row = tr
                self.to_col = tc

        return SimpleMove(from_row, from_col, to_row, to_col)

    def _get_piece_at(self, row, col):
        if self.state is None or not hasattr(self.state, "board"):
            return None
        return self.state.board[row][col]

    def _extract_piece_info(self, piece):
        if piece is None:
            return None, None, None

        hanzi_map = {
            "K": ("帥", "將"),
            "A": ("仕", "士"),
            "E": ("相", "象"),
            "H": ("傌", "馬"),
            "R": ("俥", "車"),
            "C": ("炮", "砲"),
            "P": ("兵", "卒"),
        }

        if isinstance(piece, str):
            if len(piece) >= 2:
                side = piece[0].lower()
                code = piece[1].upper()
                color_name = "red" if side == "r" else "black"
                hanzi = hanzi_map.get(code, (code, code))[0 if color_name == "red" else 1]
                return code, color_name, hanzi
            return piece, "black", piece

        color = None
        for attr in ["color", "side", "team", "owner"]:
            if hasattr(piece, attr):
                raw = str(getattr(piece, attr)).lower()
                if "red" in raw or raw == "r":
                    color = "red"
                elif "black" in raw or raw == "b":
                    color = "black"
                break

        piece_type = None
        for attr in ["piece_type", "type", "kind", "name", "symbol"]:
            if hasattr(piece, attr):
                piece_type = str(getattr(piece, attr))
                break

        label_map = {
            "rook": "R",
            "chariot": "R",
            "horse": "H",
            "knight": "H",
            "elephant": "E",
            "bishop": "E",
            "advisor": "A",
            "guard": "A",
            "general": "K",
            "king": "K",
            "cannon": "C",
            "pawn": "P",
            "soldier": "P",
            "r": "R",
            "h": "H",
            "e": "E",
            "a": "A",
            "k": "K",
            "c": "C",
            "p": "P",
        }

        label = "?"
        if piece_type is not None:
            normalized = piece_type.lower()
            label = label_map.get(normalized, normalized[:1].upper())

        if color is None:
            color = "black"

        hanzi = hanzi_map.get(label, (label, label))[0 if color == "red" else 1]
        return label, color, hanzi

    def render_text_lines(self, screen, text, font, color, x, y, max_width, max_bottom=None):
        words = text.split(" ")
        line = ""
        for word in words:
            test_line = line + word + " "
            if font.render(test_line, True, color).get_width() > max_width and line:
                surface = font.render(line, True, color)
                if max_bottom is not None and y + surface.get_height() > max_bottom:
                    return y, False
                screen.blit(surface, (x, y))
                y += surface.get_height() + 2
                line = word + " "
            else:
                line = test_line
        if line:
            surface = font.render(line, True, color)
            if max_bottom is not None and y + surface.get_height() > max_bottom:
                return y, False
            screen.blit(surface, (x, y))
            y += surface.get_height() + 2
        return y, True

    def _draw_legal_moves(self, screen):
        if self.legal_moves:
            base_radius = max(6, int(self.cell_size * 0.16))
            progress = 1.0
            if self.legal_moves_anim_duration_ms > 0:
                progress = min(1.0, self.legal_moves_anim_ms / self.legal_moves_anim_duration_ms)

            radius = max(4, int(base_radius * (0.62 + 0.38 * progress)))
            alpha = int(70 + 150 * progress)
            ring_alpha = int(110 + 120 * progress)

            marker_size = radius * 2 + 6
            marker = pygame.Surface((marker_size, marker_size), pygame.SRCALPHA)
            center = marker_size // 2
            pygame.draw.circle(marker, (18, 150, 52, alpha), (center, center), radius)
            pygame.draw.circle(marker, (12, 110, 38, ring_alpha), (center, center), radius, 1)

            for move in self.legal_moves:
                if isinstance(move, tuple) and len(move) == 2:
                    row, col = move
                elif hasattr(move, "to_row") and hasattr(move, "to_col"):
                    row, col = move.to_row, move.to_col
                else:
                    continue
                x, y = self.board_to_screen(row, col)
                screen.blit(marker, marker.get_rect(center=(x, y)))

    def _draw_board_background(self, screen):
        pad = max(8, int(self.cell_size * 0.45))
        board_rect = pygame.Rect(
            self.board_left - pad,
            self.board_top - pad,
            self.board_width + pad * 2,
            self.board_height + pad * 2,
        )

        # Slightly richer board base than global background.
        pygame.draw.rect(screen, (226, 194, 124), board_rect, border_radius=8)

        # River gets a distinct but close tone to create depth.
        river_top = self.board_top + 4 * self.cell_size + 2
        river_h = max(10, self.cell_size - 4)
        river_rect = pygame.Rect(self.board_left, river_top, self.board_width, river_h)
        pygame.draw.rect(screen, (210, 176, 106), river_rect)

        # Draw subtle horizontal grain lines using alpha overlay.
        grain = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
        step = max(5, int(self.cell_size * 0.12))
        for y in range(0, board_rect.height, step):
            alpha = 30 if (y // step) % 2 == 0 else 18
            pygame.draw.line(grain, (120, 86, 46, alpha), (0, y), (board_rect.width, y), 1)

        # Add faint vertical shading so the board has more depth at a glance.
        for x in range(0, board_rect.width, max(8, step * 2)):
            v_alpha = 10 if (x // max(8, step * 2)) % 2 == 0 else 6
            pygame.draw.line(grain, (104, 74, 40, v_alpha), (x, 0), (x, board_rect.height), 1)
        screen.blit(grain, board_rect.topleft)

        pygame.draw.rect(screen, (126, 92, 54), board_rect, width=3, border_radius=8)

    def _draw_board(self, screen):
        grid_color = (88, 58, 36)
        line_w = 1 if self.cell_size <= 72 else 2

        for row in range(self.rows):
            y = self.board_top + row * self.cell_size
            pygame.draw.line(screen, grid_color, (self.board_left, y), (self.board_left + self.board_width, y), line_w)

        for col in range(self.cols):
            x = self.board_left + col * self.cell_size
            pygame.draw.line(screen, grid_color, (x, self.board_top), (x, self.board_top + 4 * self.cell_size), line_w)
            pygame.draw.line(screen, grid_color, (x, self.board_top + 5 * self.cell_size), (x, self.board_top + 9 * self.cell_size), line_w)

        pygame.draw.line(
            screen,
            grid_color,
            (self.board_left, self.board_top),
            (self.board_left, self.board_top + self.board_height),
            line_w,
        )
        pygame.draw.line(
            screen,
            grid_color,
            (self.board_left + self.board_width, self.board_top),
            (self.board_left + self.board_width, self.board_top + self.board_height),
            line_w,
        )

    def _draw_palaces(self, screen):
        grid_color = (88, 58, 36)
        line_w = 1 if self.cell_size <= 72 else 2
        pygame.draw.line(screen, grid_color, self.board_to_screen(0, 3), self.board_to_screen(2, 5), line_w)
        pygame.draw.line(screen, grid_color, self.board_to_screen(0, 5), self.board_to_screen(2, 3), line_w)
        pygame.draw.line(screen, grid_color, self.board_to_screen(7, 3), self.board_to_screen(9, 5), line_w)
        pygame.draw.line(screen, grid_color, self.board_to_screen(7, 5), self.board_to_screen(9, 3), line_w)

    def _draw_river_text(self, screen):
        if self.supports_cjk:
            left_label = "楚 河"
            right_label = "漢 界"
        else:
            left_label = "CHU HE"
            right_label = "HAN JIE"
        t1 = self.river_font.render(left_label, True, (90, 50, 20))
        t2 = self.river_font.render(right_label, True, (90, 50, 20))
        river_y = int(self.board_top + 4.5 * self.cell_size - t1.get_height() // 2)
        screen.blit(t1, (int(self.board_left + 1.2 * self.cell_size), river_y))
        screen.blit(t2, (int(self.board_left + 5.2 * self.cell_size), river_y))

    def _draw_coordinates(self, screen):
        for row in range(self.rows):
            label = self.small_font.render(str(row), True, (50, 50, 50))
            _, y = self.board_to_screen(row, 0)
            screen.blit(label, (max(4, self.board_left - label.get_width() - 10), y - label.get_height() // 2))

        for col in range(self.cols):
            label = self.small_font.render(str(col), True, (50, 50, 50))
            x, _ = self.board_to_screen(0, col)
            screen.blit(label, (x - label.get_width() // 2, max(2, self.board_top - label.get_height() - 8)))

    def _draw_highlights(self, screen):
        if self.last_move is not None:
            from_cell, to_cell = self.last_move
            fx, fy = self.board_to_screen(*from_cell)
            tx, ty = self.board_to_screen(*to_cell)
            r1 = max(11, int(self.cell_size * 0.30))
            r2 = max(12, int(self.cell_size * 0.34))
            pygame.draw.circle(screen, (150, 105, 34), (fx, fy), r1, 2)
            pygame.draw.circle(screen, (184, 126, 28), (tx, ty), r2, 3)

        if self.hover_cell is not None:
            x, y = self.board_to_screen(*self.hover_cell)
            pygame.draw.circle(screen, self.hover_color, (x, y), max(5, int(self.cell_size * 0.15)))

        if self.selected_cell is not None:
            x, y = self.board_to_screen(*self.selected_cell)
            # Pulse helps players keep visual lock on the selected piece.
            pulse = 0.5 * (1.0 + math.sin(self.ui_time_ms * 0.012))
            base_r = max(16, int(self.cell_size * 0.42))
            pulse_r = base_r + int(self.cell_size * 0.10 * pulse)
            ring_w = 2 + int(pulse * 2)

            glow_r = pulse_r + max(4, int(self.cell_size * 0.10))
            glow_surface = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
            glow_alpha = int(35 + 45 * pulse)
            pygame.draw.circle(glow_surface, (255, 210, 90, glow_alpha), (glow_r + 1, glow_r + 1), glow_r)
            screen.blit(glow_surface, glow_surface.get_rect(center=(x, y)))

            pygame.draw.circle(screen, self.highlight_color, (x, y), pulse_r, ring_w)

    def _draw_pieces_from_state(self, screen):
        if self.state is None or not hasattr(self.state, "board"):
            return

        outer_r = max(10, int(self.cell_size * 0.36))
        inner_r = outer_r - 1
        fill_r = inner_r + 1
        shadow_offset = max(1, int(self.cell_size * 0.06))
        shadow_r = max(6, int(fill_r * 0.95))

        # One reusable alpha surface keeps shadow rendering cheap.
        shadow_surface = pygame.Surface((shadow_r * 2 + 2, shadow_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, (20, 12, 8, 55), (shadow_r + 1, shadow_r + 1), shadow_r)

        # Gloss highlight at the top of each piece for a subtle polished look.
        gloss_w = max(10, int(self.cell_size * 0.52))
        gloss_h = max(5, int(self.cell_size * 0.18))
        gloss_surface = pygame.Surface((gloss_w, gloss_h), pygame.SRCALPHA)
        pygame.draw.ellipse(gloss_surface, (255, 252, 242, 72), (0, 0, gloss_w, gloss_h))

        def draw_piece_at(px, py, label, color_name, hanzi):
            shadow_rect = shadow_surface.get_rect(center=(px + shadow_offset, py + shadow_offset))
            screen.blit(shadow_surface, shadow_rect)

            img = self.piece_images.get((label, color_name))
            if img:
                screen.blit(img, img.get_rect(center=(px, py)))
            else:
                color = self.red_color if color_name == "red" else self.black_color
                pygame.draw.circle(screen, (245, 230, 200), (px, py), fill_r)
                pygame.draw.circle(screen, color, (px, py), inner_r, 2)
                glyph = self.piece_font.render(hanzi, True, color)
                screen.blit(glyph, glyph.get_rect(center=(px, py)))

            gloss_rect = gloss_surface.get_rect(center=(px, py - max(2, int(self.cell_size * 0.16))))
            screen.blit(gloss_surface, gloss_rect)

        for row in range(self.rows):
            for col in range(self.cols):
                piece = self.state.board[row][col]
                if piece is None:
                    continue

                if self.animating_piece is not None and (row, col) == self.animating_piece["to_cell"]:
                    continue

                label, color_name, hanzi = self._extract_piece_info(piece)
                x, y = self.board_to_screen(row, col)
                draw_piece_at(x, y, label, color_name, hanzi)

        if self.animating_piece is not None:
            anim = self.animating_piece
            t = min(1.0, anim["elapsed"] / anim["duration"])
            sx, sy = anim["from"]
            ex, ey = anim["to"]
            ax = int(sx + (ex - sx) * t)
            ay = int(sy + (ey - sy) * t)
            draw_piece_at(ax, ay, anim["label"], anim["color"], anim["hanzi"])

    def _get_theme_palette(self):
        palettes = {
            "classic": {
                "panel_bg": (239, 225, 198),
                "panel_border": (112, 90, 62),
                "title": (45, 35, 30),
                "info_text": (71, 55, 40),
                "status_text": (124, 61, 24),
                "button_bg": (230, 205, 164),
                "button_hover": (240, 216, 177),
                "button_pressed": (214, 187, 145),
                "button_border": (98, 72, 48),
                "button_text": (42, 36, 32),
                "transition_tint": (247, 225, 178),
            },
            "flat": {
                "panel_bg": (238, 236, 231),
                "panel_border": (86, 86, 86),
                "title": (36, 36, 36),
                "info_text": (68, 68, 68),
                "status_text": (96, 56, 30),
                "button_bg": (226, 226, 226),
                "button_hover": (239, 239, 239),
                "button_pressed": (205, 205, 205),
                "button_border": (86, 86, 86),
                "button_text": (44, 44, 44),
                "transition_tint": (232, 232, 232),
            },
            "wood": {
                "panel_bg": (241, 224, 194),
                "panel_border": (120, 90, 56),
                "title": (64, 42, 24),
                "info_text": (84, 58, 36),
                "status_text": (125, 65, 35),
                "button_bg": (231, 206, 164),
                "button_hover": (240, 216, 176),
                "button_pressed": (214, 187, 145),
                "button_border": (112, 84, 52),
                "button_text": (72, 48, 30),
                "transition_tint": (234, 198, 140),
            },
        }
        return palettes.get(self.piece_theme, palettes["classic"])

    def _draw_theme_transition(self, screen):
        if self.theme_transition_timer_ms <= 0:
            return

        palette = self._get_theme_palette()
        progress = self.theme_transition_timer_ms / self.theme_transition_duration_ms
        alpha = int(95 * progress)
        tint = palette["transition_tint"]

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((tint[0], tint[1], tint[2], alpha))
        screen.blit(overlay, (0, 0))

    def _draw_button(self, screen, rect, text, palette, is_hovered=False, is_pressed=False):
        if is_pressed:
            bg = palette["button_pressed"]
        else:
            bg = palette["button_hover"] if is_hovered else palette["button_bg"]

        draw_rect = rect.move(0, 1) if is_pressed else rect

        # Soft shadow gives buttons clearer depth.
        shadow_offset = 1 if is_pressed else 2
        shadow_rect = draw_rect.move(0, shadow_offset)
        pygame.draw.rect(screen, (35, 25, 18, 70), shadow_rect, border_radius=8)

        pygame.draw.rect(screen, bg, draw_rect, border_radius=8)
        pygame.draw.rect(screen, palette["button_border"], draw_rect, width=2, border_radius=8)

        # Top highlight simulates a pressed metal/wooden keycap look.
        if not is_pressed:
            hi_h = max(3, rect.height // 3)
            highlight = pygame.Surface((rect.width - 6, hi_h), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255, 250, 238, 58), (0, 0, rect.width - 6, hi_h), border_radius=6)
            screen.blit(highlight, (draw_rect.x + 3, draw_rect.y + 2))

        text_surface = self.text_font.render(text, True, palette["button_text"])
        screen.blit(text_surface, text_surface.get_rect(center=draw_rect.center))

    def draw_move_history(self, screen, x, y, max_width, max_bottom):
        if not self.move_history:
            return y
        y, ok = self.render_text_lines(screen, "Lịch sử:", self.small_font, (40, 40, 40), x, y, max_width, max_bottom)
        if not ok:
            return y
        for i, move in enumerate(self.move_history[-8:]):
            y, ok = self.render_text_lines(screen, f"{i + 1}. {move}", self.small_font, (40, 40, 40), x, y, max_width, max_bottom)
            if not ok:
                break
        return y

    def _draw_side_panel(self, screen):
        palette = self._get_theme_palette()
        panel_rect = pygame.Rect(self.side_panel_x, self.side_panel_y, self.side_panel_w, self.side_panel_h)

        panel_shadow = pygame.Surface((panel_rect.width + 8, panel_rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(panel_shadow, (20, 12, 8, 55), (0, 0, panel_rect.width + 8, panel_rect.height + 8), border_radius=14)
        screen.blit(panel_shadow, (panel_rect.x + 2, panel_rect.y + 4))

        pygame.draw.rect(screen, palette["panel_bg"], panel_rect, border_radius=12)
        pygame.draw.rect(screen, palette["panel_border"], panel_rect, width=3, border_radius=12)

        pad_x = 16
        x = self.side_panel_x + pad_x
        max_text_w = self.side_panel_w - 2 * pad_x

        title = self.title_font.render("CỜ TƯỚNG", True, palette["title"])
        title_x = self.side_panel_x + (self.side_panel_w - title.get_width()) // 2
        y = self.side_panel_y + 14
        screen.blit(title, (title_x, y))
        y += title.get_height() + 14

        current_turn = "Unknown"
        if self.state is not None and hasattr(self.state, "current_player"):
            current_turn = str(self.state.current_player)

        info_lines = [
            f"Chế độ: {self.mode}",
            f"Cấp độ: {self.level}",
            f"Lượt: {current_turn}",
            f"Chọn: {self.selected_cell}",
            f"Theme quân: {self.piece_theme}",
            "",
            "Điều khiển:",
            "- Click: chọn/quân",
            "- R: reset",
            "- U: undo",
            "- N: ván mới",
            "- F11: phóng to",
            "- ESC: menu",
            "- G: đổi theme quân",
        ]

        # Keep text above buttons with a safe gap
        text_bottom_limit = self.reset_button.top - 14
        for line in info_lines:
            y, ok = self.render_text_lines(screen, line, self.text_font, palette["info_text"], x, y, max_text_w, text_bottom_limit)
            if not ok:
                break

        y += 6
        y, ok = self.render_text_lines(screen, "Trạng thái:", self.text_font, palette["info_text"], x, y, max_text_w, text_bottom_limit)
        if ok:
            self.render_text_lines(screen, self.status_message, self.small_font, palette["status_text"], x, y, max_text_w, text_bottom_limit)

        # Optional move history if there is space
        hist_top = min(self.undo_button.top - 8, text_bottom_limit)
        if hist_top > y + 20:
            self.draw_move_history(screen, x, y + 6, max_text_w, hist_top)

        self._draw_button(
            screen,
            self.reset_button,
            "Reset",
            palette,
            self.hovered_button == self.reset_button,
            self.pressed_button == self.reset_button,
        )
        self._draw_button(
            screen,
            self.undo_button,
            "Undo",
            palette,
            self.hovered_button == self.undo_button,
            self.pressed_button == self.undo_button,
        )
        self._draw_button(
            screen,
            self.newgame_button,
            "Ván mới",
            palette,
            self.hovered_button == self.newgame_button,
            self.pressed_button == self.newgame_button,
        )
        self._draw_button(
            screen,
            self.back_button,
            "Menu",
            palette,
            self.hovered_button == self.back_button,
            self.pressed_button == self.back_button,
        )
        self._draw_button(
            screen,
            self.fullscreen_button,
            "Phóng to",
            palette,
            self.hovered_button == self.fullscreen_button,
            self.pressed_button == self.fullscreen_button,
        )
        self._draw_button(
            screen,
            self.theme_button,
            "Theme quân",
            palette,
            self.hovered_button == self.theme_button,
            self.pressed_button == self.theme_button,
        )

    def draw(self, screen):
        screen.fill(self.background_color)
        self._draw_board_background(screen)
        self._draw_board(screen)
        self._draw_palaces(screen)
        self._draw_river_text(screen)
        self._draw_coordinates(screen)
        self._draw_highlights(screen)
        self._draw_legal_moves(screen)
        self._draw_pieces_from_state(screen)
        self._draw_side_panel(screen)
        self._draw_theme_transition(screen)

