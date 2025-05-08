"""
bloomfilter – fast C++17 Bloom filter

>>> from bloomfilter import BloomFilter
"""

from importlib import import_module

try:
    BloomFilter = import_module("._bloomfilter", __package__).BloomFilter
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ImportError(
        "The C extension failed to import. Did the build step run successfully?"
    ) from exc

__all__ = ["BloomFilter"]
__version__ = "0.1.1"
