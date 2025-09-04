"""
testing/test_packet.py

Unit tests for the picoNet.packet module.
"""

import unittest
import sys
import os

# Add the root project directory to the Python path
# This allows us to import modules from the picoNet library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picoNet.packet import Packet, PacketHeader, pack_packet, unpack_packet

class TestPacket(unittest.TestCase):
    """
    Test suite for packet serialization and deserialization.
    """

    def test_pack_unpack_roundtrip(self):
        """
        Tests that a packet can be packed and then unpacked back to its
        original form without any data loss.
        """
        print("\nRunning test_pack_unpack_roundtrip...")

        # 1. Create a sample packet with some non-default values
        original_header = PacketHeader(
            sequence=1024,
            ack=512,
            ack_bitfield=0b1101010101010101
        )
        original_payload = b'This is a test payload!'
        original_packet = Packet(header=original_header, payload=original_payload)

        # 2. Pack the packet into bytes
        packed_data = pack_packet(original_packet)
        print(f"Packed data size: {len(packed_data)} bytes")
        self.assertIsInstance(packed_data, bytes)

        # 3. Unpack the bytes back into a packet
        unpacked_packet = unpack_packet(packed_data)
        print(f"Unpacked packet: {unpacked_packet}")
        self.assertIsInstance(unpacked_packet, Packet)

        # 4. Assert that the unpacked packet is identical to the original
        self.assertEqual(original_packet, unpacked_packet,
                         "The unpacked packet should be identical to the original.")
        print("Roundtrip successful.")

    def test_unpack_too_small_packet(self):
        """
        Tests that unpack_packet correctly raises a ValueError when given
        a byte string that is smaller than the header size.
        """
        print("\nRunning test_unpack_too_small_packet...")
        invalid_data = b'\x01\x02\x03' # Only 3 bytes, much smaller than the header

        # Use assertRaises as a context manager to verify the exception
        with self.assertRaises(ValueError):
            unpack_packet(invalid_data)

        print("ValueError was correctly raised for small packet.")

if __name__ == '__main__':
    unittest.main()

