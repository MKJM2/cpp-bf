#ifndef BLOOM_FILTER_H
#define BLOOM_FILTER_H

#include <vector>
#include <string>
#include <cstddef>
#include <cstdint>
#include <cmath>
#include <limits>
#include <algorithm> // For std::clamp

#include "xxhash.h"

class BloomFilter {
public:
    // Constructors with original signatures preserved
    BloomFilter(size_t estimated_num_items, double false_positive_rate);
    BloomFilter(size_t num_bits, size_t num_hashes);
    BloomFilter(size_t num_bits, size_t num_hashes, const std::vector<uint64_t>& bits_data);

    // Core methods
    void add(const std::string& item);
    void add(const char* data, size_t len);
    bool might_contain(const std::string& item) const;
    bool might_contain(const char* data, size_t len) const;

    // Accessors 
    size_t get_num_bits() const { return num_bits_; }
    size_t get_num_hashes() const { return num_hashes_; }
    const std::vector<uint64_t>& get_raw_bits_vector() const { return bits_; }

private:
    void calculate_optimal_params(size_t n, double p);
    void initialize_bits();

    static constexpr uint64_t SEED1 = 0x5F0D42B1A956789FULL;
    static constexpr uint64_t SEED2 = 0x9B1A75C3E0D6F2A7ULL;

    std::vector<uint64_t> bits_;
    size_t num_bits_;
    size_t num_hashes_;
};

#endif // BLOOM_FILTER_H
