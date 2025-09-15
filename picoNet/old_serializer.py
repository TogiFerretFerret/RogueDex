"""
picoNet/serializer.py

Provides functions for serializing and deserializing game commands and data
structures into a compact binary format using MessagePack.

This module acts as a wrapper around the `msgpack` library, ensuring a
consistent serialization method throughout the project.
"""

import msgpack
from typing import Any

def serialize(data: Any) -> bytes:
    """
    Serializes a Python object into a byte string using MessagePack.

    Args:
        data: A msgpack-compatible Python object (e.g., dict, list, str, int).

    Returns:
        A byte string representing the serialized data.
    """
    # `use_bin_type=True` is the modern and recommended setting.
    return msgpack.packb(data, use_bin_type=True)

def deserialize(data: bytes) -> Any:
    """
    Deserializes a byte string from MessagePack into a Python object.

    Args:
        data: A byte string containing MessagePack-serialized data.

    Returns:
        The deserialized Python object.

    Raises:
        msgpack.UnpackException: If the data is malformed, incomplete, or contains
                                 extra data. This function provides a consistent
                                 exception type for any unpacking failure.
    """
    try:
        # `raw=False` ensures that strings are decoded to Python's str type.
        # `strict_map_key=False` is a safe default.
        return msgpack.unpackb(data, raw=False)
    except (msgpack.UnpackException, ValueError) as e:
        # Catch potential errors from the msgpack library (like ValueError for
        # incomplete data) and re-raise them as the expected UnpackException
        # to provide a consistent API for our serializer.
        raise msgpack.UnpackException(f"Failed to deserialize data: {e}") from e


