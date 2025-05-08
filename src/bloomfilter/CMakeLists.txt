cmake_minimum_required(VERSION 3.15...4.0)
project(bloomfilter LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------- third‑party (header‑only) deps -------------------------------
include(FetchContent)

FetchContent_Declare(
  xxhash
  GIT_REPOSITORY https://github.com/Cyan4973/xxHash.git
  GIT_TAG v0.8.3
  SOURCE_SUBDIR cmake_unofficial
)

FetchContent_MakeAvailable(xxhash)

find_package(pybind11 CONFIG REQUIRED)

# ------- build the extension -----------------------------------------
pybind11_add_module(_bloomfilter  # leading underscore → private C extension
    bindings.cpp
    bloom_filter.cpp
)

target_include_directories(_bloomfilter PRIVATE ${xxhash_SOURCE_DIR})
target_link_libraries     (_bloomfilter PRIVATE xxHash::xxhash)

# ensure the artifact is called "_bloomfilter.*.so/pyd/dylib"
set_target_properties(_bloomfilter PROPERTIES OUTPUT_NAME "_bloomfilter")

# ---------- copy the built library into the Python package ----------
install(TARGETS _bloomfilter
        LIBRARY DESTINATION bloomfilter          # Linux / macOS .so/.dylib
        RUNTIME DESTINATION bloomfilter          # Windows .pyd
        ARCHIVE DESTINATION bloomfilter)         # static lib, just in case

