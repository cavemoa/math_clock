import random
import requests
import re
import time

# --- 1. Ordinal Math Helpers ---
def get_ordinal(n):
    """Converts an integer to an ordinal string (e.g., 1 -> 1st, 2 -> 2nd)."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}" + ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]

def extract_index_context(number, seq):
    """Finds the Nth position of a number in the sequence using OEIS offset data."""
    try:
        data_str = seq.get('data', '')
        if not data_str:
            return None
        
        # Clean up the array and search for our number
        data_list = [x.strip() for x in data_str.split(',')]
        number_str = str(number)
        
        if number_str in data_list:
            array_pos = data_list.index(number_str)
            
            # Extract the mathematical starting index from the offset (defaults to 1)
            offset_str = seq.get('offset', '1').split(',')[0]
            try:
                start_index = int(offset_str)
            except ValueError:
                start_index = 1
                
            nth_term = array_pos + start_index
            return get_ordinal(nth_term)
    except Exception:
        pass
    return None

# --- 2. The Natural Language Parser ---
def naturalize_fact(number, description, ordinal_str=None):
    """Parses OEIS fragments and dynamically injects the ordinal context."""
    desc = description.strip().rstrip('.')
    lower_desc = desc.lower()

    # Exact matches for common short phrases
    exact_matches = {
        "primes": "a prime number",
        "composite numbers": "a composite number",
        "fibonacci numbers": "a Fibonacci number",
        "odd numbers": "an odd number",
        "even numbers": "an even number",
        "triangular numbers": "a triangular number",
        "perfect numbers": "a perfect number"
    }
    
    if lower_desc in exact_matches:
        desc = exact_matches[lower_desc]
    else:
        # Generic catch for named sequences (e.g., "Cullen numbers" -> "a Cullen number")
        desc = re.sub(r'^([a-zA-Z\s\-]+) numbers$', r'a \1 number', desc, flags=re.IGNORECASE)

        # Pattern replacements
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

        # Grammar cleanup for capitalization
        first_word = desc.split(' ')[0]
        proper_nouns = ['Euler', 'Fermat', 'Fibonacci', 'Catalan', 'Mersenne', 'Gaussian', 'Cullen', 'Bell']
        
        if first_word.istitle() and first_word not in proper_nouns and not desc.startswith(('a ', 'an ', 'the ')):
            desc = desc[0].lower() + desc[1:]

    # --- INJECT THE ORDINAL CONTEXT ---
    if ordinal_str:
        if desc.startswith('a '):
            desc = f"the {ordinal_str} " + desc[2:]
        elif desc.startswith('an '):
            desc = f"the {ordinal_str} " + desc[3:]
        elif desc.startswith('the '):
            desc = f"the {ordinal_str} " + desc[4:]
        else:
            # Fallback for weirdly structured sentences
            desc = f"the {ordinal_str} term in the sequence of {desc}"
    else:
        # If no ordinal was found, apply standard grammar fallback
        if not desc.startswith(('a ', 'an ', 'the ')):
            return f"{number} is characterized as: {desc}."

    return f"{number} is {desc}."

# --- 3. The Fetching & Scoring Engine ---
def extract_best_sequence(results_list):
    """Scores results and returns the entire winning sequence dictionary."""
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
        
        if len(name) > 80: score -= 20
        if len(name) > 120: score -= 50

        if score > highest_score:
            highest_score = score
            best_seq = seq

    return best_seq

def fetch_raw_oeis(number):
    url = f"https://oeis.org/search?q={number}&fmt=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results_list = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'number' in item and 'name' in item:
                        results_list.append(item)
            
            if results_list:
                return extract_best_sequence(results_list)
    except requests.exceptions.RequestException:
        pass
    return None

# --- 4. The Test Generator ---
def run_nlp_test(num_tests=10):
    print(f"--- Starting Contextual Parser Diagnostics ({num_tests} tests) ---\n")
    
    # Adding a known sequence to the test loop to guarantee we see the ordinal logic work
    test_cases = [610] # 610 is a known Fibonacci number
    
    for _ in range(num_tests - 1):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        test_cases.append(int(f"{hour:02d}{minute:02d}"))
        
    for i, search_number in enumerate(test_cases, 1):
        time_str = f"{search_number:04d}"[:2] + ":" + f"{search_number:04d}"[2:]
        print(f"Test {i}/{num_tests} | Time: {time_str} | Query: {search_number}")
        
        winning_seq = fetch_raw_oeis(search_number)
        
        if winning_seq:
            raw_description = winning_seq['name']
            
            # Extract the index if available
            ordinal = extract_index_context(search_number, winning_seq)
            
            # Pass both the description and the ordinal to the parser
            natural_text = naturalize_fact(search_number, raw_description, ordinal)
            
            print(f"  Raw:    {raw_description}")
            if ordinal:
                print(f"  Index:  Found ({ordinal})")
            print(f"  Parsed: {natural_text}\n")
        else:
            print("  Result: No notable OEIS sequence found.\n")
            
        if i < num_tests:
            time.sleep(1.5) 

if __name__ == "__main__":
    run_nlp_test(10)