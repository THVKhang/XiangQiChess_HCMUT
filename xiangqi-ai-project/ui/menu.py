import pygame


class Menu:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.selected_mode = "Human vs AI"
        self.selected_level = "Easy"
        self.selected_ml_level = "Hard"
        self.selected_red_level = "Easy"
        self.selected_black_level = "Easy"

        self.modes = [
            "Human vs AI",
            "Human vs ML",
            "AI vs AI",
            "AI vs Random",
            "ML vs Random",
            "ML vs Search",
        ]
        self.levels = ["Easy", "Medium", "Hard"]
        self.ml_levels = ["Easy", "Medium", "Hard"]

        self.title_font = pygame.font.SysFont("arial", 38, bold=True)
        self.heading_font = pygame.font.SysFont("arial", 24, bold=True)
        self.text_font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)

        self.mode_buttons: list[tuple[str, pygame.Rect]] = []
        self.level_buttons: list[tuple[str, pygame.Rect]] = []
        self.ml_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.red_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.black_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.start_button: pygame.Rect | None = None
        self.quit_button: pygame.Rect | None = None

        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        center_x = self.width // 2

        # Mode buttons — two columns of 3
        mode_y = 170
        col_left = center_x - 220
        col_right = center_x + 20
        modes_left = self.modes[:3]
        modes_right = self.modes[3:]
        self.mode_buttons = []
        for i, mode in enumerate(modes_left):
            rect = pygame.Rect(col_left, mode_y + i * 52, 200, 40)
            self.mode_buttons.append((mode, rect))
        for i, mode in enumerate(modes_right):
            rect = pygame.Rect(col_right, mode_y + i * 52, 200, 40)
            self.mode_buttons.append((mode, rect))

        # Level buttons (AI level, shown for single-agent modes)
        level_y = 440
        for i, level in enumerate(self.levels):
            rect = pygame.Rect(center_x - 120, level_y + i * 52, 240, 40)
            self.level_buttons.append((level, rect))

        # ML Level buttons
        ml_level_y = 440
        for i, level in enumerate(self.ml_levels):
            rect = pygame.Rect(center_x - 120, ml_level_y + i * 52, 240, 40)
            self.ml_level_buttons.append((level, rect))

        # AI vs AI separate level buttons
        ai_level_y = 440
        for i, level in enumerate(self.levels):
            red_rect = pygame.Rect(center_x - 210, ai_level_y + i * 52, 175, 40)
            black_rect = pygame.Rect(center_x + 35, ai_level_y + i * 52, 175, 40)
            self.red_level_buttons.append((level, red_rect))
            self.black_level_buttons.append((level, black_rect))

        self.start_button = pygame.Rect(center_x - 130, 635, 120, 46)
        self.quit_button = pygame.Rect(center_x + 10, 635, 120, 46)

    # ------------------------------------------------------------------
    # Helpers: which panel to show
    # ------------------------------------------------------------------

    def _mode_uses_ai_level(self) -> bool:
        return self.selected_mode in ("Human vs AI", "AI vs Random", "ML vs Search")

    def _mode_uses_ml_level(self) -> bool:
        return self.selected_mode in ("Human vs ML", "ML vs Random", "ML vs Search")

    def _mode_uses_ai_vs_ai(self) -> bool:
        return self.selected_mode == "AI vs AI"

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "start"
            elif event.key == pygame.K_ESCAPE:
                return "quit"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            for mode, rect in self.mode_buttons:
                if rect.collidepoint(mouse_pos):
                    self.selected_mode = mode

            if self._mode_uses_ai_vs_ai():
                for level, rect in self.red_level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_red_level = level
                for level, rect in self.black_level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_black_level = level
            elif self._mode_uses_ml_level() and self._mode_uses_ai_level():
                # ML vs Search: both selectors on screen
                for level, rect in self.ml_level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_ml_level = level
                for level, rect in self.level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_level = level
            elif self._mode_uses_ml_level():
                for level, rect in self.ml_level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_ml_level = level
            elif self._mode_uses_ai_level():
                for level, rect in self.level_buttons:
                    if rect.collidepoint(mouse_pos):
                        self.selected_level = level

            if self.start_button and self.start_button.collidepoint(mouse_pos):
                return "start"
            if self.quit_button and self.quit_button.collidepoint(mouse_pos):
                return "quit"

        return None

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_button(self, screen, rect, text, selected=False, color_override=None):
        if color_override:
            bg_color = color_override
        else:
            bg_color = (255, 220, 120) if selected else (230, 230, 230)
        border_color = (40, 40, 40)
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=8)
        surf = self.text_font.render(text, True, (20, 20, 20))
        screen.blit(surf, surf.get_rect(center=rect.center))

    def _draw_ml_vs_search_levels(self, screen):
        """Two side-by-side selectors: left=ML Level, right=AI Level."""
        center_x = self.width // 2
        ml_x = center_x - 215
        ai_x = center_x + 15
        y_start = 440

        ml_head = self.heading_font.render("ML Level", True, (20, 80, 160))
        ai_head = self.heading_font.render("AI Level", True, (30, 30, 30))
        screen.blit(ml_head, (ml_x, y_start - 28))
        screen.blit(ai_head, (ai_x, y_start - 28))

        for i, level in enumerate(self.ml_levels):
            r = pygame.Rect(ml_x, y_start + i * 52, 175, 40)
            self._draw_button(screen, r, level, selected=(level == self.selected_ml_level))
        for i, level in enumerate(self.levels):
            r = pygame.Rect(ai_x, y_start + i * 52, 175, 40)
            self._draw_button(screen, r, level, selected=(level == self.selected_level))

        # Override click rects for this layout
        self.ml_level_buttons = [
            (lv, pygame.Rect(ml_x, y_start + i * 52, 175, 40))
            for i, lv in enumerate(self.ml_levels)
        ]
        self.level_buttons = [
            (lv, pygame.Rect(ai_x, y_start + i * 52, 175, 40))
            for i, lv in enumerate(self.levels)
        ]

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw(self, screen):
        screen.fill((245, 239, 224))

        title = self.title_font.render("XiangQi Chess - HCMUT", True, (60, 30, 20))
        screen.blit(title, title.get_rect(center=(self.width // 2, 65)))

        subtitle = self.small_font.render(
            "Select game mode and level, then press Start",
            True, (80, 80, 80),
        )
        screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 100)))

        # Mode heading
        mode_head = self.heading_font.render("Choose Mode", True, (30, 30, 30))
        screen.blit(mode_head, (self.width // 2 - mode_head.get_width() // 2, 132))

        for mode, rect in self.mode_buttons:
            self._draw_button(screen, rect, mode, selected=(mode == self.selected_mode))

        # Level panels
        if self._mode_uses_ai_vs_ai():
            head = self.heading_font.render("AI vs AI Levels", True, (30, 30, 30))
            screen.blit(head, (self.width // 2 - head.get_width() // 2, 408))

            red_lbl = self.small_font.render("Red AI", True, (180, 30, 30))
            black_lbl = self.small_font.render("Black AI", True, (30, 30, 30))
            screen.blit(red_lbl, (self.width // 2 - 175, 430))
            screen.blit(black_lbl, (self.width // 2 + 80, 430))

            for level, rect in self.red_level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_red_level))
            for level, rect in self.black_level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_black_level))

        elif self._mode_uses_ml_level() and self._mode_uses_ai_level():
            self._draw_ml_vs_search_levels(screen)

        elif self._mode_uses_ml_level():
            head = self.heading_font.render("ML Agent Level", True, (20, 80, 160))
            screen.blit(head, (self.width // 2 - head.get_width() // 2, 408))
            for level, rect in self.ml_level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_ml_level))

        elif self._mode_uses_ai_level():
            head = self.heading_font.render("AI Level", True, (30, 30, 30))
            screen.blit(head, (self.width // 2 - head.get_width() // 2, 408))
            for level, rect in self.level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_level))

        # Start / Quit
        self._draw_button(screen, self.start_button, "Start", color_override=(120, 200, 100))
        self._draw_button(screen, self.quit_button, "Quit", color_override=(220, 100, 100))

        # Status line
        if self._mode_uses_ai_vs_ai():
            status = f"Mode: {self.selected_mode}  |  Red={self.selected_red_level}  Black={self.selected_black_level}"
        elif self._mode_uses_ml_level() and self._mode_uses_ai_level():
            status = f"Mode: {self.selected_mode}  |  ML={self.selected_ml_level}  AI={self.selected_level}"
        elif self._mode_uses_ml_level():
            status = f"Mode: {self.selected_mode}  |  ML Level={self.selected_ml_level}"
        elif self._mode_uses_ai_level():
            status = f"Mode: {self.selected_mode}  |  AI Level={self.selected_level}"
        else:
            status = f"Mode: {self.selected_mode}"

        status_surf = self.small_font.render(status, True, (80, 50, 30))
        screen.blit(status_surf, status_surf.get_rect(center=(self.width // 2, 700)))

        hint = self.small_font.render("Click a button or press Enter to Start, Esc to Quit", True, (100, 100, 100))
        screen.blit(hint, hint.get_rect(center=(self.width // 2, 720)))
