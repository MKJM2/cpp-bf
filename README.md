# BloomFilter

A minimal, relatively high–performance Bloom filter implemented in C++17 and exposed to Python through **pybind11**.  
Built for latency experiments for our COMPSCI 2241 final paper w/ Aghyad Deeb.

---

## Installation

### Pre‑built wheel (if available)

```bash
python -m pip install bloomfilter          # binary wheel for your platform
````

### From source

Requirements:

* Python ≥ 3.8
* CMake ≥ 3.15
* A C++17 compiler (GCC ≥ 7, Clang ≥ 6, MSVC ≥ 19.14)

```bash
# clone repository
git clone https://github.com/your‑org/bloomfilter.git
cd bloomfilter

# build and install editable copy
python -m pip install -e .
```

The build step is handled automatically by **scikit‑build‑core**.

---

## Quick start

```python
from bloomfilter import BloomFilter

# capacity‑style constructor: choose error rate, parameters computed automatically
bf = BloomFilter(estimated_num_items=1000, false_positive_rate=0.01)

bf.add("hello")
print("hello" in bf)   # True
print("world" in bf)   # Usually False

print(bf.num_bits, "bits")      # internal size
print(bf.num_hashes, "hashes")  # hash functions
```

### Alternate constructor (explicit parameters)

```python
bf = BloomFilter(num_bits=8192, num_hashes=6)
```

### Persistence

```python
import pickle, pathlib

path = pathlib.Path("filter.pkl")
pickle.dump(bf, path.open("wb"))      # save
bf2 = pickle.load(path.open("rb"))    # restore
```

---

## API reference

| Method / property    | Purpose                                                         |
| -------------------- | --------------------------------------------------------------- |
| `BloomFilter(n, p)`  | Create with expected *n* items and false‑positive rate *p*.     |
| `BloomFilter(m, k)`  | Create with explicit bit array size *m* and *k* hash functions. |
| `add(item)`          | Insert a `str` or `bytes`.                                      |
| `item in bf`         | Membership test (`bool`).                                       |
| `num_bits` `→ int`   | Bit array length (*m*).                                         |
| `num_hashes` `→ int` | Number of hash functions (*k*).                                 |

Objects are fully pickleable; the byte array is stored compactly.

---

## On the Kirsch-Mitzenmacher Optimization

To efficiently generate multiple hash values for an item, this Bloom filter initially used a common technique known as the Kirsch-Mitzenmacher optimization. This method computes \(k\) hash functions using two base hash values, \(h_1\) and \(h_2\), as \(g_i(x) = (h_1(x) + i \cdot h_2(x)) \pmod m\), where \(m\) is the number of bits in the filter. This reduces the number of full hash computations needed.

## On Peter Dillinger's Enhanced Double Hashing

This implementation incorporates Peter Dillinger's "enhanced double hashing" from RocksDB. The step value is modified in each iteration (e.g., `delta += j`, where `j` is the iteration counter) before being added to the current hash. This adjustment empirically improves probe distribution and robustness (leading in experimentation to more reliable false positive rates).

---

## License

Released under the MIT License – see `LICENSE` for details.

