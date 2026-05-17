import pygame


class Menu:
    """Main menu – dark premium theme with gold accents, fully responsive."""

    # ── Dark Premium Palette ─────────────────────────────────────────
    BG_TOP      = (28, 32, 40)       # deep dark blue-grey
    BG_BOT      = (18, 20, 28)       # even darker at bottom

    CARD_BG     = (38, 42, 52)       # slightly lighter card
    CARD_BORDER = (58, 62, 72)
    CARD_SHADOW = (0, 0, 0, 90)

    TITLE_CLR   = (232, 196, 112)    # warm gold
    SUB_CLR     = (160, 155, 145)    # muted grey
    HEADING_CLR = (200, 175, 120)    # soft gold
    INFO_CLR    = (150, 145, 138)
    DIVIDER     = (60, 64, 74)

    BTN_NORMAL      = (50, 54, 66)
    BTN_HOVER       = (62, 66, 80)
    BTN_SELECTED    = (180, 145, 60)   # rich gold
    BTN_SEL_TEXT    = (28, 24, 16)     # dark text on gold
    BTN_BORDER      = (68, 72, 84)
    BTN_SEL_BORDER  = (200, 165, 70)
    BTN_TEXT        = (210, 205, 195)

    START_BG        = (50, 130, 80)
    START_HOVER     = (60, 150, 95)
    QUIT_BG         = (150, 55, 55)
    QUIT_HOVER      = (175, 70, 70)
    ACTION_TEXT     = (255, 255, 255)

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.selected_mode = "Human vs AI"
        self.selected_level = "Easy"
        self.selected_ml_level = "Hard"
        self.selected_red_level = "Easy"
        self.selected_black_level = "Easy"

        self.modes = [
            "Human vs AI",  "Human vs ML",
            "AI vs AI",     "AI vs Random",
            "ML vs Random", "ML vs Search",
        ]
        self.levels = ["Easy", "Medium", "Hard"]

        self._init_fonts()

        self.mode_buttons: list[tuple[str, pygame.Rect]] = []
        self.level_buttons: list[tuple[str, pygame.Rect]] = []
        self.ml_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.red_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.black_level_buttons: list[tuple[str, pygame.Rect]] = []
        self.start_button = pygame.Rect(0, 0, 1, 1)
        self.quit_button  = pygame.Rect(0, 0, 1, 1)

        self.hovered_rect: pygame.Rect | None = None
        self._card_rect = pygame.Rect(0, 0, 1, 1)
        self._divider_y = 0

        self._build_layout()

    def _init_fonts(self):
        for family in ("Segoe UI", "Arial", "Helvetica", "georgia"):
            try:
                self.title_font   = pygame.font.SysFont(family, 40, bold=True)
                self.heading_font = pygame.font.SysFont(family, 20, bold=True)
                self.text_font    = pygame.font.SysFont(family, 16, bold=True)
                self.small_font   = pygame.font.SysFont(family, 13)
                return
            except Exception:
                continue
        self.title_font   = pygame.font.SysFont(None, 40, bold=True)
        self.heading_font = pygame.font.SysFont(None, 20, bold=True)
        self.text_font    = pygame.font.SysFont(None, 16, bold=True)
        self.small_font   = pygame.font.SysFont(None, 13)

    # ── layout ───────────────────────────────────────────────────────
    def resize(self, w: int, h: int):
        self.width = w
        self.height = h
        self._build_layout()

    def _build_layout(self):
        cx = self.width  // 2
        cy = self.height // 2

        card_w = min(620, self.width  - 80)
        card_h = min(580, self.height - 80)
        self._card_rect = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)
        cr = self._card_rect

        pad = 30
        inner_w = card_w - pad * 2
        btn_w  = (inner_w - 14) // 2
        btn_h  = 36
        row_gap = 8
        col_gap = 14

        # Mode buttons
        mode_top = cr.y + 95
        self.mode_buttons.clear()
        for i, mode in enumerate(self.modes):
            col = i % 2
            row = i // 2
            bx = cr.x + pad + col * (btn_w + col_gap)
            by = mode_top + row * (btn_h + row_gap)
            self.mode_buttons.append((mode, pygame.Rect(bx, by, btn_w, btn_h)))

        self._divider_y = mode_top + 3 * (btn_h + row_gap) + 6

        # Level buttons
        level_top = self._divider_y + 32
        level_btn_w = min(200, inner_w // 2)

        self.level_buttons.clear()
        for i, lv in enumerate(self.levels):
            bx = cx - level_btn_w // 2
            by = level_top + i * (btn_h + row_gap)
            self.level_buttons.append((lv, pygame.Rect(bx, by, level_btn_w, btn_h)))

        # ML level buttons (same layout as regular level buttons)
        self.ml_level_buttons.clear()
        for i, lv in enumerate(self.levels):
            bx = cx - level_btn_w // 2
            by = level_top + i * (btn_h + row_gap)
            self.ml_level_buttons.append((lv, pygame.Rect(bx, by, level_btn_w, btn_h)))

        self.red_level_buttons.clear()
        self.black_level_buttons.clear()
        split_w = (inner_w - col_gap) // 2
        for i, lv in enumerate(self.levels):
            rx = cr.x + pad
            bx2 = rx + split_w + col_gap
            by = level_top + i * (btn_h + row_gap)
            self.red_level_buttons.append((lv, pygame.Rect(rx, by, split_w, btn_h)))
            self.black_level_buttons.append((lv, pygame.Rect(bx2, by, split_w, btn_h)))

        # Action buttons
        action_y = cr.y + card_h - pad - 42
        action_w = min(130, (inner_w - col_gap) // 2)
        self.start_button = pygame.Rect(cx - action_w - col_gap // 2, action_y, action_w, 42)
        self.quit_button  = pygame.Rect(cx + col_gap // 2,           action_y, action_w, 42)

    # ── events ───────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.resize(event.w, event.h)

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.hovered_rect = None
            for _, r in (self.mode_buttons + self.level_buttons + self.ml_level_buttons
                         + self.red_level_buttons + self.black_level_buttons):
                if r.collidepoint(pos):
                    self.hovered_rect = r
                    break
            if self.start_button.collidepoint(pos):
                self.hovered_rect = self.start_button
            elif self.quit_button.collidepoint(pos):
                self.hovered_rect = self.quit_button

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "start"
            if event.key == pygame.K_ESCAPE:
                return "quit"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for mode, r in self.mode_buttons:
                if r.collidepoint(pos):
                    self.selected_mode = mode
            for lv, r in self.level_buttons:
                if r.collidepoint(pos):
                    self.selected_level = lv
            for lv, r in self.ml_level_buttons:
                if r.collidepoint(pos):
                    self.selected_ml_level = lv
            for lv, r in self.red_level_buttons:
                if r.collidepoint(pos):
                    self.selected_red_level = lv
            for lv, r in self.black_level_buttons:
                if r.collidepoint(pos):
                    self.selected_black_level = lv
            if self.start_button.collidepoint(pos):
                return "start"
            if self.quit_button.collidepoint(pos):
                return "quit"

        return None

    # ── drawing ──────────────────────────────────────────────────────
    def _draw_btn(self, screen, rect, text, selected=False, kind="normal"):
        hovered = rect is self.hovered_rect

        if kind == "start":
            bg = self.START_HOVER if hovered else self.START_BG
            fg, border = self.ACTION_TEXT, bg
        elif kind == "quit":
            bg = self.QUIT_HOVER if hovered else self.QUIT_BG
            fg, border = self.ACTION_TEXT, bg
        elif selected:
            bg, fg, border = self.BTN_SELECTED, self.BTN_SEL_TEXT, self.BTN_SEL_BORDER
        elif hovered:
            bg, fg, border = self.BTN_HOVER, self.BTN_TEXT, self.BTN_BORDER
        else:
            bg, fg, border = self.BTN_NORMAL, self.BTN_TEXT, self.BTN_BORDER

        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, width=1, border_radius=6)

        surf = self.text_font.render(text, True, fg)
        screen.blit(surf, surf.get_rect(center=rect.center))

    def draw(self, screen):
        # Gradient background
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r = int(self.BG_TOP[0] + (self.BG_BOT[0] - self.BG_TOP[0]) * t)
            g = int(self.BG_TOP[1] + (self.BG_BOT[1] - self.BG_TOP[1]) * t)
            b = int(self.BG_TOP[2] + (self.BG_BOT[2] - self.BG_TOP[2]) * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (self.width, y))

        cr = self._card_rect
        cx = self.width // 2

        # Card shadow
        sr = cr.inflate(8, 8).move(0, 4)
        shadow = pygame.Surface((sr.w, sr.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, self.CARD_SHADOW, (0, 0, sr.w, sr.h), border_radius=18)
        screen.blit(shadow, sr.topleft)

        # Card
        pygame.draw.rect(screen, self.CARD_BG, cr, border_radius=14)
        pygame.draw.rect(screen, self.CARD_BORDER, cr, width=1, border_radius=14)

        # Title
        title = self.title_font.render("XiangQi Chess", True, self.TITLE_CLR)
        screen.blit(title, title.get_rect(center=(cx, cr.y + 30)))

        sub = self.small_font.render("HCMUT  —  Machine Learning Evaluation", True, self.SUB_CLR)
        screen.blit(sub, sub.get_rect(center=(cx, cr.y + 60)))

        # Game Mode heading
        h1 = self.heading_font.render("GAME MODE", True, self.HEADING_CLR)
        screen.blit(h1, h1.get_rect(center=(cx, cr.y + 82)))

        for mode, r in self.mode_buttons:
            self._draw_btn(screen, r, mode, selected=(mode == self.selected_mode))

        # Divider
        pad = 30
        pygame.draw.line(screen, self.DIVIDER,
                         (cr.x + pad, self._divider_y),
                         (cr.x + cr.w - pad, self._divider_y), 1)

        # Difficulty heading
        needs_split = self.selected_mode == "AI vs AI"
        is_ml_mode = self.selected_mode in ("Human vs ML", "ML vs Random", "ML vs Search")
        if needs_split:
            h2_text = "RED AI  /  BLACK AI"
        elif is_ml_mode:
            h2_text = "ML LEVEL"
        else:
            h2_text = "DIFFICULTY"
        h2 = self.heading_font.render(h2_text, True, self.HEADING_CLR)
        screen.blit(h2, h2.get_rect(center=(cx, self._divider_y + 16)))

        if needs_split:
            for lv, r in self.red_level_buttons:
                self._draw_btn(screen, r, f"Red: {lv}", selected=(lv == self.selected_red_level))
            for lv, r in self.black_level_buttons:
                self._draw_btn(screen, r, f"Blk: {lv}", selected=(lv == self.selected_black_level))
        elif is_ml_mode:
            for lv, r in self.ml_level_buttons:
                self._draw_btn(screen, r, lv, selected=(lv == self.selected_ml_level))
        else:
            for lv, r in self.level_buttons:
                self._draw_btn(screen, r, lv, selected=(lv == self.selected_level))

        # Action buttons
        self._draw_btn(screen, self.start_button, "Start", kind="start")
        self._draw_btn(screen, self.quit_button,  "Quit",  kind="quit")

        # Status
        if self.selected_mode == "AI vs AI":
            info = f"{self.selected_mode}  ·  Red {self.selected_red_level}  vs  Black {self.selected_black_level}"
        elif self.selected_mode in ("Human vs ML", "ML vs Random", "ML vs Search"):
            info = f"{self.selected_mode}  ·  ML {self.selected_ml_level}"
        else:
            info = f"{self.selected_mode}  ·  {self.selected_level}"
        info_surf = self.small_font.render(info, True, self.INFO_CLR)
        screen.blit(info_surf, info_surf.get_rect(center=(cx, self.quit_button.bottom + 14)))