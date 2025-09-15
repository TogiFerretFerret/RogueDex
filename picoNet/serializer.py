"""
picoNet/custom_serializer.py

A hyper-optimized, custom binary serializer for RogueDex game commands.
This serializer is designed to be a drop-in replacement for the msgpack-based
one, but with a significantly smaller payload size for our specific data structures.

The format uses single-byte tags for data types and interns common dictionary
keys into single-byte IDs to achieve high efficiency. It can also handle
unknown keys, making it flexible for other data structures.
"""

import struct
import io

# --- Type Tags ---
# A single byte that precedes each piece of data to identify its type.
TAG_NULL = 0x00
TAG_BOOL_FALSE = 0x01
TAG_BOOL_TRUE = 0x02
TAG_INT32 = 0x03    # 4-byte signed integer
TAG_FLOAT64 = 0x04  # 8-byte double-precision float
TAG_STRING_UTF8 = 0x05
TAG_LIST = 0x06
TAG_DICT = 0x07     # A dictionary with our special known keys

# --- Key Tags (for expandability) ---
TAG_KNOWN_KEY = 0x08  # The key is in our codebook, next byte is its ID
TAG_UNKNOWN_KEY = 0x09 # The key is a string, next bytes are its data

# --- Known Keys "Codebook" ---
# This is the core optimization. We map common, repeated string keys
# to a single, efficient byte. This saves a massive amount of space.
KNOWN_KEYS = {
    'command': 0x01,
    'player_id': 0x02,
    'position': 0x03,
    'velocity': 0x04,
    'is_running': 0x05,
    'tick': 0x06,
    'x': 0x07,
    'y': 0x08,
    'hex': 0x09,
    'color': 0x0A,
}
# Create a reverse mapping for fast deserialization
KNOWN_KEYS_INV = {v: k for k, v in KNOWN_KEYS.items()}


def serialize(data: dict) -> bytes:
    """
    Serializes a Python dictionary into our custom compact byte format.

    Args:
        data: A dictionary containing game command data.

    Returns:
        A byte string representing the serialized data.
    """
    if not isinstance(data, dict):
        raise TypeError("Top-level object for this serializer must be a dictionary.")

    stream = io.BytesIO()
    stream.write(bytes([TAG_DICT]))
    stream.write(struct.pack('>H', len(data)))

    for key, value in data.items():
        # --- The Key Optimization ---
        # Check if the key is one of our special, optimized keys.
        if key in KNOWN_KEYS:
            stream.write(bytes([TAG_KNOWN_KEY]))
            stream.write(bytes([KNOWN_KEYS[key]]))
        else:
            # Fallback for any unknown keys, making the format expandable.
            stream.write(bytes([TAG_UNKNOWN_KEY]))
            encoded_key = key.encode('utf-8')
            stream.write(struct.pack('>H', len(encoded_key)))
            stream.write(encoded_key)

        # Serialize the value using the recursive helper
        _serialize_value(stream, value)

    return stream.getvalue()

def _serialize_value(stream, value):
    """Helper function to recursively serialize a value to the stream."""
    if value is None:
        stream.write(bytes([TAG_NULL]))
    elif isinstance(value, bool):
        stream.write(bytes([TAG_BOOL_TRUE if value else TAG_BOOL_FALSE]))
    elif isinstance(value, int):
        stream.write(bytes([TAG_INT32]))
        stream.write(struct.pack('>i', value))
    elif isinstance(value, float):
        stream.write(bytes([TAG_FLOAT64]))
        stream.write(struct.pack('>d', value))
    elif isinstance(value, str):
        stream.write(bytes([TAG_STRING_UTF8]))
        encoded_str = value.encode('utf-8')
        stream.write(struct.pack('>H', len(encoded_str)))
        stream.write(encoded_str)
    elif isinstance(value, list):
        stream.write(bytes([TAG_LIST]))
        stream.write(struct.pack('>H', len(value)))
        for item in value:
            _serialize_value(stream, item)
    elif isinstance(value, dict):
        # Allow nested dictionaries by calling back to the main serialize function
        # This gives them the same key-optimization benefits.
        nested_data = serialize(value)
        stream.write(nested_data)
    else:
        raise TypeError(f"Unsupported type for serialization: {type(value)}")


def deserialize(data: bytes) -> dict:
    """
    Deserializes a byte string from our custom format into a Python dictionary.
    """
    stream = io.BytesIO(data)
    main_tag = stream.read(1)[0]

    if main_tag != TAG_DICT:
        raise ValueError("Data stream does not start with a dictionary tag.")

    try:
        num_items = struct.unpack('>H', stream.read(2))[0]
        result_dict = {}
        for _ in range(num_items):
            key_tag = stream.read(1)[0]
            key = None
            if key_tag == TAG_KNOWN_KEY:
                key_id = stream.read(1)[0]
                key = KNOWN_KEYS_INV.get(key_id)
                if key is None:
                    raise ValueError(f"Invalid known key ID '{key_id}' found.")
            elif key_tag == TAG_UNKNOWN_KEY:
                key_length = struct.unpack('>H', stream.read(2))[0]
                key = stream.read(key_length).decode('utf-8')
            else:
                raise ValueError(f"Invalid or unknown key tag '{key_tag}' in stream.")
            
            value = _deserialize_value(stream)
            result_dict[key] = value
        return result_dict
    except (struct.error, IndexError):
        raise ValueError("Malformed or incomplete data stream.")


def _deserialize_value(stream):
    """Helper function to recursively deserialize a value from the stream."""
    # We peek at the next byte to see what type it is.
    tag_byte = stream.read(1)
    if not tag_byte:
        raise ValueError("Incomplete stream: trying to read a value tag.")
    tag = tag_byte[0]
    
    if tag == TAG_NULL:
        return None
    if tag == TAG_BOOL_FALSE:
        return False
    if tag == TAG_BOOL_TRUE:
        return True
    if tag == TAG_INT32:
        return struct.unpack('>i', stream.read(4))[0]
    if tag == TAG_FLOAT64:
        return struct.unpack('>d', stream.read(8))[0]
    if tag == TAG_STRING_UTF8:
        length = struct.unpack('>H', stream.read(2))[0]
        return stream.read(length).decode('utf-8')
    if tag == TAG_LIST:
        num_items = struct.unpack('>H', stream.read(2))[0]
        return [_deserialize_value(stream) for _ in range(num_items)]
    if tag == TAG_DICT:
        # If we find a nested dictionary, we need to deserialize it fully.
        # This requires knowing its length, which is a bit tricky.
        # For now, we'll put the tag back and deserialize from the parent.
        # A more robust solution might require length-prefixing dictionaries.
        stream.seek(stream.tell() - 1) # Rewind the stream by one byte
        return deserialize(stream.read()) # Consume the rest of the stream
    
    raise ValueError(f"Unknown type tag in stream: {tag}")


