"""
picoNet/packet.py

Defines the core data structures for network communication in picoNet and
provides utility functions for serializing and deserializing them.
"""

import struct
from dataclasses import dataclass

# A unique 32-bit integer to identify our game's traffic.
# This helps quickly discard any unrelated UDP packets that might be
# received on the listening port. We'll use a simple value for now.
PROTOCOL_ID = 0x524F4755 # Hex for "ROGU"

# The format string for packing/unpacking the header with the struct module.
# '!' specifies network byte order (big-endian).
# 'I' is a 4-byte unsigned int (for protocol_id and sequence).
# 'H' is a 2-byte unsigned short (for ack and ack_bitfield).
HEADER_FORMAT = "!IIHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT) # Should be 12 bytes

@dataclass
class PacketHeader:
    """
    Represents the header for every picoNet packet. (12 bytes total)

    This structure contains all the metadata necessary to manage reliability,
    ordering, and connection state.
    """
    protocol_id: int = PROTOCOL_ID
    sequence: int = 0
    ack: int = 0
    ack_bitfield: int = 0

@dataclass
class Packet:
    """
    Represents a complete picoNet packet, containing both the header
    and the game-specific data payload.
    """
    header: PacketHeader
    payload: bytes

def pack_packet(packet: Packet) -> bytes:
    """
    Serializes a Packet object into a byte string for transmission.

    Args:
        packet: The Packet object to serialize.

    Returns:
        A byte string representing the complete packet.
    """
    header_bytes = struct.pack(
        HEADER_FORMAT,
        packet.header.protocol_id,
        packet.header.sequence,
        packet.header.ack,
        packet.header.ack_bitfield
    )
    return header_bytes + packet.payload

def unpack_packet(data: bytes) -> Packet:
    """
    Deserializes a byte string into a Packet object.

    Args:
        data: The raw byte string received from the network.

    Returns:
        A Packet object representing the received data.

    Raises:
        ValueError: If the data is smaller than the minimum header size.
    """
    if len(data) < HEADER_SIZE:
        raise ValueError(f"Received data is too small to be a valid packet. "
                         f"Got {len(data)} bytes, expected at least {HEADER_SIZE}.")

    header_tuple = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
    header = PacketHeader(
        protocol_id=header_tuple[0],
        sequence=header_tuple[1],
        ack=header_tuple[2],
        ack_bitfield=header_tuple[3]
    )
    payload = data[HEADER_SIZE:]

    return Packet(header=header, payload=payload)


