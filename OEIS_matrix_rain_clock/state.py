from __future__ import annotations

from dataclasses import dataclass, field

GridCell = tuple[int, int]
TimePixelStackEntry = dict[str, object]
FactTarget = tuple[GridCell, str]


@dataclass(frozen=True)
class PrefetchedFact:
    text: str
    seq_id: str | None


@dataclass
class AppState:
    current_time_str: str = ""
    display_fact_text: str = ""
    time_pixel_targets: dict[GridCell, int] = field(default_factory=dict)
    active_time_pixels: dict[GridCell, list[TimePixelStackEntry]] = field(
        default_factory=dict
    )
    fact_targets: list[FactTarget] = field(default_factory=list)
    revealed_flags: list[bool] = field(default_factory=list)
    current_seq_id: str | None = None
    link_rect: object | None = None
