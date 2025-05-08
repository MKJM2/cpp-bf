#include "bloom_filter.h"
#include <stdexcept>

// Constructor for optimal m and k
BloomFilter::BloomFilter(size_t estimated_num_items,
                         double false_positive_rate) {
  if (estimated_num_items == 0 || false_positive_rate <= 0.0 ||
      false_positive_rate >= 1.0) {
    throw std::invalid_argument(
        "Invalid parameters: n must be > 0, p must be between 0 and 1");
  }
  calculate_optimal_params(estimated_num_items, false_positive_rate);
  initialize_bits();
}

// Constructor for explicit m and k
BloomFilter::BloomFilter(size_t num_bits, size_t num_hashes)
    : num_bits_(num_bits), num_hashes_(num_hashes) {
  if (num_bits_ == 0 || num_hashes_ == 0) {
    throw std::invalid_argument(
        "Invalid parameters: bits and hashes must be > 0");
  }
  initialize_bits();
}

// Constructor for deserialization
BloomFilter::BloomFilter(size_t num_bits, size_t num_hashes,
                         const std::vector<uint64_t> &bits_data)
    : num_bits_(num_bits), num_hashes_(num_hashes), bits_(bits_data) {
  if (num_bits_ == 0 || num_hashes_ == 0 ||
      bits_data.size() != (num_bits_ + 63) / 64) {
    throw std::invalid_argument("Invalid data for BloomFilter restoration");
  }
}

void BloomFilter::calculate_optimal_params(size_t n, double p) {
  // Optimal bits: m = -n*ln(p)/(ln(2)²)
  static constexpr double LN2_SQUARED = 0.480453013918201; // ln(2)²
  double m_bits = -static_cast<double>(n) * std::log(p) / LN2_SQUARED;

  if (m_bits > static_cast<double>(std::numeric_limits<size_t>::max())) {
    throw std::overflow_error("Required bits exceeds size_t limit");
  }

  num_bits_ = static_cast<size_t>(std::ceil(m_bits));
  num_bits_ = std::max<size_t>(1, num_bits_);

  // Optimal hash functions: k = (m/n)*ln(2)
  static constexpr double LN2 = 0.693147180559945; // ln(2)
  double k_hashes = (static_cast<double>(num_bits_) / n) * LN2;

  num_hashes_ = static_cast<size_t>(std::ceil(k_hashes));
  num_hashes_ = std::clamp<size_t>(num_hashes_, 1,
                                   16); // Cap at 16 for practical efficiency
}

void BloomFilter::initialize_bits() {
  size_t num_blocks = (num_bits_ + 63) / 64;
  bits_.assign(num_blocks, 0);
}

void BloomFilter::add(const std::string &item) {
  add(item.data(), item.length());
}

void BloomFilter::add(const char *data, size_t len) {
  const uint64_t h1_initial = XXH64(data, len, SEED1);
  const uint64_t h2_initial = XXH64(data, len, SEED2);

  uint64_t current_probe_hash = h1_initial;
  uint64_t current_step_val = h2_initial;

  for (size_t i = 0; i < num_hashes_; ++i) {
    // Enhanced double hashing (see README.md)
    // 1. Update delta (current_step_val)
    current_step_val += i; // accumulates 'i' in each iteration

    const size_t bit_index = current_probe_hash % num_bits_;

    // Set the bit
    bits_[bit_index >> 6] |= (1ULL << (bit_index & 63));

    // Update probe hash for the next iteration
    current_probe_hash += current_step_val;
  }
}

bool BloomFilter::might_contain(const std::string &item) const {
  return might_contain(item.data(), item.length());
}

bool BloomFilter::might_contain(const char *data, size_t len) const {
  const uint64_t h1_initial = XXH64(data, len, SEED1);
  const uint64_t h2_initial = XXH64(data, len, SEED2);

  uint64_t current_probe_hash = h1_initial;
  uint64_t current_step_val = h2_initial; // This is the 'delta'

  for (size_t i = 0; i < num_hashes_; ++i) {
    // Enhanced double hashing: update delta (current_step_val)
    current_step_val += i;

    const size_t bit_index = current_probe_hash % num_bits_;
    const size_t block_index = bit_index >> 6; // / 64
    const size_t bit_offset = bit_index & 63;  // % 64

    if (!(bits_[block_index] & (1ULL << bit_offset))) {
      return false; // Early exit
    }

    // Update probe hash for the next iteration
    current_probe_hash += current_step_val;
  }
  return true;
}
