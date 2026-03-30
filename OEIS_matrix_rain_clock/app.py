from __future__ import annotations

import datetime
import random
import threading
import webbrowser

import pygame

from .config import load_config
from .layout import get_fact_targets, get_time_pixels
from .math_facts import get_prime_factors_string
from .oeis_client import fetch_oeis_fact
from .renderer import MatrixRainRenderer
from .state import AppState, PrefetchedFact


class MatrixRainClockApp:
    def __init__(self, config_path: str = "clock_settings.yaml") -> None:
        self.config = load_config(config_path)
        self.renderer = MatrixRainRenderer(self.config)
        self.state = AppState()
        self.prefetched_facts: dict[str, PrefetchedFact] = {}
        self.prefetch_lock = threading.Lock()

    def background_fetcher(self, time_str: str, number: int) -> None:
        result = fetch_oeis_fact(number, self.config.api.sequence_ranking)
        fact_text = result.text

        if random.random() < self.config.api.prime_factor_chance:
            factors_str = get_prime_factors_string(number)
            if factors_str:
                fact_text += f" Its prime factorization is {factors_str}."

        with self.prefetch_lock:
            self.prefetched_facts[time_str] = PrefetchedFact(
                text=fact_text,
                seq_id=result.seq_id,
            )

    def start_prefetch(self, time_str: str, number: int) -> None:
        with self.prefetch_lock:
            if time_str in self.prefetched_facts:
                return

        threading.Thread(
            target=self.background_fetcher,
            args=(time_str, number),
            daemon=True,
        ).start()

    def update_display_for_time(self, time_str: str) -> None:
        with self.prefetch_lock:
            prefetched = self.prefetched_facts.get(time_str)

        if prefetched is None:
            number = int(time_str.replace(":", ""))
            self.start_prefetch(time_str, number)
            display_fact = f"Loading sequence for {time_str.replace(':', '')}..."
            seq_id = None
        else:
            display_fact = prefetched.text
            seq_id = prefetched.seq_id

        if (
            time_str == self.state.current_time_str
            and display_fact == self.state.display_fact_text
            and seq_id == self.state.current_seq_id
        ):
            return

        self.state.current_time_str = time_str
        self.state.display_fact_text = display_fact
        self.state.current_seq_id = seq_id
        self.state.time_pixel_targets = get_time_pixels(
            time_str, self.renderer.columns, self.renderer.rows
        )
        self.state.fact_targets = get_fact_targets(
            display_fact, self.renderer.columns, self.renderer.rows
        )
        self.state.revealed_flags = [False] * len(self.state.fact_targets)

    def run(self) -> None:
        running = True

        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M")
        self.start_prefetch(now_str, int(now.strftime("%H%M")))

        while running:
            mouse_pos = self.renderer.get_mouse_position()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.state.link_rect
                    and self.state.current_seq_id
                    and self.state.link_rect.collidepoint(event.pos)
                ):
                    webbrowser.open(f"https://oeis.org/{self.state.current_seq_id}")

            now = datetime.datetime.now()
            now_str = now.strftime("%H:%M")
            self.update_display_for_time(now_str)

            next_minute = now + datetime.timedelta(minutes=1)
            self.start_prefetch(
                next_minute.strftime("%H:%M"),
                int(next_minute.strftime("%H%M")),
            )

            self.renderer.clear_frame()
            self.renderer.draw_rain_and_collide(
                self.state.time_pixel_targets, self.state.active_time_pixels
            )
            self.renderer.draw_active_time_pixels(self.state.active_time_pixels)
            unrevealed_indices = self.renderer.reveal_fact_characters(
                self.state.fact_targets, self.state.revealed_flags
            )
            self.renderer.draw_revealed_fact(
                self.state.fact_targets, self.state.revealed_flags
            )
            self.renderer.draw_cursor(self.state.fact_targets, unrevealed_indices)
            self.state.link_rect = self.renderer.draw_link(
                self.state.current_seq_id, mouse_pos
            )
            self.renderer.present()

        self.renderer.shutdown()


def main(config_path: str = "clock_settings.yaml") -> None:
    app = MatrixRainClockApp(config_path=config_path)
    app.run()
