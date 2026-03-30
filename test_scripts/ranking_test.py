from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from OEIS_matrix_rain_clock.config import load_config
from OEIS_matrix_rain_clock.math_facts import (  # noqa: E402
    extract_index_context,
    naturalize_fact,
    score_sequence,
)


DEFAULT_REPEATABLE_NUMBERS = [
    610,
    1200,
    1147,
    1605,
    1729,
    2016,
    2222,
    541,
    1000,
    1040,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Query OEIS slowly and inspect how the current YAML sequence-ranking "
            "configuration chooses facts."
        )
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=10,
        help="How many numbers to test. Default: 10.",
    )
    parser.add_argument(
        "--mode",
        choices=["random", "repeatable", "custom"],
        default="repeatable",
        help=(
            "How test numbers are chosen. "
            "'repeatable' uses a fixed built-in list, "
            "'random' generates HHMM-style values, "
            "'custom' uses --numbers."
        ),
    )
    parser.add_argument(
        "--numbers",
        nargs="+",
        type=int,
        help="Explicit numbers to test when using --mode custom.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used in random mode. Default: 42.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between OEIS queries. Default: 2.0.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="How many ranked OEIS candidates to print per query. Default: 5.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds per OEIS request. Default: 5.0.",
    )
    parser.add_argument(
        "--config",
        default="clock_settings.yaml",
        help="Path to the YAML config file. Default: clock_settings.yaml.",
    )
    return parser.parse_args()


def build_test_numbers(args: argparse.Namespace) -> list[int]:
    if args.mode == "custom":
        if not args.numbers:
            raise ValueError("--mode custom requires --numbers.")
        return args.numbers[: args.count]

    if args.mode == "repeatable":
        numbers: list[int] = []
        while len(numbers) < args.count:
            numbers.extend(DEFAULT_REPEATABLE_NUMBERS)
        return numbers[: args.count]

    rng = random.Random(args.seed)
    return [rng.randint(0, 2359) for _ in range(args.count)]


def format_time_like(number: int) -> str:
    padded = f"{number:04d}"
    return f"{padded[:2]}:{padded[2:]}"


def fetch_candidates(number: int, timeout: float) -> list[dict]:
    url = f"https://oeis.org/search?q={number}&fmt=json"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        return []

    return [
        item
        for item in data
        if isinstance(item, dict) and "number" in item and "name" in item
    ]


def print_candidate_summary(
    number: int,
    ranked_candidates: list[tuple[int, dict]],
    top_count: int,
) -> None:
    if not ranked_candidates:
        print("  Result: No OEIS candidates returned.\n")
        return

    winning_score, winning_seq = ranked_candidates[0]
    ordinal = extract_index_context(number, winning_seq)
    natural_text = naturalize_fact(number, winning_seq["name"], ordinal)

    seq_id = f"A{winning_seq['number']:06d}"
    print(f"  Winner: {seq_id} | score={winning_score}")
    print(f"  Raw:    {winning_seq['name']}")
    if ordinal:
        print(f"  Index:  {ordinal}")
    print(f"  Parsed: {natural_text}")
    print("  Top candidates:")

    for score, seq in ranked_candidates[:top_count]:
        candidate_id = f"A{seq['number']:06d}"
        print(f"    {candidate_id} | score={score} | {seq['name']}")

    print()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    ranking_config = config.api.sequence_ranking
    numbers = build_test_numbers(args)

    print(
        f"--- OEIS Ranking Diagnostics ({len(numbers)} queries, mode={args.mode}, "
        f"delay={args.delay:.1f}s) ---"
    )
    if args.mode == "random":
        print(f"Seed: {args.seed}")
    elif args.mode == "repeatable":
        print(f"Repeatable base list: {DEFAULT_REPEATABLE_NUMBERS}")
    elif args.mode == "custom":
        print(f"Custom numbers: {numbers}")
    print()

    for index, number in enumerate(numbers, start=1):
        time_like = format_time_like(number)
        print(f"Test {index}/{len(numbers)} | Query: {number} | Time-like: {time_like}")

        try:
            candidates = fetch_candidates(number, timeout=args.timeout)
        except requests.exceptions.RequestException as exc:
            print(f"  Request failed: {exc}\n")
        else:
            ranked_candidates = sorted(
                (
                    (score_sequence(candidate, ranking_config), candidate)
                    for candidate in candidates
                ),
                key=lambda item: item[0],
                reverse=True,
            )
            print_candidate_summary(number, ranked_candidates, args.top)

        if index < len(numbers):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
