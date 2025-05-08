#ifndef BLOOM_FILTER_H
#define BLOOM_FILTER_H

#include <vector>
#include <string>
#include <cstddef> // For size_t
#include <cstdint> // For uint64_t
#include <cmath>   // For log, ceil, exp
#include <limits>  // For numeric_limits

#include "xxhash.h" // For XXH64

class BloomFilter {
public:
    // Constructor for optimal m and k based on n and p
    BloomFilter(size_t estimated_num_items, double false_positive_rate);

    // Constructor for explicit m and k
    BloomFilter(size_t num_bits, size_t num_hashes);

    // Constructor for deserialization/pickling
    BloomFilter(size_t num_bits, size_t num_hashes,
                const std::vector<uint64_t>& bits_data);

    void add(const std::string& item);
    void add(const char* data, size_t len);

    bool might_contain(const std::string& item) const;
    bool might_contain(const char* data, size_t len) const;

    size_t get_num_bits() const { return num_bits_; }
    size_t get_num_hashes() const { return num_hashes_; }

    // For pickling/serialization
    const std::vector<uint64_t>& get_raw_bits_vector() const {
        return bits_;
    }

private:
    void calculate_optimal_params(size_t n, double p);
    void initialize_bits();

    // Arbitrary fixed seeds for xxHash to generate two distinct base hashes.
    static constexpr uint64_t SEED1 = 0x5F0D42B1A956789FULL;
    static constexpr uint64_t SEED2 = 0x9B1A75C3E0D6F2A7ULL;

    std::vector<uint64_t> bits_;
    size_t num_bits_;   // m: total number of bits in the filter
    size_t num_hashes_; // k: number of hash functions
};

#endif // BLOOM_FILTER_H

