from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DisplayConfig:
    width: int
    height: int
    font_size: int
    target_fps: int
    background_color: tuple[int, int, int]


@dataclass(frozen=True)
class DigitalRainConfig:
    head_color: tuple[int, int, int]
    tail_color: tuple[int, int, int]
    alpha: int
    screen_fade_alpha: int
    character_set: str
    font_name: str | None


@dataclass(frozen=True)
class TimeDigitsConfig:
    color: tuple[int, int, int]
    fade_alpha: int
    max_overlap_stack: int


@dataclass(frozen=True)
class FactCharactersConfig:
    color: tuple[int, int, int]
    cursor_color: tuple[int, int, int]
    link_color: tuple[int, int, int]
    background_alpha: int
    reveal_window_size: int


@dataclass(frozen=True)
class AnimationConfig:
    fall_speed: float
    drop_reset_chance: float


@dataclass(frozen=True)
class SequenceLengthPenaltyConfig:
    min_length: int
    penalty: int


@dataclass(frozen=True)
class SequenceRankingConfig:
    comment_weight: int
    keyword_weights: dict[str, int]
    name_contains_weights: dict[str, int]
    length_penalties: tuple[SequenceLengthPenaltyConfig, ...]


@dataclass(frozen=True)
class ApiConfig:
    prime_factor_chance: float
    sequence_ranking: SequenceRankingConfig


@dataclass(frozen=True)
class AppConfig:
    display: DisplayConfig
    digital_rain: DigitalRainConfig
    time_digits: TimeDigitsConfig
    fact_characters: FactCharactersConfig
    animation: AnimationConfig
    api: ApiConfig


def _to_color(values: list[int]) -> tuple[int, int, int]:
    if len(values) != 3:
        raise ValueError(f"Expected 3 color channels, got {values!r}")
    return tuple(int(channel) for channel in values)


def _to_int_dict(mapping: dict | None, default: dict[str, int]) -> dict[str, int]:
    result = default.copy()
    if not mapping:
        return result

    for key, value in mapping.items():
        result[str(key).strip().lower()] = int(value)
    return result


def _load_sequence_ranking_config(api_config: dict) -> SequenceRankingConfig:
    default_keyword_weights = {
        "core": 50,
        "nice": 30,
        "easy": 10,
    }
    default_name_contains_weights = {
        "prime": 60,
    }

    apply_length_penalty = bool(api_config.get("apply_length_penalty", True))
    default_length_penalties = (
        (
            SequenceLengthPenaltyConfig(min_length=80, penalty=20),
            SequenceLengthPenaltyConfig(min_length=120, penalty=50),
        )
        if apply_length_penalty
        else ()
    )

    ranking_data = api_config.get("sequence_ranking", {})
    penalty_data = ranking_data.get("length_penalties")

    if penalty_data is None:
        length_penalties = default_length_penalties
    else:
        length_penalties = tuple(
            SequenceLengthPenaltyConfig(
                min_length=int(item["min_length"]),
                penalty=int(item["penalty"]),
            )
            for item in penalty_data
        )

    return SequenceRankingConfig(
        comment_weight=int(ranking_data.get("comment_weight", 1)),
        keyword_weights=_to_int_dict(
            ranking_data.get("keyword_weights"), default_keyword_weights
        ),
        name_contains_weights=_to_int_dict(
            ranking_data.get("name_contains_weights"),
            default_name_contains_weights,
        ),
        length_penalties=tuple(
            sorted(length_penalties, key=lambda item: item.min_length)
        ),
    )


def load_config(filepath: str = "clock_settings.yaml") -> AppConfig:
    path = Path(filepath)

    try:
        with path.open("r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
    except Exception as exc:
        raise RuntimeError(f"Config load failed for '{filepath}': {exc}") from exc

    if not config_data:
        raise RuntimeError(f"'{filepath}' is empty.")

    return AppConfig(
        display=DisplayConfig(
            width=int(config_data["display"]["width"]),
            height=int(config_data["display"]["height"]),
            font_size=int(config_data["display"]["font_size"]),
            target_fps=int(config_data["display"]["target_fps"]),
            background_color=_to_color(
                config_data["display"].get("background_color", [0, 0, 0])
            ),
        ),
        digital_rain=DigitalRainConfig(
            head_color=_to_color(config_data["digital_rain"]["head_color"]),
            tail_color=_to_color(config_data["digital_rain"]["tail_color"]),
            alpha=int(config_data["digital_rain"].get("alpha", 255)),
            screen_fade_alpha=int(
                config_data["digital_rain"].get("screen_fade_alpha", 15)
            ),
            character_set=str(
                config_data["digital_rain"].get("character_set", "classic")
            ).strip().lower(),
            font_name=(
                str(config_data["digital_rain"]["font_name"]).strip()
                if config_data["digital_rain"].get("font_name")
                else None
            ),
        ),
        time_digits=TimeDigitsConfig(
            color=_to_color(config_data["time_digits"]["color"]),
            fade_alpha=int(config_data["time_digits"].get("fade_alpha", 3)),
            max_overlap_stack=int(
                config_data["time_digits"].get("max_overlap_stack", 3)
            ),
        ),
        fact_characters=FactCharactersConfig(
            color=_to_color(config_data["fact_characters"].get("color", [255, 255, 255])),
            cursor_color=_to_color(
                config_data["fact_characters"].get("cursor_color", [0, 255, 0])
            ),
            link_color=_to_color(
                config_data["fact_characters"].get("link_color", [100, 255, 100])
            ),
            background_alpha=int(
                config_data["fact_characters"].get("background_alpha", 200)
            ),
            reveal_window_size=int(
                config_data["fact_characters"].get("reveal_window_size", 1)
            ),
        ),
        animation=AnimationConfig(
            fall_speed=float(config_data["animation"].get("fall_speed", 1.0)),
            drop_reset_chance=float(
                config_data["animation"].get("drop_reset_chance", 0.95)
            ),
        ),
        api=ApiConfig(
            prime_factor_chance=float(
                config_data["api"].get("prime_factor_chance", 0.25)
            ),
            sequence_ranking=_load_sequence_ranking_config(config_data["api"]),
        ),
    )
