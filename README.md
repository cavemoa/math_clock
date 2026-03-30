# Matrix Math Clock ⏱️🧮

A cyberpunk-inspired, generative ASCII-art clock that displays the current time and reveals highly obscure, mathematically significant facts about that specific time (e.g., 11:47 -> 1147) using real-time data from the On-Line Encyclopedia of Integer Sequences (OEIS).

## ✨ Features

* **Generative Matrix Rain Engine:** A custom-built Pygame engine that simulates the iconic falling green code.
* **ASCII Art Time Display:** The current time is rendered in large block digits that dynamically "catch" falling rain, selectively fading and replenishing only the digits that change when the minute rolls over.
* **Organic Text Decryption:** The math facts don't just appear; they are deposited onto the screen letter-by-letter precisely when a drop of digital rain passes over their grid coordinates.
* **Natural Language Parsing (NLP):** Raw, academic mathematical fragments from the OEIS database are heuristically parsed into natural English sentences on the fly.
* **Contextual Ordinal Math:** Calculates exactly where the time sits within a sequence (e.g., "1605 is the **24th** Catalan number").
* **Prime Factorization:** Randomly calculates and appends the prime factorization of the current time using CPU-bound mathematics.
* **Multi-Threaded Pre-fetching:** The clock quietly queries the internet for the *next* minute's fact in a background thread, ensuring the visual animation never freezes or drops frames.
* **Fully Configurable:** Almost every visual and functional aspect can be tweaked without touching the Python code via a simple YAML file.

## 🛠️ Prerequisites

This project requires **Python 3.7+**. 

You will also need to install the following third-party libraries:
* `pygame` (Visual rendering engine)
* `pyyaml` (Configuration management)
* `requests` (API network fetching)
* `sympy` (Fast prime factorization)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/matrix-math-clock.git](https://github.com/yourusername/matrix-math-clock.git)
   cd matrix-math-clock
   ```

2. Install the required dependencies:
   ```bash
   pip install pygame pyyaml requests sympy
   ```

3. Ensure `clock_settings.yaml` is in the same directory as the main script.

4. Run the clock:
   ```bash
   python main_clock.py
   ```
   *(Press `ESC` or close the window to exit).*

## ⚙️ Configuration (`clock_settings.yaml`)

The clock's behavior and aesthetics are controlled entirely by the `clock_settings.yaml` file. 

### Display & Colors
* Adjust the `width`, `height`, and `font_size` to fit your monitor or Raspberry Pi display.
* Colors are defined in standard `[R, G, B]` format.
* `rain_alpha`: Controls the brightness of the falling code.
* `fade_alpha`: Controls how long the "trails" of the falling code remain on screen before fading to black.

### Animation Dynamics
* `fall_speed`: Determines how fast the drops fall. (e.g., `1.0` is standard, `0.5` is slow, `2.0` is fast). Fractional speeds allow for smooth, jittery terminal effects.
* `reveal_window_size`: Determines how many upcoming letters in the math fact act as "tripwires" for the falling rain. A higher number makes the text decrypt faster and more chaotically.

### API & Data
* `apply_length_penalty`: If `true`, the scoring algorithm prioritizes shorter, punchier math facts to fit neatly on the screen.
* `prime_factor_chance`: A float between `0.0` and `1.0`. For example, `0.25` gives the clock a 25% chance every minute to calculate and append the prime factorization to the OEIS fact.

## 🧠 How it Works (Architecture)

1. **The Grid:** The screen is divided into a rigid column/row grid based on the chosen font size. 
2. **The Fetcher:** When the minute changes, a background thread calculates the *next* minute (e.g., `1148`), pings the OEIS JSON API, ranks the returned sequences based on algorithmic fame/simplicity, and passes the winner through the NLP grammar router.
3. **The Lock:** The parsed text is mapped to specific target coordinates on the Pygame grid.
4. **The Collision:** As the Pygame loop iterates, it checks the physical intersection of the falling `drops` array against the unrevealed target coordinates. When an intersection occurs, the text permanently locks into place, shielding itself from the background rain.

## 📝 Offline Fallback
If the clock loses internet connectivity, it gracefully falls back to local mathematical calculations (e.g., Even/Odd checking) while continuing to run the prime factorization engine, ensuring the screen never goes blank.

