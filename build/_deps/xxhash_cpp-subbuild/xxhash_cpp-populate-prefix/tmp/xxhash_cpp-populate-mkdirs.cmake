# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-src"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-build"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/tmp"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/src/xxhash_cpp-populate-stamp"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/src"
  "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/src/xxhash_cpp-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/src/xxhash_cpp-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/mkjm/Projects/cpp-bf/build/_deps/xxhash_cpp-subbuild/xxhash_cpp-populate-prefix/src/xxhash_cpp-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
