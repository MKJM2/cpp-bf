cmake_minimum_required(VERSION 3.15)
project(BloomFilterProject VERSION 0.1.0 LANGUAGES CXX)

# More verbose CMake logging for debugging FetchContent
set(CMAKE_MESSAGE_LOG_LEVEL STATUS) # Ensure we see status messages
set(CMAKE_MESSAGE_CONTEXT_SHOW TRUE) # Shows context (filename:lineno) for messages

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(FetchContent)

message(STATUS "[CMake] Declaring pybind11...")
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG v2.12.0
)
message(STATUS "[CMake] Making pybind11 available...")
FetchContent_MakeAvailable(pybind11) # Populates and calls add_subdirectory

# Verify pybind11 population
FetchContent_GetProperties(pybind11)
if(pybind11_POPULATED AND pybind11_SOURCE_DIR)
    message(STATUS "[CMake] pybind11 successfully populated. Source: ${pybind11_SOURCE_DIR}")
else()
    message(WARNING "[CMake] pybind11 FAILED to populate. POPULATED: ${pybind11_POPULATED}, SOURCE_DIR: ${pybind11_SOURCE_DIR}")
endif()


message(STATUS "[CMake] Declaring xxHash...")
FetchContent_Declare(
  xxhash_cpp 
  GIT_REPOSITORY https://github.com/Cyan4973/xxHash.git
  GIT_TAG v0.8.2
  SOURCE_SUBDIR cmake_unofficial
)

# Check xxHash properties BEFORE MakeAvailable
FetchContent_GetProperties(xxhash_cpp)
message(STATUS "[CMake] Before MakeAvailable(xxhash_cpp): xxhash_cpp_POPULATED=${xxhash_cpp_POPULATED}, xxhash_cpp_SOURCE_DIR='${xxhash_cpp_SOURCE_DIR}'")

message(STATUS "[CMake] Attempting FetchContent_MakeAvailable(xxhash_cpp)...")
FetchContent_MakeAvailable(xxhash_cpp) # This populates and calls add_subdirectory

# Check xxHash properties AFTER MakeAvailable
FetchContent_GetProperties(xxhash_cpp) # Re-check properties
message(STATUS "[CMake] After MakeAvailable(xxhash_cpp): xxhash_cpp_POPULATED=${xxhash_cpp_POPULATED}, xxhash_cpp_SOURCE_DIR='${xxhash_cpp_SOURCE_DIR}'")


# --- Primary Diagnostic for xxHash ---
if(NOT xxhash_cpp_SOURCE_DIR OR NOT xxhash_cpp_POPULATED)
    message(FATAL_ERROR "[CMake] CRITICAL: xxhash_cpp_SOURCE_DIR is not set or xxhash_cpp is not populated after FetchContent_MakeAvailable. "
                        "This means FetchContent failed to download or extract the xxHash sources. "
                        "Possible causes: "
                        "1. Network connectivity issue to github.com for the xxHash repository. "
                        "2. Git command failing during the clone/checkout of xxHash. "
                        "3. Incorrect GIT_REPOSITORY or GIT_TAG for xxHash. "
                        "4. Permissions problems in the build directory's _deps folder. "
                        "Please check your internet connection, git installation, and the CMake output above for any specific errors from git or FetchContent. "
                        "xxhash_cpp_POPULATED: ${xxhash_cpp_POPULATED}, xxhash_cpp_SOURCE_DIR: '${xxhash_cpp_SOURCE_DIR}'")
else()
    message(STATUS "[CMake] xxhash_cpp_SOURCE_DIR is: ${xxhash_cpp_SOURCE_DIR}")
    if(NOT EXISTS "${xxhash_cpp_SOURCE_DIR}/xxhash.h")
        message(FATAL_ERROR "[CMake] CRITICAL: xxhash.h not found at ${xxhash_cpp_SOURCE_DIR}/xxhash.h, even though xxhash_cpp_SOURCE_DIR is set. "
                            "This suggests the downloaded content is incomplete or incorrect.")
    else()
        message(STATUS "[CMake] SUCCESS: xxhash_cpp seems populated and xxhash.h found at ${xxhash_cpp_SOURCE_DIR}/xxhash.h.")
    endif()
endif()

# --- Python Module ---
pybind11_add_module(bloom_filter_module SHARED
    bindings.cpp
    bloom_filter.cpp
)

target_include_directories(bloom_filter_module PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR} # For bloom_filter.h
    ${xxhash_cpp_SOURCE_DIR}        # For xxhash.h (This will fail if xxhash_cpp_SOURCE_DIR is not set)
)

# Link against the xxHash static library.
target_link_libraries(bloom_filter_module PRIVATE xxHash::xxhash)

target_compile_definitions(bloom_filter_module PRIVATE
    VERSION_INFO=${PROJECT_VERSION}
)
