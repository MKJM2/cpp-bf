"""
bloomfilter – fast C++17 Bloom filter

>>> from bloomfilter import BloomFilter
"""

from importlib import import_module

try:
    # the C++ extension is installed at the wheel root
    # from _bloomfilter import BloomFilter            # type: ignore
    BloomFilter = import_module("._bloomfilter", __package__).BloomFilter
except ModuleNotFoundError as exc:          # pragma: no cover
    raise ImportError(
        "The C extension failed to import. "
        "Did the build step run successfully?"
    ) from exc

__all__ = ["BloomFilter"]
__version__ = "0.1.0"
