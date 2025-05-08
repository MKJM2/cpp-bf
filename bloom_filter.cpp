#include "bloom_filter.h"
#include <stdexcept> // For std::invalid_argument, std::overflow_error
#include <algorithm> // For std::max, std::min

// Constructor for optimal m and k
BloomFilter::BloomFilter(size_t estimated_num_items,
                         double false_positive_rate) {
    if (estimated_num_items == 0) {
        throw std::invalid_argument(
            "Estimated number of items cannot be zero.");
    }
    if (false_positive_rate <= 0.0 || false_positive_rate >= 1.0) {
        throw std::invalid_argument(
            "False positive rate must be between 0.0 and 1.0 (exclusive).");
    }
    calculate_optimal_params(estimated_num_items, false_positive_rate);
    initialize_bits();
}

// Constructor for explicit m and k
BloomFilter::BloomFilter(size_t num_bits, size_t num_hashes)
    : num_bits_(num_bits), num_hashes_(num_hashes) {
    if (num_bits_ == 0) {
        throw std::invalid_argument("Number of bits cannot be zero.");
    }
    if (num_hashes_ == 0) {
        throw std::invalid_argument(
            "Number of hash functions cannot be zero.");
    }
    initialize_bits();
}

// Constructor for deserialization/pickling
BloomFilter::BloomFilter(size_t num_bits, size_t num_hashes,
                         const std::vector<uint64_t>& bits_data)
    : num_bits_(num_bits), num_hashes_(num_hashes), bits_(bits_data) {
    if (num_bits_ == 0 || num_hashes_ == 0) {
        throw std::invalid_argument(
            "Invalid parameters for BloomFilter rehydration.");
    }
    size_t expected_blocks = (num_bits_ + 63) / 64;
    if (bits_.size() != expected_blocks) {
        throw std::runtime_error(
            "Mismatch in bit array size during BloomFilter rehydration.");
    }
}

void BloomFilter::calculate_optimal_params(size_t n, double p) {
    double n_double = static_cast<double>(n);
    double log_p = std::log(p);
    double log_2 = std::log(2.0);
    double log_2_sq = log_2 * log_2;

    double m_candidate = - (n_double * log_p) / log_2_sq;
    if (m_candidate > static_cast<double>(
            std::numeric_limits<size_t>::max())) {
        throw std::overflow_error(
            "Calculated number of bits exceeds size_t limits.");
    }
    num_bits_ = static_cast<size_t>(std::ceil(m_candidate));
    num_bits_ = std::max(static_cast<size_t>(1), num_bits_); // Ensure at least 1 bit

    double k_candidate = (static_cast<double>(num_bits_) / n_double) * log_2;
    num_hashes_ = static_cast<size_t>(std::ceil(k_candidate));
    num_hashes_ = std::max(static_cast<size_t>(1), num_hashes_); // Ensure at least 1 hash
    // Practical cap on k; too many hashes for a small m/n is inefficient
    num_hashes_ = std::min(num_hashes_, static_cast<size_t>(32)); 
}

void BloomFilter::initialize_bits() {
    size_t num_blocks = (num_bits_ + 63) / 64;
    // The following check is redundant as num_bits_ is guaranteed to be >= 1
    // by constructors, ensuring num_blocks will also be >= 1.
    // if (num_blocks == 0 && num_bits_ > 0) num_blocks = 1;
    
    try {
        bits_.assign(num_blocks, 0ULL);
    } catch (const std::bad_alloc& e) {
        throw std::runtime_error(
            "Failed to allocate memory for bit array: " + std::string(e.what()));
    }
}

void BloomFilter::add(const std::string& item) {
    add(item.data(), item.length());
}

void BloomFilter::add(const char* data, size_t len) {
    if (num_bits_ == 0) return; // Should not happen with constructor checks

    uint64_t hash1 = XXH64(data, len, SEED1);
    uint64_t hash2 = XXH64(data, len, SEED2);

    for (size_t i = 0; i < num_hashes_; ++i) {
        uint64_t combined_hash = hash1 + i * hash2;
        size_t bit_index = combined_hash % num_bits_;
        
        size_t block_index = bit_index / 64;
        size_t offset_in_block = bit_index % 64;
        bits_[block_index] |= (1ULL << offset_in_block);
    }
}

bool BloomFilter::might_contain(const std::string& item) const {
    return might_contain(item.data(), item.length());
}

bool BloomFilter::might_contain(const char* data, size_t len) const {
    if (num_bits_ == 0) return false; // Should not happen

    uint64_t hash1 = XXH64(data, len, SEED1);
    uint64_t hash2 = XXH64(data, len, SEED2);

    for (size_t i = 0; i < num_hashes_; ++i) {
        uint64_t combined_hash = hash1 + i * hash2;
        size_t bit_index = combined_hash % num_bits_;

        size_t block_index = bit_index / 64;
        size_t offset_in_block = bit_index % 64;
        if (!((bits_[block_index] >> offset_in_block) & 1ULL)) {
            return false;
        }
    }
    return true;
}

