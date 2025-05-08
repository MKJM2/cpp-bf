#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include "bloom_filter.h"

// Helper macros for version stringification
#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PYBIND11_MODULE(bloom_filter_module, m) {
    m.doc() = R"pbdoc(
        Python bindings for a C++ Bloom filter implementation.
        Provides a fast Bloom filter for checking set membership
        with a configurable false positive rate.
    )pbdoc";

    py::class_<BloomFilter> bloom_filter_class(m, "BloomFilter", R"pbdoc(
        A Bloom filter is a space-efficient probabilistic data structure used
        to test whether an element is a member of a set. False positive
        matches are possible, but false negatives are not.
    )pbdoc");

    bloom_filter_class
        .def(py::init<size_t, double>(),
             py::arg("estimated_num_items"), py::arg("false_positive_rate"),
             R"pbdoc(
                Constructs a Bloom filter, calculating optimal size (m) and
                number of hash functions (k) based on the estimated number of
                items and desired false positive probability.

                Args:
                    estimated_num_items (int): Estimated number of items.
                    false_positive_rate (float): Desired false positive rate
                                                 (e.g., 0.01 for 1%).
             )pbdoc")
        .def(py::init<size_t, size_t>(),
             py::arg("num_bits"), py::arg("num_hashes"),
             R"pbdoc(
                Constructs a Bloom filter with a specific number of bits (m)
                and number of hash functions (k).

                Args:
                    num_bits (int): Total bits in the filter's bit array.
                    num_hashes (int): Number of hash functions.
             )pbdoc")
        .def("add", [](BloomFilter &bf, const std::string &item) {
                bf.add(item);
             }, py::arg("item"), "Adds a string item to the filter.")
        .def("add", [](BloomFilter &bf, py::bytes item_bytes) {
                py::buffer_info info(py::buffer(item_bytes).request());
                bf.add(static_cast<const char*>(info.ptr), info.size);
             }, py::arg("item"), "Adds a bytes item to the filter.")
        .def("might_contain", [](const BloomFilter &bf, const std::string &item) {
                return bf.might_contain(item);
             }, py::arg("item"), "Checks if a string item might be in the filter.")
        .def("might_contain", [](const BloomFilter &bf, py::bytes item_bytes) {
                py::buffer_info info(py::buffer(item_bytes).request());
                return bf.might_contain(static_cast<const char*>(info.ptr), info.size);
             }, py::arg("item"), "Checks if a bytes item might be in the filter.")
        .def("__contains__", [](const BloomFilter &bf, const std::string &item) {
                return bf.might_contain(item);
             }, py::is_operator(), "Implements `item in filter` for strings.")
        .def("__contains__", [](const BloomFilter &bf, py::bytes item_bytes) {
                py::buffer_info info(py::buffer(item_bytes).request());
                return bf.might_contain(static_cast<const char*>(info.ptr), info.size);
             }, py::is_operator(), "Implements `item in filter` for bytes.")
        .def_property_readonly("num_bits", &BloomFilter::get_num_bits,
                               "Number of bits in the filter (m).")
        .def_property_readonly("num_hashes", &BloomFilter::get_num_hashes,
                               "Number of hash functions used (k).")
        .def(py::pickle(
            [](const BloomFilter &bf) { // __getstate__
                return py::make_tuple(bf.get_num_bits(),
                                      bf.get_num_hashes(),
                                      bf.get_raw_bits_vector());
            },
            [](py::tuple t) { // __setstate__
                if (t.size() != 3) {
                    throw std::runtime_error("Invalid state for unpickling BloomFilter");
                }
                // Use the special constructor for rehydration
                return BloomFilter(t[0].cast<size_t>(),
                                   t[1].cast<size_t>(),
                                   t[2].cast<std::vector<uint64_t>>());
            }
        ));

    #ifdef VERSION_INFO
        m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
    #else
        m.attr("__version__") = "dev";
    #endif
}

