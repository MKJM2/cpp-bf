#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include "bloom_filter.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PYBIND11_MODULE(_bloomfilter, m) {
    m.doc() = "Fast Bloom filter implementation with configurable false positive rate";

    py::class_<BloomFilter> bloom(m, "BloomFilter", "Space-efficient probabilistic set membership testing");

    bloom
        .def(py::init<size_t, double>(), 
             py::arg("estimated_num_items"), py::arg("false_positive_rate"),
             "Create filter with optimal parameters based on item count and error rate")
        .def(py::init<size_t, size_t>(),
             py::arg("num_bits"), py::arg("num_hashes"),
             "Create filter with explicit bit count and hash function count")
        .def("add", py::overload_cast<const std::string&>(&BloomFilter::add), 
             py::arg("item"), "Add string item to filter")
        .def("add", [](BloomFilter &bf, py::bytes item) {
             std::string_view view = py::cast<std::string_view>(item);
             bf.add(view.data(), view.size());
         }, py::arg("item"), "Add bytes to filter")
        .def("might_contain", py::overload_cast<const std::string&>(&BloomFilter::might_contain, py::const_),
             py::arg("item"), "Test if string might be in filter")
        .def("might_contain", [](const BloomFilter &bf, py::bytes item) {
             std::string_view view = py::cast<std::string_view>(item);
             return bf.might_contain(view.data(), view.size());
         }, py::arg("item"), "Test if bytes might be in filter")
        .def("__contains__", [](const BloomFilter &bf, py::object item) {
             if (py::isinstance<py::str>(item)) {
                 return bf.might_contain(py::cast<std::string>(item));
             } else if (py::isinstance<py::bytes>(item)) {
                 std::string_view view = py::cast<std::string_view>(item);
                 return bf.might_contain(view.data(), view.size());
             }
             throw py::type_error("Only str or bytes supported");
         }, "Test membership with 'item in filter' syntax")
        .def_property_readonly("num_bits", &BloomFilter::get_num_bits)
        .def_property_readonly("num_hashes", &BloomFilter::get_num_hashes)
        .def(py::pickle(
            [](const BloomFilter &bf) {
                return py::make_tuple(bf.get_num_bits(), bf.get_num_hashes(), bf.get_raw_bits_vector());
            },
            [](py::tuple t) {
                if (t.size() != 3) throw std::runtime_error("Invalid pickle state");
                return BloomFilter(t[0].cast<size_t>(), t[1].cast<size_t>(), t[2].cast<std::vector<uint64_t>>());
            }
        ));

    #ifdef VERSION_INFO
        m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
    #else
        m.attr("__version__") = "dev";
    #endif
}
