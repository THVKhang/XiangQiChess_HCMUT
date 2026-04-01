import os
import pygame


def pick_font(size: int):
    # Prefer CJK-capable fonts if available.
    for name in [
        "Microsoft YaHei",
        "SimSun",
        "KaiTi",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "segoeui",
    ]:
        try:
            return pygame.font.SysFont(name, size, bold=True)
        except Exception:
            continue
    return pygame.font.SysFont(None, size, bold=True)


def has_distinct_cjk(font):
    # If these surfaces are identical, the font is likely drawing tofu boxes.
    test_chars = ["帥", "將", "炮", "車"]
    blobs = []
    for ch in test_chars:
        surf = font.render(ch, True, (0, 0, 0))
        blobs.append(pygame.image.tostring(surf, "RGBA"))
    return len(set(blobs)) > 1


def main():
    pygame.init()
    os.makedirs(os.path.dirname(__file__), exist_ok=True)

    size = 220
    themes = {
        "classic": {
            "bg": (245, 230, 200),
            "ring_red": (190, 50, 50),
            "ring_black": (40, 40, 40),
            "inner_ring": 8,
        },
        "flat": {
            "bg": (252, 242, 216),
            "ring_red": (170, 40, 40),
            "ring_black": (30, 30, 30),
            "inner_ring": 4,
        },
        "wood": {
            "bg": (232, 206, 160),
            "ring_red": (155, 55, 42),
            "ring_black": (58, 46, 34),
            "inner_ring": 6,
        },
    }

    pieces = {
        "general": ("帥", "將", "K"),
        "advisor": ("仕", "士", "A"),
        "elephant": ("相", "象", "E"),
        "knight": ("傌", "馬", "H"),
        "rook": ("俥", "車", "R"),
        "cannon": ("炮", "砲", "C"),
        "pawn": ("兵", "卒", "P"),
    }

    cjk_font = pick_font(118)
    ascii_font = pygame.font.SysFont("segoeui", 98, bold=True)
    use_cjk = has_distinct_cjk(cjk_font)

    base_assets = os.path.dirname(__file__)
    for theme_name, cfg in themes.items():
        theme_dir = os.path.join(base_assets, theme_name)
        os.makedirs(theme_dir, exist_ok=True)
        bg = cfg["bg"]
        ring_red = cfg["ring_red"]
        ring_black = cfg["ring_black"]
        ring_width = cfg["inner_ring"]

        for name, (red_char, black_char, code) in pieces.items():
            for color_name, char, ring in [
                ("red", red_char, ring_red),
                ("black", black_char, ring_black),
            ]:
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                center = size // 2

                pygame.draw.circle(surf, bg, (center, center), 98)
                pygame.draw.circle(surf, ring, (center, center), 96, ring_width)

                label = char if use_cjk else code
                font = cjk_font if use_cjk else ascii_font
                text = font.render(label, True, ring)
                rect = text.get_rect(center=(center, center))
                surf.blit(text, rect)

                out_path = os.path.join(theme_dir, f"{name}_{color_name}.png")
                pygame.image.save(surf, out_path)
                print(f"Generated: {out_path}")

    pygame.quit()


if __name__ == "__main__":
    main()
