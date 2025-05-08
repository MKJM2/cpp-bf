import time
import random
import sys
import os

from bloom_filter import BloomFilter

# --- Add build directory to Python path to find the C++ module ---
# Assumes benchmark.py is in the project root and the .so is in 'build/'
script_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(script_dir, 'build')
sys.path.insert(0, build_dir)

try:
    import bloom_filter_module
except ImportError as e:
    print(f"Error: Could not import 'bloom_filter_module'. {e}")
    print(f"Ensure it's built and available in: {build_dir}")
    print(f"Or that '{build_dir}' is in your PYTHONPATH.")
    print("If the .so file has a different name (e.g., due to Python version),")
    print("you might need to rename it or adjust the import logic.")
    sys.exit(1)

# --- Benchmark Parameters ---
NUM_ITEMS_TO_ADD = 100_000
NUM_ITEMS_TO_CHECK = 20_000 # Check a subset to keep benchmark faster

BF_CAPACITY = NUM_ITEMS_TO_ADD
BF_ERROR_RATE = 0.01 # Target 1% False Positive Rate

# --- Data Generation ---
print(f"Generating data for benchmark...")
print(f"  Target Capacity for Filters: {BF_CAPACITY}")
print(f"  Target Error Rate for Filters: {BF_ERROR_RATE}")
print(f"  Items to add: {NUM_ITEMS_TO_ADD}")
print(f"  Items to check (50% existing, 50% new): {NUM_ITEMS_TO_CHECK}")

items_to_add = [random.randint(0, NUM_ITEMS_TO_ADD * 10) for _ in range(NUM_ITEMS_TO_ADD)]

num_existing_to_check = NUM_ITEMS_TO_CHECK // 2
num_new_to_check = NUM_ITEMS_TO_CHECK - num_existing_to_check
items_to_check_existing = random.sample(items_to_add, min(num_existing_to_check, len(items_to_add)))
max_val_in_added = max(items_to_add) if items_to_add else NUM_ITEMS_TO_ADD * 10
items_to_check_non_existing = [
    random.randint(max_val_in_added + 1, max_val_in_added + 1 + NUM_ITEMS_TO_ADD * 10)
    for _ in range(num_new_to_check)
]
items_for_checking_phase = items_to_check_existing + items_to_check_non_existing
random.shuffle(items_for_checking_phase)
print("Data generation complete.")

# --- C++ Bloom Filter Benchmark ---
print(f"\n--- C++ Bloom Filter (bloom_filter_module) ---")
cpp_bf = None
cpp_bf_actual_size = "N/A"
cpp_bf_actual_hashes = "N/A"
try:
    print(f"Initializing C++ Bloom Filter: capacity={BF_CAPACITY}, error_rate={BF_ERROR_RATE}")
    cpp_bf = bloom_filter_module.BloomFilter(BF_CAPACITY, BF_ERROR_RATE)
    print(f"  C++ BF Initialized. Effective params (if exposed): Size={cpp_bf_actual_size} bits, Hashes={cpp_bf_actual_hashes}")

except AttributeError as e:
    print(f"Error: Class 'BloomFilter' not found or method missing in 'bloom_filter_module'. {e}")
    sys.exit(1)
except TypeError as e:
    print(f"Error: Could not initialize bloom_filter_module.BloomFilter with capacity={BF_CAPACITY}, error_rate={BF_ERROR_RATE}.")
    print(f"  TypeError: {e}")
    print("  This usually means the C++ BloomFilter constructor signature (and its bindings)")
    print("  does not match (capacity, error_rate) or a required method is missing.")
    sys.exit(1)

if not hasattr(cpp_bf, 'add'):
    print("Error: C++ BloomFilter object does not have an 'add' method.")
    sys.exit(1)

start_time = time.perf_counter()
for item in items_to_add:
    cpp_bf.add(str(item))
duration_add_cpp = time.perf_counter() - start_time
print(f"Time to add {NUM_ITEMS_TO_ADD} items (C++): {duration_add_cpp:.6f} seconds")

contains_method_name_cpp = ''
if hasattr(cpp_bf, 'contains'): contains_method_name_cpp = 'contains'
elif hasattr(cpp_bf, '__contains__'): contains_method_name_cpp = '__contains__'
else:
    print("Error: C++ BloomFilter object does not have a 'contains' or '__contains__' method.")
    sys.exit(1)

cpp_check_func = getattr(cpp_bf, contains_method_name_cpp)

false_positives_cpp = 0
start_time = time.perf_counter()
for item in items_for_checking_phase:
    result = cpp_check_func(str(item))
    if result and item in items_to_check_non_existing:
        false_positives_cpp += 1
duration_check_cpp = time.perf_counter() - start_time
print(f"Time to check {len(items_for_checking_phase)} items (C++): {duration_check_cpp:.6f} seconds")

fp_rate_cpp = (false_positives_cpp / num_new_to_check) if num_new_to_check > 0 else 0.0
print(f"False Positive Rate (C++): {fp_rate_cpp:.6f} ({false_positives_cpp}/{num_new_to_check})")

# --- Python Bloom Filter (from bloom_filter.py) Benchmark ---
print(f"\n--- Python Bloom Filter (bloom_filter.py) ---")
print(f"Initializing Python Bloom Filter: capacity={{BF_CAPACITY}}, error_rate={{BF_ERROR_RATE}}")
# KeyType is str because we are adding stringified integers
py_bf = BloomFilter[str](capacity=BF_CAPACITY, error_rate=BF_ERROR_RATE)
print(f"  Python BF Initialized. Effective params: Size={{py_bf.size}} bits, Hashes={{py_bf.num_hashes}}")

start_time = time.perf_counter()
for item in items_to_add:
    py_bf.add(str(item)) # Add as string
duration_add_py = time.perf_counter() - start_time
print(f"Time to add {NUM_ITEMS_TO_ADD} items (Python): {duration_add_py:.6f} seconds")

false_positives_py = 0
start_time = time.perf_counter()
for item in items_for_checking_phase:
    result = str(item) in py_bf # Check as string
    if result and item in items_to_check_non_existing:
        false_positives_py += 1
duration_check_py = time.perf_counter() - start_time
print(f"Time to check {len(items_for_checking_phase)} items (Python): {duration_check_py:.6f} seconds")

fp_rate_py = (false_positives_py / num_new_to_check) if num_new_to_check > 0 else 0.0
print(f"False Positive Rate (Python): {fp_rate_py:.6f} ({false_positives_py}/{num_new_to_check})")

# --- Summary ---
print(f"\n--- Summary ---")
print(f"Target Capacity for Filters: {BF_CAPACITY}")
print(f"Target Error Rate for Filters: {BF_ERROR_RATE}")
print(f"Items added to each filter: {NUM_ITEMS_TO_ADD}")
print(f"Items checked for each filter: {len(items_for_checking_phase)}")

print(f"\nC++ Bloom Filter Effective Parameters (if exposed by bindings):")
print(f"  Calculated Size: {cpp_bf_actual_size} bits")
print(f"  Calculated Hash Functions: {cpp_bf_actual_hashes}")

print(f"\nPython Bloom Filter (bloom_filter.py) Effective Parameters:")
print(f"  Calculated Size: {py_bf.size} bits") # Accessing .size directly
print(f"  Calculated Hash Functions: {py_bf.num_hashes}") # Accessing .num_hashes directly

print(f"\nAddition Times:")
print(f"  C++:    {duration_add_cpp:.6f} seconds")
print(f"  Python: {duration_add_py:.6f} seconds")
if duration_add_py > 0 and duration_add_cpp > 0:
    print(f"  C++ was {duration_add_py/duration_add_cpp:.2f}x faster at adding items.")
elif duration_add_cpp == 0 and duration_add_py > 0:
    print("  C++ addition was instantaneous or too fast to measure accurately compared to Python.")

print(f"\nCheck Times (for 'contains'):")
print(f"  C++:    {duration_check_cpp:.6f} seconds")
print(f"  Python: {duration_check_py:.6f} seconds")
if duration_check_py > 0 and duration_check_cpp > 0:
    print(f"  C++ was {duration_check_py/duration_check_cpp:.2f}x faster at checking items.")
elif duration_check_cpp == 0 and duration_check_py > 0:
     print("  C++ checking was instantaneous or too fast to measure accurately compared to Python.")

print(f"\nFalse Positive Rates (on {num_new_to_check} non-existing items):")
print(f"  C++:    {fp_rate_cpp:.6f}")
print(f"  Python: {fp_rate_py:.6f}")

print(f"\nTo run this benchmark:")
print(f"1. Ensure your C++ Bloom Filter is compiled (e.g., run 'cmake --build build' in project root).")
print(f"2. Ensure 'bloom_filter.py' is in the same directory as this script.")
print(f"3. Run this script: python benchmark.py")
print(f"4. IMPORTANT: If your C++ BloomFilter class in 'bloom_filter_module' has a different constructor,")
print(f"   or does not expose methods/properties like 'size_in_bits' or 'num_hashes' as attempted,")
print(f"   you may need to adjust its instantiation or how effective parameters are retrieved (around line ~50).") 