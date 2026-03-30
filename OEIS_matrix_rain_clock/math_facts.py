from __future__ import annotations

import re

import sympy


def get_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}" + ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]


def extract_index_context(number: int, seq: dict) -> str | None:
    try:
        data_str = seq.get("data", "")
        if not data_str:
            return None

        data_list = [item.strip() for item in data_str.split(",")]
        number_str = str(number)

        if number_str in data_list:
            array_pos = data_list.index(number_str)
            offset_str = seq.get("offset", "1").split(",")[0]
            try:
                start_index = int(offset_str)
            except ValueError:
                start_index = 1
            return get_ordinal(array_pos + start_index)
    except Exception:
        return None

    return None


def naturalize_fact(
    number: int, description: str, ordinal_str: str | None = None
) -> str:
    desc = description.strip().rstrip(".")
    lower_desc = desc.lower()

    exact_matches = {
        "primes": "a prime number",
        "composite numbers": "a composite number",
        "fibonacci numbers": "a Fibonacci number",
        "odd numbers": "an odd number",
        "even numbers": "an even number",
        "triangular numbers": "a triangular number",
        "perfect numbers": "a perfect number",
    }

    if lower_desc in exact_matches:
        desc = exact_matches[lower_desc]
    else:
        desc = re.sub(
            r"^([a-zA-Z\s\-]+) numbers$",
            r"a \1 number",
            desc,
            flags=re.IGNORECASE,
        )
        desc = re.sub(
            r"^(?:Numbers|Integers)(?:\s+[a-z])?\s+such that\s+",
            "a number such that ",
            desc,
            flags=re.IGNORECASE,
        )
        desc = re.sub(
            r"^(?:Numbers|Integers)\s+whose\s+",
            "a number whose ",
            desc,
            flags=re.IGNORECASE,
        )
        desc = re.sub(
            r"^(?:Numbers|Integers)\s+which\s+",
            "a number which ",
            desc,
            flags=re.IGNORECASE,
        )
        desc = re.sub(
            r"^(?:Numbers|Integers)\s+that\s+",
            "a number that ",
            desc,
            flags=re.IGNORECASE,
        )
        desc = re.sub(
            r"^Products\s+of\s+", "the product of ", desc, flags=re.IGNORECASE
        )
        desc = re.sub(r"^Sums\s+of\s+", "the sum of ", desc, flags=re.IGNORECASE)
        desc = re.sub(
            r"^Squares\s+of\s+", "the square of ", desc, flags=re.IGNORECASE
        )
        desc = re.sub(r"^Cubes\s+of\s+", "the cube of ", desc, flags=re.IGNORECASE)
        desc = re.sub(
            r"^Multiples\s+of\s+", "a multiple of ", desc, flags=re.IGNORECASE
        )
        desc = re.sub(r"^Powers\s+of\s+", "a power of ", desc, flags=re.IGNORECASE)

        first_word = desc.split(" ")[0]
        proper_nouns = [
            "Euler",
            "Fermat",
            "Fibonacci",
            "Catalan",
            "Mersenne",
            "Gaussian",
            "Cullen",
            "Bell",
        ]
        if (
            first_word.istitle()
            and first_word not in proper_nouns
            and not desc.startswith(("a ", "an ", "the "))
        ):
            desc = desc[0].lower() + desc[1:]

    if ordinal_str:
        if desc.startswith("a "):
            desc = f"the {ordinal_str} " + desc[2:]
        elif desc.startswith("an "):
            desc = f"the {ordinal_str} " + desc[3:]
        elif desc.startswith("the "):
            desc = f"the {ordinal_str} " + desc[4:]
        else:
            desc = f"the {ordinal_str} term in the sequence of {desc}"
    elif not desc.startswith(("a ", "an ", "the ")):
        return f"{number} is characterized as: {desc}."

    return f"{number} is {desc}."


def get_prime_factors_string(number: int) -> str | None:
    if number < 2:
        return None

    factors = sympy.factorint(number)
    if len(factors) == 1 and list(factors.values())[0] == 1:
        return None

    parts = []
    for prime, exponent in factors.items():
        if exponent == 1:
            parts.append(str(prime))
        else:
            parts.append(f"{prime}^{exponent}")

    return " * ".join(parts)


def get_fallback_fact(number: int) -> str:
    if number % 2 == 0:
        return f"{number} is an even number, divisible by 2."
    return f"{number} is an odd number. It cannot be divided evenly by 2."


def extract_best_sequence(
    results_list: list[dict], apply_length_penalty: bool
) -> dict | None:
    best_seq = None
    highest_score = -100

    for seq in results_list:
        score = 0
        keywords = seq.get("keyword", "").split(",")
        name = seq.get("name", "")

        if "core" in keywords:
            score += 50
        if "nice" in keywords:
            score += 30
        if "easy" in keywords:
            score += 10
        if "prime" in name.lower():
            score += 60

        score += len(seq.get("comment", []))

        if apply_length_penalty:
            if len(name) > 80:
                score -= 20
            if len(name) > 120:
                score -= 50

        if score > highest_score:
            highest_score = score
            best_seq = seq

    return best_seq
