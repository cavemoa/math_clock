from __future__ import annotations

import random

import pygame

from .config import AppConfig
from .digit_font import get_rain_characters


class MatrixRainRenderer:
    def __init__(self, config: AppConfig) -> None:
        pygame.init()

        self.config = config
        self.width = config.display.width
        self.height = config.display.height
        self.font_size = config.display.font_size
        self.background_color = config.display.background_color

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Matrix Math Clock - Interactive Data")
        self.clock = pygame.time.Clock()
        self.text_font = self._build_text_font()
        self.rain_font = self._build_rain_font()
        self.rain_chars = get_rain_characters(config.digital_rain.character_set)

        self.fade_surface = pygame.Surface((self.width, self.height))
        self.fade_surface.fill(self.background_color)
        self.fade_surface.set_alpha(config.digital_rain.screen_fade_alpha)

        self.fact_mask_surface = pygame.Surface((self.font_size, self.font_size))
        self.fact_mask_surface.fill(self.background_color)
        self.fact_mask_surface.set_alpha(config.fact_characters.background_alpha)

        self.columns = self.width // self.font_size
        self.rows = self.height // self.font_size
        self.drops = [
            float(random.randint(-50, 0)) for _ in range(self.columns)
        ]

    def get_mouse_position(self) -> tuple[int, int]:
        return pygame.mouse.get_pos()

    def _load_font_from_candidates(
        self, font_names: list[str], bold: bool = False
    ) -> pygame.font.Font:
        for font_name in font_names:
            match = pygame.font.match_font(font_name, bold=bold)
            if match:
                return pygame.font.Font(match, self.font_size)
        return pygame.font.Font(None, self.font_size)

    def _build_text_font(self) -> pygame.font.Font:
        return self._load_font_from_candidates(
            ["Consolas", "DejaVu Sans Mono", "Courier New"], bold=True
        )

    def _build_rain_font(self) -> pygame.font.Font:
        candidates: list[str] = []
        if self.config.digital_rain.font_name:
            candidates.append(self.config.digital_rain.font_name)

        if self.config.digital_rain.character_set == "math":
            candidates.extend(
                [
                    "Noto Sans Math",
                    "Cambria Math",
                    "STIX Two Math",
                    "STIXGeneral",
                    "DejaVu Sans",
                    "Segoe UI Symbol",
                ]
            )
        else:
            candidates.extend(["Consolas", "DejaVu Sans Mono", "Courier New"])

        return self._load_font_from_candidates(candidates)

    def _blit_grid_character(
        self,
        font: pygame.font.Font,
        char: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
        alpha: int | None = None,
    ) -> None:
        char_surface = font.render(char, True, color)
        if alpha is not None:
            char_surface.set_alpha(alpha)
        char_rect = char_surface.get_rect(
            center=(x + (self.font_size // 2), y + (self.font_size // 2))
        )
        self.screen.blit(char_surface, char_rect)

    def clear_frame(self) -> None:
        self.screen.blit(self.fade_surface, (0, 0))

    def draw_rain_and_collide(
        self,
        time_pixel_targets: dict[tuple[int, int], int],
        active_time_pixels: dict[tuple[int, int], list[dict[str, object]]],
    ) -> None:
        for column_index in range(len(self.drops)):
            drop_row_int = int(self.drops[column_index])
            x = column_index * self.font_size
            y = drop_row_int * self.font_size

            head_char = random.choice(self.rain_chars)
            self._blit_grid_character(
                self.rain_font,
                head_char,
                self.config.digital_rain.head_color,
                x,
                y,
                alpha=self.config.digital_rain.alpha,
            )

            if drop_row_int > 0:
                tail_char = random.choice(self.rain_chars)
                self._blit_grid_character(
                    self.rain_font,
                    tail_char,
                    self.config.digital_rain.tail_color,
                    x,
                    y - self.font_size,
                    alpha=self.config.digital_rain.alpha,
                )

            current_drop_y = self.drops[column_index]
            previous_drop_y = current_drop_y - self.config.animation.fall_speed

            for target_row in range(self.rows):
                target = (column_index, target_row)
                if target in time_pixel_targets and previous_drop_y < target_row <= current_drop_y:
                    active_stack = active_time_pixels.setdefault(target, [])
                    if len(active_stack) >= self.config.time_digits.max_overlap_stack:
                        active_stack.pop(0)
                    active_stack.append(
                        {
                            "char": random.choice(self.rain_chars),
                            "alpha": float(time_pixel_targets[target]),
                        }
                    )

            self.drops[column_index] += self.config.animation.fall_speed

            if y > self.height and random.random() > self.config.animation.drop_reset_chance:
                self.drops[column_index] = 0.0

    def draw_active_time_pixels(
        self, active_time_pixels: dict[tuple[int, int], list[dict[str, object]]]
    ) -> None:
        keys_to_remove = []

        for (col, row), stack in active_time_pixels.items():
            if not stack:
                keys_to_remove.append((col, row))
                continue

            x = col * self.font_size
            y = row * self.font_size
            max_alpha = max(float(data["alpha"]) for data in stack)

            mask_surface = pygame.Surface((self.font_size, self.font_size))
            mask_surface.fill(self.background_color)
            mask_surface.set_alpha(int(max_alpha))
            self.screen.blit(mask_surface, (x, y))

            for data in stack:
                self._blit_grid_character(
                    self.rain_font,
                    str(data["char"]),
                    self.config.time_digits.color,
                    x,
                    y,
                    alpha=int(float(data["alpha"])),
                )
                data["alpha"] = float(data["alpha"]) - self.config.time_digits.fade_alpha

            active_time_pixels[(col, row)] = [
                data for data in stack if float(data["alpha"]) > 0
            ]
            if not active_time_pixels[(col, row)]:
                keys_to_remove.append((col, row))

        for key in keys_to_remove:
            active_time_pixels.pop(key, None)

    def reveal_fact_characters(
        self, fact_targets: list[tuple[tuple[int, int], str]], revealed_flags: list[bool]
    ) -> list[int]:
        unrevealed_indices = [
            index for index, is_revealed in enumerate(revealed_flags) if not is_revealed
        ]

        if unrevealed_indices:
            active_window = unrevealed_indices[
                : self.config.fact_characters.reveal_window_size
            ]
            for index in active_window:
                (target_col, target_row), _ = fact_targets[index]
                current_drop_y = self.drops[target_col]
                previous_drop_y = current_drop_y - self.config.animation.fall_speed

                if previous_drop_y < target_row <= current_drop_y:
                    revealed_flags[index] = True

        return unrevealed_indices

    def draw_revealed_fact(
        self, fact_targets: list[tuple[tuple[int, int], str]], revealed_flags: list[bool]
    ) -> None:
        for index, ((col, row), char) in enumerate(fact_targets):
            if revealed_flags[index]:
                x = col * self.font_size
                y = row * self.font_size
                self.screen.blit(self.fact_mask_surface, (x, y))
                self._blit_grid_character(
                    self.text_font,
                    char,
                    self.config.fact_characters.color,
                    x,
                    y,
                )

    def draw_cursor(
        self, fact_targets: list[tuple[tuple[int, int], str]], unrevealed_indices: list[int]
    ) -> None:
        if not unrevealed_indices:
            return
        if (pygame.time.get_ticks() // 200) % 2 != 0:
            return

        first_unrevealed = unrevealed_indices[0]
        (cursor_col, cursor_row), _ = fact_targets[first_unrevealed]
        cursor_rect = pygame.Rect(
            cursor_col * self.font_size,
            cursor_row * self.font_size,
            max(2, self.font_size // 3),
            self.font_size,
        )
        pygame.draw.rect(
            self.screen, self.config.fact_characters.cursor_color, cursor_rect
        )

    def draw_link(
        self, seq_id: str | None, mouse_pos: tuple[int, int]
    ) -> pygame.Rect | None:
        if not seq_id:
            return None

        link_str = f"[{seq_id}]"
        link_surf = self.text_font.render(
            link_str, True, self.config.fact_characters.link_color
        )
        link_rect = link_surf.get_rect(bottomright=(self.width - 15, self.height - 15))

        is_hovering = link_rect.collidepoint(mouse_pos)
        if is_hovering:
            link_surf = self.text_font.render(
                link_str, True, self.config.fact_characters.color
            )

        link_mask = pygame.Surface(link_rect.size)
        link_mask.fill(self.background_color)
        link_mask.set_alpha(self.config.fact_characters.background_alpha)

        self.screen.blit(link_mask, link_rect.topleft)
        self.screen.blit(link_surf, link_rect.topleft)
        return link_rect

    def present(self) -> None:
        pygame.display.flip()
        self.clock.tick(self.config.display.target_fps)

    def shutdown(self) -> None:
        pygame.quit()
