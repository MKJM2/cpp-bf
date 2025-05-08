import time
import random
import sys
import os

from bloom_filter import BloomFilter

# --- Attempt to import rbloom for comparison ---
try:
    from rbloom import Bloom as RBloom # Alias to avoid name clash
    RBLOOM_AVAILABLE = True
except ImportError:
    RBLOOM_AVAILABLE = False
    print("INFO: 'rbloom' library not found. Skipping rbloom benchmark. To include it, run: pip install rbloom")

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

# Initialize result variables for all filters to handle conditional execution
duration_add_cpp, duration_check_cpp, fp_rate_cpp = 0.0, 0.0, 0.0
duration_add_py, duration_check_py, fp_rate_py = 0.0, 0.0, 0.0
duration_add_rbloom, duration_check_rbloom, fp_rate_rbloom = 0.0, 0.0, 0.0
cpp_bf_actual_size, cpp_bf_actual_hashes = "N/A", "N/A"
py_bf_actual_size, py_bf_actual_hashes = "N/A", "N/A"
rbloom_bf_actual_size, rbloom_bf_actual_hashes = "N/A", "N/A"

# --- C++ Bloom Filter Benchmark ---
print(f"\n--- C++ Bloom Filter (bloom_filter_module) ---")
cpp_bf = None
try:
    print(f"Initializing C++ Bloom Filter: capacity={BF_CAPACITY}, error_rate={BF_ERROR_RATE}")
    cpp_bf = bloom_filter_module.BloomFilter(BF_CAPACITY, BF_ERROR_RATE)
    if hasattr(cpp_bf, 'num_bits'): cpp_bf_actual_size = cpp_bf.num_bits
    if hasattr(cpp_bf, 'num_hashes'): cpp_bf_actual_hashes = cpp_bf.num_hashes
    print(f"  C++ BF Initialized. Effective params (if exposed): Size={cpp_bf_actual_size} bits, Hashes={cpp_bf_actual_hashes}")
except Exception as e:
    print(f"Error during C++ Bloom Filter setup: {e}")
    cpp_bf = None # Ensure it's None if setup fails

if cpp_bf:
    start_time = time.perf_counter()
    for item in items_to_add:
        cpp_bf.add(str(item))
    duration_add_cpp = time.perf_counter() - start_time
    print(f"Time to add {NUM_ITEMS_TO_ADD} items (C++): {duration_add_cpp:.6f} seconds")

    false_positives_cpp = 0
    start_time = time.perf_counter()
    for item in items_for_checking_phase:
        if str(item) in cpp_bf:
            if item in items_to_check_non_existing:
                false_positives_cpp += 1
    duration_check_cpp = time.perf_counter() - start_time
    print(f"Time to check {len(items_for_checking_phase)} items (C++): {duration_check_cpp:.6f} seconds")
    fp_rate_cpp = (false_positives_cpp / num_new_to_check) if num_new_to_check > 0 else 0.0
    print(f"False Positive Rate (C++): {fp_rate_cpp:.6f} ({false_positives_cpp}/{num_new_to_check})")
else:
    print("Skipping C++ Bloom Filter benchmark due to initialization error.")

# --- Python Bloom Filter (from bloom_filter.py) Benchmark ---
print(f"\n--- Python Bloom Filter (bloom_filter.py) ---")
py_bf = None
try:
    print(f"Initializing Python Bloom Filter: capacity={BF_CAPACITY}, error_rate={BF_ERROR_RATE}")
    py_bf = BloomFilter[str](capacity=BF_CAPACITY, error_rate=BF_ERROR_RATE)
    py_bf_actual_size = py_bf.size
    py_bf_actual_hashes = py_bf.num_hashes
    print(f"  Python BF Initialized. Effective params: Size={py_bf_actual_size} bits, Hashes={py_bf_actual_hashes}")
except Exception as e:
    print(f"Error during Python (bloom_filter.py) Bloom Filter setup: {e}")
    py_bf = None

if py_bf is not None:
    start_time = time.perf_counter()
    for item in items_to_add:
        py_bf.add(str(item))
    duration_add_py = time.perf_counter() - start_time
    print(f"Time to add {NUM_ITEMS_TO_ADD} items (Python): {duration_add_py:.6f} seconds")

    false_positives_py = 0
    start_time = time.perf_counter()
    for item in items_for_checking_phase:
        if str(item) in py_bf:
            if item in items_to_check_non_existing:
                false_positives_py += 1
    duration_check_py = time.perf_counter() - start_time
    print(f"Time to check {len(items_for_checking_phase)} items (Python): {duration_check_py:.6f} seconds")
    fp_rate_py = (false_positives_py / num_new_to_check) if num_new_to_check > 0 else 0.0
    print(f"False Positive Rate (Python): {fp_rate_py:.6f} ({false_positives_py}/{num_new_to_check})")
else:
    print("Skipping Python (bloom_filter.py) Bloom Filter benchmark due to initialization error.")

# --- rbloom Library Benchmark ---
if RBLOOM_AVAILABLE:
    print(f"\n--- rbloom Library Filter ---")
    rbloom_bf = None
    try:
        print(f"Initializing rbloom.Bloom Filter: capacity={BF_CAPACITY}, error_rate={BF_ERROR_RATE}")
        rbloom_bf = RBloom(expected_items=BF_CAPACITY, false_positive_rate=BF_ERROR_RATE)
        # rbloom does not directly expose num_bits/num_hashes in a simple way like the others
        # It uses a more complex internal structure (layers of sub-filters)
        # We can estimate or try to infer, but for now, we'll mark as N/A
        rbloom_bf_actual_size = "N/A (see rbloom internals)"
        rbloom_bf_actual_hashes = "N/A (see rbloom internals)"
        print(f"  rbloom BF Initialized.")
    except Exception as e:
        print(f"Error during rbloom.Bloom Filter setup: {e}")
        rbloom_bf = None

    if rbloom_bf is not None:
        start_time = time.perf_counter()
        for item in items_to_add:
            rbloom_bf.add(str(item)) # rbloom also expects string or bytes
        duration_add_rbloom = time.perf_counter() - start_time
        print(f"Time to add {NUM_ITEMS_TO_ADD} items (rbloom): {duration_add_rbloom:.6f} seconds")

        false_positives_rbloom = 0
        start_time = time.perf_counter()
        for item in items_for_checking_phase:
            if str(item) in rbloom_bf:
                if item in items_to_check_non_existing:
                    false_positives_rbloom += 1
        duration_check_rbloom = time.perf_counter() - start_time
        print(f"Time to check {len(items_for_checking_phase)} items (rbloom): {duration_check_rbloom:.6f} seconds")
        fp_rate_rbloom = (false_positives_rbloom / num_new_to_check) if num_new_to_check > 0 else 0.0
        print(f"False Positive Rate (rbloom): {fp_rate_rbloom:.6f} ({false_positives_rbloom}/{num_new_to_check})")
    else:
        print("Skipping rbloom benchmark due to initialization error or library not available.")

# --- Summary ---
print(f"\n--- Summary ---")
print(f"Target Capacity for Filters: {BF_CAPACITY}")
print(f"Target Error Rate for Filters: {BF_ERROR_RATE}")
print(f"Items added to each filter: {NUM_ITEMS_TO_ADD}")
print(f"Items checked (50% existing, 50% new): {len(items_for_checking_phase)}")

print(f"\nC++ Bloom Filter (bloom_filter_module):")
print(f"  Effective Size: {cpp_bf_actual_size} bits, Hashes: {cpp_bf_actual_hashes}")
print(f"  Add time: {duration_add_cpp:.6f}s, Check time: {duration_check_cpp:.6f}s, FPR: {fp_rate_cpp:.6f}")

print(f"\nPython Bloom Filter (bloom_filter.py):")
print(f"  Effective Size: {py_bf_actual_size} bits, Hashes: {py_bf_actual_hashes}")
print(f"  Add time: {duration_add_py:.6f}s, Check time: {duration_check_py:.6f}s, FPR: {fp_rate_py:.6f}")

if RBLOOM_AVAILABLE:
    print(f"\nrbloom Library Filter:")
    print(f"  Effective Size: {rbloom_bf_actual_size}, Hashes: {rbloom_bf_actual_hashes}")
    print(f"  Add time: {duration_add_rbloom:.6f}s, Check time: {duration_check_rbloom:.6f}s, FPR: {fp_rate_rbloom:.6f}")

print(f"\nTo run this benchmark:")
print(f"1. Ensure C++ Bloom Filter is compiled ('cmake --build build').")
print(f"2. Ensure 'bloom_filter.py' is present.")
print(f"3. For rbloom comparison, install it: pip install rbloom")
print(f"4. Run script: python benchmark.py")
print(f"5. Note: If C++ BloomFilter constructor/properties differ, adjust script around line ~60.") 