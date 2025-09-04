"""
testing/test_serializer.py

Unit tests for the picoNet.serializer module.
"""

import unittest
import sys
import os
import msgpack

# Add the root project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picoNet.serializer import serialize, deserialize

class TestSerializer(unittest.TestCase):
    """
    Test suite for data serialization and deserialization.
    """

    def test_serialize_deserialize_roundtrip(self):
        """
        Tests that a complex data structure can be serialized and then
        deserialized back to its original form.
        """
        print("\nRunning test_serialize_deserialize_roundtrip...")

        # 1. Create a sample data structure representing a game command
        original_data = {
            "command": "PLAYER_MOVE",
            "player_id": "player_12345",
            "position": [10.5, 0.0, -22.3],
            "velocity": [1.2, 0.0, 0.5],
            "is_running": True,
            "tick": 54321
        }
        print(f"Original data: {original_data}")

        # 2. Serialize the data into bytes
        serialized_data = serialize(original_data)
        print(f"Serialized data size: {len(serialized_data)} bytes")
        self.assertIsInstance(serialized_data, bytes)

        # 3. Deserialize the bytes back into a Python object
        deserialized_data = deserialize(serialized_data)
        print(f"Deserialized data: {deserialized_data}")

        # 4. Assert that the deserialized data is identical to the original
        self.assertEqual(original_data, deserialized_data,
                         "The deserialized data should be identical to the original.")
        print("Roundtrip successful.")

    def test_deserialize_invalid_data(self):
        """
        Tests that deserialize correctly raises an exception when given
        malformed data that is not valid MessagePack.
        """
        print("\nRunning test_deserialize_invalid_data...")
        # A msgpack map header indicating 1 key-value pair, but only providing a key.
        # This is structurally invalid and will cause an UnpackException.
        invalid_data = b'\x81\xa1a'

        # Verify that the expected exception is raised
        with self.assertRaises(msgpack.UnpackException):
            deserialize(invalid_data)

        print("msgpack.UnpackException was correctly raised for invalid data.")

if __name__ == '__main__':
    unittest.main()

