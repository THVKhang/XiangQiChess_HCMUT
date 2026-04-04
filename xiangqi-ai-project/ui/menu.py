import pygame


class Menu:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.selected_mode = "Human vs AI"
        self.selected_level = "Easy"
        self.selected_red_level = "Easy"
        self.selected_black_level = "Easy"

        self.modes = ["Human vs AI", "AI vs AI", "AI vs Random"]
        self.levels = ["Easy", "Medium", "Hard"]

        self.title_font = pygame.font.SysFont("arial", 40, bold=True)
        self.heading_font = pygame.font.SysFont("arial", 28, bold=True)
        self.text_font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 18)

        self.mode_buttons = []
        self.level_buttons = []
        self.red_level_buttons = []
        self.black_level_buttons = []
        self.start_button = None
        self.quit_button = None

        self._build_layout()

    def _build_layout(self):
        center_x = self.width // 2

        # Mode buttons
        mode_y = 180
        for i, mode in enumerate(self.modes):
            rect = pygame.Rect(center_x - 150, mode_y + i * 60, 300, 44)
            self.mode_buttons.append((mode, rect))

        # Level buttons
        level_y = 420
        for i, level in enumerate(self.levels):
            rect = pygame.Rect(center_x - 150, level_y + i * 60, 300, 44)
            self.level_buttons.append((level, rect))

        # AI vs AI separate level buttons
        ai_level_y = 420
        for i, level in enumerate(self.levels):
            red_rect = pygame.Rect(center_x - 170, ai_level_y + i * 60, 150, 44)
            black_rect = pygame.Rect(center_x + 20, ai_level_y + i * 60, 150, 44)
            self.red_level_buttons.append((level, red_rect))
            self.black_level_buttons.append((level, black_rect))

        self.start_button = pygame.Rect(center_x - 150, 620, 140, 50)
        self.quit_button = pygame.Rect(center_x + 10, 620, 140, 50)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.selected_mode = self.modes[0]
            elif event.key == pygame.K_2:
                self.selected_mode = self.modes[1]
            elif event.key == pygame.K_3:
                self.selected_mode = self.modes[2]

            elif event.key == pygame.K_e:
                self.selected_level = "Easy"
            elif event.key == pygame.K_m:
                self.selected_level = "Medium"
            elif event.key == pygame.K_h:
                self.selected_level = "Hard"

            elif event.key == pygame.K_q:
                self.selected_red_level = "Easy"
            elif event.key == pygame.K_w:
                self.selected_red_level = "Medium"
            elif event.key == pygame.K_e:
                self.selected_red_level = "Hard"

            elif event.key == pygame.K_a:
                self.selected_black_level = "Easy"
            elif event.key == pygame.K_s:
                self.selected_black_level = "Medium"
            elif event.key == pygame.K_d:
                self.selected_black_level = "Hard"

            elif event.key == pygame.K_RETURN:
                return "start"
            elif event.key == pygame.K_ESCAPE:
                return "quit"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            for mode, rect in self.mode_buttons:
                if rect.collidepoint(mouse_pos):
                    self.selected_mode = mode

            for level, rect in self.level_buttons:
                if rect.collidepoint(mouse_pos):
                    self.selected_level = level

            for level, rect in self.red_level_buttons:
                if rect.collidepoint(mouse_pos):
                    self.selected_red_level = level

            for level, rect in self.black_level_buttons:
                if rect.collidepoint(mouse_pos):
                    self.selected_black_level = level

            if self.start_button.collidepoint(mouse_pos):
                return "start"
            if self.quit_button.collidepoint(mouse_pos):
                return "quit"

        return None

    def _draw_button(self, screen, rect, text, selected=False):
        bg_color = (230, 230, 230) if not selected else (255, 220, 120)
        border_color = (40, 40, 40)

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=8)

        text_surface = self.text_font.render(text, True, (20, 20, 20))
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def draw(self, screen):
        screen.fill((245, 239, 224))

        title = self.title_font.render("XiangQi Chess - HCMUT", True, (60, 30, 20))
        title_rect = title.get_rect(center=(self.width // 2, 70))
        screen.blit(title, title_rect)

        subtitle = self.small_font.render(
            "Level 1 UI Scaffold - Select mode and level to start",
            True,
            (70, 70, 70),
        )
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 110))
        screen.blit(subtitle, subtitle_rect)

        mode_heading = self.heading_font.render("Choose Mode", True, (30, 30, 30))
        screen.blit(mode_heading, (self.width // 2 - 90, 140))

        for mode, rect in self.mode_buttons:
            self._draw_button(screen, rect, mode, selected=(mode == self.selected_mode))

        if self.selected_mode == "AI vs AI":
            level_heading = self.heading_font.render("AI vs AI Levels", True, (30, 30, 30))
            screen.blit(level_heading, (self.width // 2 - 105, 380))

            red_label = self.small_font.render("Red AI", True, (80, 50, 30))
            black_label = self.small_font.render("Black AI", True, (80, 50, 30))
            screen.blit(red_label, (self.width // 2 - 125, 405))
            screen.blit(black_label, (self.width // 2 + 65, 405))

            for level, rect in self.red_level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_red_level))

            for level, rect in self.black_level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_black_level))
        else:
            level_heading = self.heading_font.render("Choose Level", True, (30, 30, 30))
            screen.blit(level_heading, (self.width // 2 - 90, 380))

            for level, rect in self.level_buttons:
                self._draw_button(screen, rect, level, selected=(level == self.selected_level))

        self._draw_button(screen, self.start_button, "Start", selected=False)
        self._draw_button(screen, self.quit_button, "Quit", selected=False)

        help_text_1 = self.small_font.render(
            "Keyboard: 1/2/3 mode, E/M/H level, Q/W/E Red, A/S/D Black, Enter Start",
            True,
            (80, 80, 80),
        )

        if self.selected_mode == "AI vs AI":
            current_text = (
                f"Current: {self.selected_mode} | Red={self.selected_red_level} | "
                f"Black={self.selected_black_level}"
            )
        else:
            current_text = f"Current: {self.selected_mode} | {self.selected_level}"

        help_text_2 = self.small_font.render(current_text, True, (80, 50, 30))
        help_text_3 = self.small_font.render(
            "AI strength order: Easy < Medium < Hard",
            True,
            (80, 50, 30),
        )

        screen.blit(help_text_1, (self.width // 2 - help_text_1.get_width() // 2, 690))
        screen.blit(help_text_2, (self.width // 2 - help_text_2.get_width() // 2, 715))
        screen.blit(help_text_3, (self.width // 2 - help_text_3.get_width() // 2, 740))