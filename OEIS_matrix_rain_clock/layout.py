from __future__ import annotations

from .digit_font import ASCII_DIGITS

GridCell = tuple[int, int]
FactTarget = tuple[GridCell, str]


def wrap_text_to_grid(text: str, max_cols: int) -> list[str]:
    words = text.split(" ")
    lines: list[str] = []
    current_line = ""

    for word in words:
        separator = 1 if current_line else 0
        if len(current_line) + len(word) + separator <= max_cols:
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def get_time_pixels(time_str: str, columns: int, rows: int) -> dict[GridCell, int]:
    active_pixels: dict[GridCell, int] = {}
    time_width = sum(len(ASCII_DIGITS[char][0]) + 1 for char in time_str) - 1
    time_start_col = (columns - time_width) // 2
    time_start_row = rows // 8

    current_col = time_start_col
    for char in time_str:
        matrix = ASCII_DIGITS[char]
        for row_index, row_str in enumerate(matrix):
            for col_index, value in enumerate(row_str):
                if value == "#":
                    active_pixels[(current_col + col_index, time_start_row + row_index)] = 255
                elif value == "+":
                    active_pixels[(current_col + col_index, time_start_row + row_index)] = 120
        current_col += len(matrix[0]) + 1

    return active_pixels


def get_fact_targets(fact_text: str, columns: int, rows: int) -> list[FactTarget]:
    ordered_targets: list[FactTarget] = []
    if not fact_text:
        return ordered_targets

    max_fact_cols = columns - 8
    fact_lines = wrap_text_to_grid(fact_text, max_fact_cols)
    digit_height = len(next(iter(ASCII_DIGITS.values())))
    current_row = (rows // 8) + digit_height + 1

    for line in fact_lines:
        start_col = (columns - len(line)) // 2
        for index, char in enumerate(line):
            ordered_targets.append(((start_col + index, current_row), char))
        current_row += 1

    return ordered_targets
