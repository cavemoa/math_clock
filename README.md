# Matrix Math Clock

A cyberpunk-inspired ASCII-art clock built with Pygame. It shows the current time as glowing matrix-style digits and reveals mathematical facts about that time's numeric form using the OEIS database. For example, `11:47` is treated as `1147` and looked up as an integer sequence value.

<p align="center">
  <img src="\images\screenshot_1.JPG" alt="Screenshot 1" width="45%" />
  <img src="\images\screenshot_2.JPG" alt="Screenshot 2" width="45%" />

</p>

## Overview

This repository now contains two runnable versions of the clock:

- `matrix_math_clock.py`: the original all-in-one single-script version.
- `run_oeis_matrix_rain_clock.py`: the entry point for the refactored module-based version.

Both versions use the same `clock_settings.yaml` configuration file and aim to produce the same overall visual effect.

## Versions

### Single-script version

`matrix_math_clock.py` is the original monolithic implementation. It contains configuration loading, OEIS fetching, math helpers, layout logic, rendering, and the main Pygame loop in one file.

Use this version if you want:

- the original implementation exactly as written
- a single file that is easy to copy and experiment with
- a reference point for comparing the refactored package

Run it with:

```bash
python matrix_math_clock.py
```

### Module version

`run_oeis_matrix_rain_clock.py` is a small entry-point script that launches the refactored `OEIS_matrix_rain_clock` package.

The package separates responsibilities across several files:

- `OEIS_matrix_rain_clock/config.py`: YAML loading and config objects
- `OEIS_matrix_rain_clock/digit_font.py`: ASCII digit definitions and matrix character set
- `OEIS_matrix_rain_clock/math_facts.py`: math helpers, OEIS text cleanup, and factorization
- `OEIS_matrix_rain_clock/oeis_client.py`: OEIS API fetching
- `OEIS_matrix_rain_clock/layout.py`: text wrapping and grid positioning
- `OEIS_matrix_rain_clock/renderer.py`: Pygame drawing logic
- `OEIS_matrix_rain_clock/state.py`: runtime state objects
- `OEIS_matrix_rain_clock/app.py`: application controller and main loop

Use this version if you want:

- cleaner code organization
- easier maintenance and extension
- a better starting point for adding tests or new features

Run it with:

```bash
python run_oeis_matrix_rain_clock.py
```

## Features

- Matrix-style digital rain rendered in Pygame
- Selectable rain character sets: classic or curated math symbols
- Large ASCII-art time display
- OEIS-backed facts for the current time interpreted as a number
- Heuristic conversion of OEIS sequence names into readable English
- Optional prime factorization appended to facts
- Background fetching so animation stays responsive
- Configurable colors, timing, and display behaviour through YAML

## Requirements

This project requires Python 3.7+ and these libraries:

- `pygame`
- `pyyaml`
- `requests`
- `sympy`

Install them with:

```bash
pip install pygame pyyaml requests sympy
```

## Configuration

Both versions read settings from `clock_settings.yaml`.

You can tune:

- display size and font size
- digital rain character set and preferred rain font
- rain colors and fade behaviour
- time digit appearance
- fact reveal speed
- OEIS scoring behaviour
- prime factorization frequency

### Digital rain character sets

The refactored module version supports two rain character sets through `clock_settings.yaml`:

```yaml
digital_rain:
  character_set: classic   # classic | math
  font_name: ""            # optional preferred rain font
```

- `classic` uses the original letters, digits, and symbols
- `math` uses a curated set of mathematical operators and symbols

When `character_set: math` is selected, the renderer will try to use a math-capable font automatically. If `font_name` is blank, it attempts safe fallbacks such as `Noto Sans Math`, `Cambria Math`, `STIX Two Math`, `DejaVu Sans`, and other available system fonts before falling back to Pygame's default font.

### OEIS ranking options

The refactored module version also lets you tune how OEIS search results are ranked before one is chosen for display:

```yaml
api:
  sequence_ranking:
    comment_weight: 1
    keyword_weights:
      core: 50
      nice: 30
      easy: 10
    name_contains_weights:
      prime: 60
    length_penalties:
      - min_length: 80
        penalty: 20
      - min_length: 120
        penalty: 50
```

- `comment_weight` rewards sequences with more OEIS comment lines
- `keyword_weights` boosts results whose OEIS keywords match entries like `core`, `nice`, or `easy`
- `name_contains_weights` boosts results whose title contains words or fragments you care about
- `length_penalties` discourages long titles that would produce awkward on-screen fact text

The defaults match the previous built-in behaviour, so if you do not change these values the sequence selection should feel the same as before.

## How It Works

1. The current time is converted from `HH:MM` to an integer like `1147`.
2. The clock queries OEIS for that number and scores returned sequences.
3. The best result is rewritten into more natural English.
4. The text is mapped onto the screen as hidden target characters.
5. Falling matrix rain reveals both the time digits and the fact text as it collides with those positions.

## Offline behaviour

If OEIS cannot be reached, the clock falls back to simple local facts such as even/odd classification, so the display still has something meaningful to show.

## Exit

Press `Esc` or close the Pygame window to exit either version.
