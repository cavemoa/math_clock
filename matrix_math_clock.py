import pygame
import random
import datetime
from datetime import timedelta
import yaml
import sys
import requests
import threading
import re
import sympy

# --- 1. Configuration ---
def load_config(filepath='clock_settings.yaml'):
    try:
        with open(filepath, 'r') as file:
            config_data = yaml.safe_load(file)
            if config_data is None:
                print(f"[Error] '{filepath}' is empty.")
                sys.exit(1)
            return config_data
    except Exception as e:
        print(f"[Error] Config load failed: {e}")
        sys.exit(1)

config = load_config()

# --- 2. Pygame Setup & YAML Mapping ---
pygame.init()
WIDTH = config['display']['width']
HEIGHT = config['display']['height']
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Matrix Math Clock - Monolithic Digits")
clock = pygame.time.Clock()

FONT_SIZE = config['display']['font_size']
font = pygame.font.SysFont('consolas', FONT_SIZE, bold=True)
BG_COLOR = tuple(config['display'].get('background_color', [0, 0, 0]))

COLOR_HEAD = tuple(config['digital_rain']['head_color'])
COLOR_TAIL = tuple(config['digital_rain']['tail_color'])
RAIN_ALPHA = config['digital_rain'].get('alpha', 255)
SCREEN_FADE_ALPHA = config['digital_rain'].get('screen_fade_alpha', 15)

COLOR_TIME = tuple(config['time_digits']['color'])
TIME_FADE_ALPHA = config['time_digits'].get('fade_alpha', 3)
# NEW: Load the stacking limit
MAX_OVERLAP = config['time_digits'].get('max_overlap_stack', 3)

COLOR_LOCKED = tuple(config['fact_characters']['color'])
COLOR_CURSOR = tuple(config['fact_characters']['cursor_color'])
REVEAL_WINDOW = config['fact_characters'].get('reveal_window_size', 1)

FALL_SPEED = config['animation'].get('fall_speed', 1.0)
DROP_RESET_CHANCE = config['animation'].get('drop_reset_chance', 0.95)
APPLY_LENGTH_PENALTY = config['api'].get('apply_length_penalty', True)
PRIME_FACTOR_CHANCE = config['api'].get('prime_factor_chance', 0.25)

matrix_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*"

fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BG_COLOR)
fade_surface.set_alpha(SCREEN_FADE_ALPHA)

columns = WIDTH // FONT_SIZE
rows = HEIGHT // FONT_SIZE
drops = [float(random.randint(-50, 0)) for _ in range(columns)]

# --- NEW: DOUBLE-SIZED 6x10 ASCII FONT ---
ASCII_DIGITS = {
    '0': ["######", "######", "##  ##", "##  ##", "##  ##", "##  ##", "##  ##", "##  ##", "######", "######"],
    '1': ["    ##", "   ###", "  ####", "    ##", "    ##", "    ##", "    ##", "    ##", "######", "######"],
    '2': ["######", "######", "    ##", "    ##", "######", "######", "##    ", "##    ", "######", "######"],
    '3': ["######", "######", "    ##", "    ##", "######", "######", "    ##", "    ##", "######", "######"],
    '4': ["##  ##", "##  ##", "##  ##", "##  ##", "######", "######", "    ##", "    ##", "    ##", "    ##"],
    '5': ["######", "######", "##    ", "##    ", "######", "######", "    ##", "    ##", "######", "######"],
    '6': ["######", "######", "##    ", "##    ", "######", "######", "##  ##", "##  ##", "######", "######"],
    '7': ["######", "######", "    ##", "    ##", "   ## ", "   ## ", "  ##  ", "  ##  ", " ##   ", " ##   "],
    '8': ["######", "######", "##  ##", "##  ##", "######", "######", "##  ##", "##  ##", "######", "######"],
    '9': ["######", "######", "##  ##", "##  ##", "######", "######", "    ##", "    ##", "######", "######"],
    ':': ["  ", "  ", "##", "##", "  ", "  ", "##", "##", "  ", "  "]
}

# --- 3. Data Engine: NLP & Math Helpers ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13: return f"{n}th"
    return f"{n}" + ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]

def extract_index_context(number, seq):
    try:
        data_str = seq.get('data', '')
        if not data_str: return None
        data_list = [x.strip() for x in data_str.split(',')]
        number_str = str(number)
        if number_str in data_list:
            array_pos = data_list.index(number_str)
            offset_str = seq.get('offset', '1').split(',')[0]
            try: start_index = int(offset_str)
            except ValueError: start_index = 1
            return get_ordinal(array_pos + start_index)
    except Exception: pass
    return None

def naturalize_fact(number, description, ordinal_str=None):
    desc = description.strip().rstrip('.')
    lower_desc = desc.lower()

    exact_matches = {
        "primes": "a prime number", "composite numbers": "a composite number",
        "fibonacci numbers": "a Fibonacci number", "odd numbers": "an odd number",
        "even numbers": "an even number", "triangular numbers": "a triangular number",
        "perfect numbers": "a perfect number"
    }
    
    if lower_desc in exact_matches:
        desc = exact_matches[lower_desc]
    else:
        desc = re.sub(r'^([a-zA-Z\s\-]+) numbers$', r'a \1 number', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^(?:Numbers|Integers)(?:\s+[a-z])?\s+such that\s+', 'a number such that ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^(?:Numbers|Integers)\s+whose\s+', 'a number whose ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^(?:Numbers|Integers)\s+which\s+', 'a number which ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^(?:Numbers|Integers)\s+that\s+', 'a number that ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Products\s+of\s+', 'the product of ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Sums\s+of\s+', 'the sum of ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Squares\s+of\s+', 'the square of ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Cubes\s+of\s+', 'the cube of ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Multiples\s+of\s+', 'a multiple of ', desc, flags=re.IGNORECASE)
        desc = re.sub(r'^Powers\s+of\s+', 'a power of ', desc, flags=re.IGNORECASE)

        first_word = desc.split(' ')[0]
        proper_nouns = ['Euler', 'Fermat', 'Fibonacci', 'Catalan', 'Mersenne', 'Gaussian', 'Cullen', 'Bell']
        if first_word.istitle() and first_word not in proper_nouns and not desc.startswith(('a ', 'an ', 'the ')):
            desc = desc[0].lower() + desc[1:]

    if ordinal_str:
        if desc.startswith('a '): desc = f"the {ordinal_str} " + desc[2:]
        elif desc.startswith('an '): desc = f"the {ordinal_str} " + desc[3:]
        elif desc.startswith('the '): desc = f"the {ordinal_str} " + desc[4:]
        else: desc = f"the {ordinal_str} term in the sequence of {desc}"
    else:
        if not desc.startswith(('a ', 'an ', 'the ')):
            return f"{number} is characterized as: {desc}."

    return f"{number} is {desc}."

def get_prime_factors_string(number):
    if number < 2: return None
    factors = sympy.factorint(number)
    if len(factors) == 1 and list(factors.values())[0] == 1: return None
    parts = []
    for prime, exponent in factors.items():
        if exponent == 1: parts.append(str(prime))
        else: parts.append(f"{prime}^{exponent}")
    return " * ".join(parts)

# --- 4. Data Engine: OEIS Fetching ---
def get_fallback_fact(number):
    num = int(number)
    if num % 2 == 0: return f"{num} is an even number, divisible by 2."
    return f"{num} is an odd number. It cannot be divided evenly by 2."

def extract_best_sequence(results_list, apply_length_penalty):
    best_seq = None
    highest_score = -100
    for seq in results_list:
        score = 0
        keywords = seq.get('keyword', '').split(',')
        name = seq.get('name', '')

        if 'core' in keywords: score += 50
        if 'nice' in keywords: score += 30
        if 'easy' in keywords: score += 10
        if 'prime' in name.lower(): score += 60
        score += len(seq.get('comment', []))
        
        if apply_length_penalty:
            if len(name) > 80: score -= 20
            if len(name) > 120: score -= 50

        if score > highest_score:
            highest_score = score
            best_seq = seq
    return best_seq

def fetch_oeis_fact(number):
    url = f"https://oeis.org/search?q={number}&fmt=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results_list = [item for item in data if isinstance(item, dict) and 'number' in item and 'name' in item] if isinstance(data, list) else []
            if results_list:
                best_seq = extract_best_sequence(results_list, APPLY_LENGTH_PENALTY)
                if best_seq:
                    raw_description = best_seq['name']
                    ordinal = extract_index_context(number, best_seq)
                    return naturalize_fact(number, raw_description, ordinal)
    except requests.exceptions.RequestException: pass
    return get_fallback_fact(number)

# --- 5. Threading Logic ---
prefetched_facts = {}

def background_fetcher(time_str, number):
    fact = fetch_oeis_fact(number)
    if random.random() < PRIME_FACTOR_CHANCE:
        factors_str = get_prime_factors_string(number)
        if factors_str:
            fact += f" Its prime factorization is {factors_str}."
    prefetched_facts[time_str] = fact

# --- 6. Visual Grid Logic ---
def wrap_text_to_grid(text, max_cols):
    words = text.split(' ')
    lines, current_line = [], ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_cols:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line: lines.append(current_line.strip())
    return lines

def get_time_pixels(time_str):
    active_pixels = set()
    time_width = sum(len(ASCII_DIGITS[char][0]) + 1 for char in time_str) - 1
    time_start_col = (columns - time_width) // 2
    
    # Push the larger numbers slightly lower so they don't clip the top edge
    time_start_row = rows // 8  
    
    current_col = time_start_col
    for char in time_str:
        matrix = ASCII_DIGITS[char]
        for r, row_str in enumerate(matrix):
            for c, val in enumerate(row_str):
                if val == '#':
                    active_pixels.add((current_col + c, time_start_row + r))
        current_col += len(matrix[0]) + 1
    return active_pixels

def get_fact_targets(fact_text):
    ordered_targets = []
    if not fact_text: return ordered_targets
    
    max_fact_cols = columns - 8  
    fact_lines = wrap_text_to_grid(fact_text, max_fact_cols)
    
    # Because digits are now 10 rows tall, push the text further down
    current_row = (rows // 8) + 10 + 2  
    for line in fact_lines:
        start_col = (columns - len(line)) // 2
        for i, char in enumerate(line):
            ordered_targets.append(((start_col + i, current_row), char))
        current_row += 1 
    return ordered_targets

# --- 7. Main Game Loop ---
current_time_str = ""
time_pixel_targets = set()   
active_time_pixels = {}  
fact_targets = []  
revealed_flags = [] 

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    now = datetime.datetime.now()
    now_str = now.strftime("%H:%M")
    
    if now_str != current_time_str:
        current_time_str = now_str
        
        display_fact = prefetched_facts.get(now_str, f"Loading sequence for {now_str.replace(':', '')}...")
        
        time_pixel_targets = get_time_pixels(now_str)
        fact_targets = get_fact_targets(display_fact)
        revealed_flags = [False] * len(fact_targets)

        next_minute = now + timedelta(minutes=1)
        next_time_str = next_minute.strftime("%H:%M")
        next_number = int(next_minute.strftime("%H%M"))
        threading.Thread(target=background_fetcher, args=(next_time_str, next_number), daemon=True).start()

    screen.blit(fade_surface, (0, 0))

    # --- DRAW THE RAIN & CHECK TIME PIXEL COLLISIONS ---
    for i in range(len(drops)):
        drop_row_int = int(drops[i])
        x, y = i * FONT_SIZE, drop_row_int * FONT_SIZE
        
        head_char = random.choice(matrix_chars)
        head_surface = font.render(head_char, True, COLOR_HEAD)
        head_surface.set_alpha(RAIN_ALPHA)
        screen.blit(head_surface, (x, y))

        if drop_row_int > 0:
            tail_y_int = drop_row_int - 1
            tail_char = random.choice(matrix_chars)
            tail_surface = font.render(tail_char, True, COLOR_TAIL)
            tail_surface.set_alpha(RAIN_ALPHA)
            screen.blit(tail_surface, (x, y - FONT_SIZE))

        # Collision Check for Time Pixels
        current_drop_y = drops[i]
        previous_drop_y = current_drop_y - FALL_SPEED
        
        for target_row in range(rows):
            if (i, target_row) in time_pixel_targets:
                if previous_drop_y < target_row <= current_drop_y:
                    
                    if (i, target_row) not in active_time_pixels:
                        active_time_pixels[(i, target_row)] = []
                    
                    # Manage Stacking Limit
                    if len(active_time_pixels[(i, target_row)]) >= MAX_OVERLAP:
                        # Remove the oldest, most faded character to make room
                        active_time_pixels[(i, target_row)].pop(0)
                        
                    active_time_pixels[(i, target_row)].append({
                        'char': random.choice(matrix_chars),
                        'alpha': 255 
                    })

        drops[i] += FALL_SPEED

        if drop_row_int * FONT_SIZE > HEIGHT and random.random() > DROP_RESET_CHANCE:
            drops[i] = 0

    # --- DRAW THE OVERLAPPING TIME PIXELS ---
    keys_to_remove = []
    for (col, row), stack in active_time_pixels.items():
        if not stack:
            keys_to_remove.append((col, row))
            continue
            
        x, y = col * FONT_SIZE, row * FONT_SIZE
        max_alpha = max(data['alpha'] for data in stack)
        
        mask_surface = pygame.Surface((FONT_SIZE, FONT_SIZE))
        mask_surface.fill(BG_COLOR)
        mask_surface.set_alpha(int(max_alpha))
        screen.blit(mask_surface, (x, y))
        
        for data in stack:
            char_surface = font.render(data['char'], True, COLOR_TIME)
            char_surface.set_alpha(int(data['alpha']))
            screen.blit(char_surface, (x, y))
            data['alpha'] -= TIME_FADE_ALPHA
            
        active_time_pixels[(col, row)] = [data for data in stack if data['alpha'] > 0]
        
        if not active_time_pixels[(col, row)]:
            keys_to_remove.append((col, row))
            
    for k in keys_to_remove:
        if k in active_time_pixels:
            del active_time_pixels[k]

    # --- FACT COLLISION LOGIC ---
    unrevealed_indices = [i for i, is_revealed in enumerate(revealed_flags) if not is_revealed]
    
    if unrevealed_indices:
        active_window = unrevealed_indices[:REVEAL_WINDOW]
        for i in active_window:
            (target_col, target_row), _ = fact_targets[i]
            current_drop_y = drops[target_col]
            previous_drop_y = current_drop_y - FALL_SPEED

            if previous_drop_y < target_row <= current_drop_y:
                revealed_flags[i] = True

    # --- DRAW THE LOCKED FACT ---
    for i, ((col, row), char) in enumerate(fact_targets):
        if revealed_flags[i]:
            x, y = col * FONT_SIZE, row * FONT_SIZE
            pygame.draw.rect(screen, BG_COLOR, (x, y, FONT_SIZE, FONT_SIZE))
            screen.blit(font.render(char, True, COLOR_LOCKED), (x, y))

    # --- DRAW THE CURSOR ---
    if unrevealed_indices and (pygame.time.get_ticks() // 200) % 2 == 0:
        first_unrevealed = unrevealed_indices[0]
        (cursor_col, cursor_row), _ = fact_targets[first_unrevealed]
        screen.blit(font.render("█", True, COLOR_CURSOR), (cursor_col * FONT_SIZE, cursor_row * FONT_SIZE))

    pygame.display.flip()
    clock.tick(config['display']['target_fps'])

pygame.quit()