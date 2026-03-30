from __future__ import annotations

import random

import pygame

from .config import AppConfig
from .digit_font import MATRIX_CHARS


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
        self.font = pygame.font.SysFont("consolas", self.font_size, bold=True)

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

            head_char = random.choice(MATRIX_CHARS)
            head_surface = self.font.render(
                head_char, True, self.config.digital_rain.head_color
            )
            head_surface.set_alpha(self.config.digital_rain.alpha)
            self.screen.blit(head_surface, (x, y))

            if drop_row_int > 0:
                tail_char = random.choice(MATRIX_CHARS)
                tail_surface = self.font.render(
                    tail_char, True, self.config.digital_rain.tail_color
                )
                tail_surface.set_alpha(self.config.digital_rain.alpha)
                self.screen.blit(tail_surface, (x, y - self.font_size))

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
                            "char": random.choice(MATRIX_CHARS),
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
                char_surface = self.font.render(
                    str(data["char"]), True, self.config.time_digits.color
                )
                char_surface.set_alpha(int(float(data["alpha"])))
                self.screen.blit(char_surface, (x, y))
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
                self.screen.blit(
                    self.font.render(char, True, self.config.fact_characters.color),
                    (x, y),
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
        link_surf = self.font.render(
            link_str, True, self.config.fact_characters.link_color
        )
        link_rect = link_surf.get_rect(bottomright=(self.width - 15, self.height - 15))

        is_hovering = link_rect.collidepoint(mouse_pos)
        if is_hovering:
            link_surf = self.font.render(
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
