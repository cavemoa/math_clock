import random
import requests
import re
import time
import sympy

# --- 1. Math & Context Helpers ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
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
            try:
                start_index = int(offset_str)
            except ValueError:
                start_index = 1
            return get_ordinal(array_pos + start_index)
    except Exception:
        pass
    return None

def get_prime_factors_string(number):
    """Calculates prime factors and formats them (e.g., 12 -> 2^2 * 3)."""
    if number < 2:
        return None
        
    factors = sympy.factorint(number)
    
    # Skip formatting if the number is just prime itself
    if len(factors) == 1 and list(factors.values())[0] == 1:
        return None
        
    parts = []
    for prime, exponent in factors.items():
        if exponent == 1:
            parts.append(str(prime))
        else:
            parts.append(f"{prime}^{exponent}")
            
    return " * ".join(parts)

# --- 2. The Natural Language Parser ---
def naturalize_fact(number, description, ordinal_str=None):
    desc = description.strip().rstrip('.')
    lower_desc = desc.lower()

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

# --- 3. The Fetching Engine ---
def extract_best_sequence(results_list):
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
def run_nlp_test(num_tests=10, factor_chance=0.5):
    print(f"--- Starting Final Pipeline Diagnostics ({num_tests} tests) ---\n")
    print(f"Prime Factorization Chance set to: {factor_chance * 100}%\n")
    
    # 1200 is highly composite (12:00), 1147 is a known semi-prime
    test_cases = [1200, 1147] 
    
    for _ in range(num_tests - 2):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        test_cases.append(int(f"{hour:02d}{minute:02d}"))
        
    for i, search_number in enumerate(test_cases, 1):
        time_str = f"{search_number:04d}"[:2] + ":" + f"{search_number:04d}"[2:]
        print(f"Test {i}/{num_tests} | Time: {time_str} | Query: {search_number}")
        
        winning_seq = fetch_raw_oeis(search_number)
        
        if winning_seq:
            raw_description = winning_seq['name']
            ordinal = extract_index_context(search_number, winning_seq)
            
            # 1. Base Natural Text
            final_fact = naturalize_fact(search_number, raw_description, ordinal)
            
            print(f"  Raw OEIS: {raw_description}")
            if ordinal:
                print(f"  Ordinal:  Found ({ordinal})")
            
            # 2. Factorization Roll
            roll = random.random()
            if roll < factor_chance:
                factors_str = get_prime_factors_string(search_number)
                if factors_str:
                    print(f"  Factors:  Rolled successfully! ({factors_str})")
                    final_fact += f" Its prime factorization is {factors_str}."
                else:
                    print(f"  Factors:  Rolled successfully, but number is prime (Skipping)")
            else:
                 print(f"  Factors:  Did not roll (Failed chance)")

            print(f"  Final:    {final_fact}\n")
        else:
            print("  Result:   No notable OEIS sequence found.\n")
            
        if i < num_tests:
            time.sleep(1.5) 

if __name__ == "__main__":
    # You can change 0.5 to 1.0 if you want to force factors to append every single time
    run_nlp_test(num_tests=10, factor_chance=0.5)