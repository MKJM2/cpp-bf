#!/usr/bin/env python3
import argparse
import math
import xxhash  # type: ignore[import-not-found]
import struct
from bitarray import bitarray  # type: ignore[import-not-found]
from typing import (
    Callable,
    Final,
    Generic,
    Iterable,
    List,
    Tuple,
    TypeVar,
    Optional,
)


# --- Type variables and aliases ---
KeyType = TypeVar("KeyType")
# Define a specific type for the serializer function
Serializer = Callable[[KeyType], bytes]

# --- Constants ---
XXH_SEED1: Final[int] = 0
XXH_SEED2: Final[int] = 6917


# --- Generic Bloom Filter ---
class BloomFilter(Generic[KeyType]):
    """
    A generic, high-performance Bloom filter optimized for speed.

    Requires the user to provide a `serializer` function during initialization
    to convert items of `KeyType` into bytes before hashing. The core filter
    logic operates exclusively on these bytes.

    Features:
    - Generic over KeyType.
    - Requires user-provided serialization function (KeyType -> bytes).
    - xxhash (xxh64) for fast hashing.
    - bitarray package for C-optimized bit manipulation.
    - Kirsch-Mitzenmacher optimization (double hashing).
    - No runtime type checks in hot paths.
    """

    __slots__ = (
        "capacity",
        "error_rate",
        "serializer",
        "size",
        "num_hashes",
        "bit_array",
        "num_items",
        "_hasher1_intdigest",
        "_hasher2_intdigest",
    )

    # Type alias for the internal hash function signature (bytes -> int)
    _BytesHasher = Callable[[bytes], int]

    def __init__(
        self,
        capacity: int,
        error_rate: float,
        serializer: Optional[Serializer[KeyType]] = None,
    ):
        """
        Initializes the generic Bloom filter.

        Args:
            capacity: The expected number of items to be stored (n).
            error_rate: The desired false positive probability (p), e.g., 0.001.
            serializer: An optional function that takes an item of KeyType and returns bytes.
                        If None, built-in support for int, float, str, bytes is used.

        Raises:
            ValueError: If capacity is non-positive or error_rate is not in (0, 1).
            TypeError: If serializer is provided but not callable, or if an
                       unsupported key type is encountered at insertion.
        """
        if not capacity > 0:
            raise ValueError("Capacity must be positive")
        if not 0 < error_rate < 1:
            raise ValueError("Error rate must be between 0 and 1")

        if serializer is None:
            serializer = self._default_serializer
        self.serializer: Final[Serializer[KeyType]] = serializer

        self.capacity: Final[int] = capacity
        self.error_rate: Final[float] = error_rate

        size, num_hashes = self._calculate_optimal_params(capacity, error_rate)
        self.size: Final[int] = size
        self.num_hashes: Final[int] = num_hashes

        # Initialize bit array using the C-backed bitarray
        self.bit_array: bitarray = bitarray(self.size)
        self.bit_array.setall(0)

        self.num_items: int = 0

        # Initialize hashers using xxh64_intdigest for direct integer output
        # These always operate on bytes internally.
        self._hasher1_intdigest: BloomFilter._BytesHasher = (
            lambda b: xxhash.xxh64_intdigest(b, seed=XXH_SEED1)
        )
        self._hasher2_intdigest: BloomFilter._BytesHasher = (
            lambda b: xxhash.xxh64_intdigest(b, seed=XXH_SEED2)
        )

    @staticmethod
    def _default_serializer(item: KeyType) -> bytes:
        """
        Default serialization for int, float, str, bytes.
        Raises TypeError on other types.
        """
        if isinstance(item, (bytes, bytearray)):
            return bytes(item)  # no-op
        if isinstance(item, str):
            return item.encode("utf-8")
        if isinstance(item, float):  # float: 8-byte IEEE-754 big-endian
            return struct.pack(">d", item)
        if isinstance(item, int):  # int: two's-complement 64-bit little-endian
            return item.to_bytes(8, byteorder="little", signed=True)
        raise TypeError(
            f"No default serializer for type {type(item).__name__}; "
            "please provide a custom serializer"
        )

    @staticmethod
    def _calculate_optimal_params(capacity: int, error_rate: float) -> Tuple[int, int]:
        """Calculates optimal size (m) and hash count (k)."""
        # m = - (n * ln(p)) / (ln(2)^2)
        m_float: float = -(capacity * math.log(error_rate)) / (math.log(2) ** 2)
        size: int = max(1, int(math.ceil(m_float)))  # Ensure size is at least 1

        # k = (m / n) * ln(2)
        # Handle potential division by zero if capacity is somehow <= 0 despite check
        k_float: float = (size / capacity) * math.log(2) if capacity > 0 else 1.0
        num_hashes: int = max(1, int(math.ceil(k_float)))  # Ensure at least 1 hash

        return size, num_hashes

    def _get_indices(self, item_bytes: bytes) -> List[int]:
        """
        Generates k indices using enhanced double hashing with xxhash on bytes.

        See https://github.com/facebook/rocksdb/issues/4120,
        http://peterd.org/pcd-diss.pdf as well as Kirsch-Mitzenmacher
        optimization for double hashing.

        Args:
            item_bytes: The serialized item in bytes.
        Returns:
            A list of k indices for the bit array.
        """
        h1: int = self._hasher1_intdigest(item_bytes)
        h2: int = self._hasher2_intdigest(item_bytes)
        m: int = self.size
        num_hashes: int = self.num_hashes
        # Generate k indices using Kirsch-Mitzenmacher optimization
        return [(h1 + i * h2 + (i * (i - 1) // 2)) % m for i in range(num_hashes)]

    def _add_indices(self, indices: List[int]) -> None:
        """Sets the bits at the given indices in the bit array."""
        bit_arr: bitarray = self.bit_array
        for index in indices:
            bit_arr[index] = 1

    def _check_indices(self, indices: List[int]) -> bool:
        """Checks if all bits at the given indices are set."""
        bit_arr: bitarray = self.bit_array
        for index in indices:
            if not bit_arr[index]:
                return False  # Definitely not present (early exit)
        return True  # Possibly present

    # --- Public Add/Contains Methods ---

    def add(self, item: KeyType) -> None:
        """
        Adds an item to the Bloom filter.

        The item is first converted to bytes using the serializer provided
        during initialization.

        Args:
            item: The item of KeyType to add.
        """
        try:
            item_bytes: bytes = self.serializer(item)
        except Exception as e:
            raise TypeError(
                f"Failed to serialize item of type {type(item).__name__} with provided serializer: {e}"
            ) from e

        indices: List[int] = self._get_indices(item_bytes)
        self._add_indices(indices)
        self.num_items += 1

    def __contains__(self, item: KeyType) -> bool:
        """
        Checks if an item might be in the Bloom filter.

        The item is first converted to bytes using the serializer provided
        during initialization.

        Args:
            item: The item of KeyType to check.

        Returns:
            True if the item is possibly in the set (may be a false positive).
            False if the item is definitely not in the set.
        """
        try:
            item_bytes: bytes = self.serializer(item)
        except Exception as e:
            # If serialization fails, the item cannot have been added
            raise TypeError(
                f"Warning: Failed to serialize item for checking. Returning False. Error: {e}"
            ) from e

        indices: List[int] = self._get_indices(item_bytes)
        result = self._check_indices(indices)
        return result

    def contains_batch(self, items: Iterable[KeyType]) -> List[bool]:
        """
        Checks if multiple items might be in the Bloom filter.

        The items are first converted to bytes using the serializer provided
        during initialization.

        Args:
            items: An iterable of items of KeyType to check.

        Returns:
            A list of booleans indicating whether each item is possibly in the set
            (may be a false positive). False if the item is definitely not in the set.
        """
        try:
            item_bytes_list: List[bytes] = [
                self.serializer(item) for item in items
            ]
        except Exception as e:
            # If serialization fails, the items cannot have been added
            raise TypeError(
                f"Warning: Failed to serialize items for checking. Returning False. Error: {e}"
            ) from e

        indices_list: List[List[int]] = [
            self._get_indices(item_bytes) for item_bytes in item_bytes_list
        ]
        results = [self._check_indices(indices) for indices in indices_list]
        return results

    # --- Other Public Methods ---

    def __len__(self) -> int:
        """Returns the number of items added."""
        return self.num_items

    @property
    def bit_size(self) -> int:
        """Returns the size of the underlying bit array (m)."""
        return self.size

    def __sizeof__(self) -> int:
        """Returns the size of the underlying bit array in bytes"""
        return math.ceil(self.bit_size / 8)

    def get_current_false_positive_rate(self) -> float:
        """
        Estimates the current theoretical false positive rate based on the
        number of items added (`num_items`).

        Formula: (1 - exp(-k * n / m))^k
        Where: k = num_hashes, n = num_items, m = size

        Returns:
            The estimated false positive probability (float between 0.0 and 1.0).
        """
        k: int = self.num_hashes
        n: int = self.num_items
        m: int = self.size

        if m == 0 or n == 0:  # Avoid division by zero or calculation for empty filter
            return 0.0

        try:
            exponent: float = -k * n / float(m)
            rate: float = (1.0 - math.exp(exponent)) ** k
        except (OverflowError, ValueError):
            rate = 1.0  # Theoretical rate approaches 1 if calculations fail

        return max(0.0, min(1.0, rate))  # Clamp result

    def __repr__(self) -> str:
        """Returns a developer-friendly representation of the filter."""
        # Determine serializer name if possible, otherwise show type
        serializer_name = getattr(
            self.serializer, "__name__", str(type(self.serializer))
        )
        return (
            f"{self.__class__.__name__}("
            f"capacity={self.capacity}, "
            f"error_rate={self.error_rate:.2e}, "
            f"serializer={serializer_name}, "
            f"size={self.size}, "
            f"num_hashes={self.num_hashes}, "
            f"num_items={self.num_items})"
        )