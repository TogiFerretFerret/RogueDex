"""
testing/rotomdex/test_data_loader.py

Unit tests for the rotomdex.data_loader module.
"""

import unittest
import sys
import os
from pathlib import Path

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# This import will fail until we implement the data_loader
from rotomdex.data_loader import load_pokemon_data, load_move_data

class TestDataLoader(unittest.TestCase):
    """
    Test suite for loading data from our mock JSON files.
    """

    def setUp(self):
        """
        Locates the mock data directory for use in tests.
        """
        self.mock_data_path = Path(__file__).parent / "mock_data"
        self.assertTrue(self.mock_data_path.exists(), "Mock data directory not found.")

    def test_load_pokemon_data(self):
        """
        Tests that we can successfully load and parse the mock pokemon.json file.
        """
        pokemon_file = self.mock_data_path / "pokemon.json"
        pokemon_data = load_pokemon_data(pokemon_file)

        # Basic assertions
        self.assertIsInstance(pokemon_data, dict)
        # FIX: Assert for lowercase keys to match the mock data format
        self.assertIn("pikachu", pokemon_data)
        self.assertIn("bulbasaur", pokemon_data)

        # Check a specific entry
        # FIX: Access using the correct lowercase key
        pikachu = pokemon_data["pikachu"]
        self.assertEqual(pikachu['types'][0], "Electric")
        self.assertEqual(pikachu['base_stats']['speed'], 90)
        print("\nSuccessfully tested loading Pokémon data.")

    def test_load_move_data(self):
        """
        Tests that we can successfully load and parse the mock moves.json file.
        """
        moves_file = self.mock_data_path / "moves.json"
        move_data = load_move_data(moves_file)

        # Basic assertions
        self.assertIsInstance(move_data, dict)
        # FIX: Assert for lowercase key to match the mock data format
        self.assertIn("thunder-shock", move_data)

        # Check a specific entry
        # FIX: Access using the correct lowercase key
        thunder_shock = move_data["thunder-shock"]
        self.assertEqual(thunder_shock['power'], 40)
        self.assertEqual(thunder_shock['move_type'], "Electric")
        print("Successfully tested loading move data.")


if __name__ == '__main__':
    unittest.main()
