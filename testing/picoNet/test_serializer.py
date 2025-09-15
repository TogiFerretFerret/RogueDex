"""
testing/picoNet/test_serializer.py

The definitive unit tests for our new, custom picoNet.serializer module.
"""

import unittest
import sys
import os
import msgpack # Imported for the size comparison test

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Import our new custom serializer
from picoNet import serializer


class TestSerializer(unittest.TestCase):
    """
    Tests for the custom serializer module.
    Verifies round-trip integrity, size efficiency, error handling, and expandability.
    """

    def setUp(self):
        """Set up a standard, complex data dictionary for all tests."""
        self.game_command_data = {
            'command': 'PLAYER_MOVE',
            'player_id': 'player_12345',
            'position': [10.5, 0.0, -22.3],
            'velocity': [1.2, 0.0, 0.5],
            'is_running': True,
            'tick': 54321,
        }

    def test_serialize_deserialize_roundtrip(self):
        """
        Ensures that serializing and then deserializing a standard game command
        results in the exact same original data.
        """
        print("\nRunning test_serialize_deserialize_roundtrip...")
        serialized_data = serializer.serialize(self.game_command_data)
        deserialized_data = serializer.deserialize(serialized_data)

        self.assertEqual(self.game_command_data, deserialized_data,
                         "Round-trip data should be identical to the original.")
        print("Roundtrip successful.")

    def test_size_comparison_with_msgpack(self):
        """
        The critical test: proves our custom serializer produces a smaller payload
        than the generic msgpack serializer for our specific data.
        """
        print("\nRunning test_size_comparison_with_msgpack...")

        # Serialize with our custom, optimized format
        custom_serialized = serializer.serialize(self.game_command_data)
        custom_size = len(custom_serialized)
        print(f"Custom Serializer Size: {custom_size} bytes")

        # Serialize with the generic msgpack format for comparison
        msgpack_serialized = msgpack.packb(self.game_command_data, use_bin_type=True)
        msgpack_size = len(msgpack_serialized)
        print(f"MsgPack Serializer Size: {msgpack_size} bytes")

        self.assertLess(custom_size, msgpack_size,
                        "Custom serializer should produce a smaller payload than msgpack.")
        print(f"Success! Custom serializer is {msgpack_size - custom_size} bytes smaller.")

    def test_deserialize_invalid_data(self):
        """
        Tests that deserialize correctly raises a ValueError when given
        malformed data that is not valid for our custom format.
        """
        print("\nRunning test_deserialize_invalid_data...")
        # This is not a valid stream because it doesn't start with our TAG_DICT
        invalid_data = b'this is not valid data'

        # Verify that our custom ValueError is raised, not a msgpack error.
        with self.assertRaises(ValueError):
            serializer.deserialize(invalid_data)

        print("ValueError was correctly raised for invalid data.")

    def test_mixed_known_and_unknown_keys(self):
        """
        Tests serialization of a dictionary with both known and unknown keys,
        verifying the expandability of the format for turtle commands.
        """
        print("\nRunning test_mixed_known_and_unknown_keys...")
        
        turtle_command_data = {
            'command': 'TURTLE_CMD',      # Known key
            'turtle_id': 'michelangelo',  # Unknown key
            'actions': [
                {'action': 'forward', 'distance': 100}, # all unknown keys
                {'action': 'right', 'angle': 90, 'pen': 'down'}
            ]
        }

        serialized = serializer.serialize(turtle_command_data)
        deserialized = serializer.deserialize(serialized)

        self.assertEqual(turtle_command_data, deserialized,
                         "Should correctly handle a mix of known and unknown keys.")
        print("Successfully serialized and deserialized a mix of known and unknown keys.")


if __name__ == '__main__':
    unittest.main()

