from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import requests

from .math_facts import (
    extract_best_sequence,
    extract_index_context,
    get_fallback_fact,
    naturalize_fact,
)

if TYPE_CHECKING:
    from .config import SequenceRankingConfig


@dataclass(frozen=True)
class FactResult:
    text: str
    seq_id: str | None


def fetch_oeis_fact(
    number: int, ranking_config: "SequenceRankingConfig", timeout: float = 5.0
) -> FactResult:
    url = f"https://oeis.org/search?q={number}&fmt=json"

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                results_list = [
                    item
                    for item in data
                    if isinstance(item, dict) and "number" in item and "name" in item
                ]
                if results_list:
                    best_seq = extract_best_sequence(results_list, ranking_config)
                    if best_seq:
                        ordinal = extract_index_context(number, best_seq)
                        seq_id = f"A{best_seq['number']:06d}"
                        return FactResult(
                            text=naturalize_fact(number, best_seq["name"], ordinal),
                            seq_id=seq_id,
                        )
    except requests.exceptions.RequestException:
        pass

    return FactResult(text=get_fallback_fact(number), seq_id=None)
