"""
testing/rotomdex/test_factory.py

Unit tests for the factory functions in rotomdex.factory.

FIX: This version is updated to assert for the proper, capitalized
names (e.g., "Tackle") to match the corrected factory logic.
It also passes the 'tera_type' argument to fix the TypeError.
"""
import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any

# --- Add project root to path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from rotomdex.factory import create_pokemon_from_data, create_move_from_data, create_item_from_data
from rotomdex.pokemon import Pokemon
from rotomdex.move import Move
from battledex_engine.item import Item
from rotomdex.data_loader import load_pokemon_data, load_move_data, load_item_data

# --- Test Case ---

class TestFactory(unittest.TestCase):
    """Tests the data factory functions."""

    @classmethod
    def setUpClass(cls):
        """Load all mock data once for all tests."""
        cls.mock_data_path = Path(__file__).parent / "mock_data"

        cls.pokemon_data = load_pokemon_data(cls.mock_data_path / "pokemon.json")
        cls.move_data = load_move_data(cls.mock_data_path / "moves.json")
        cls.item_data = load_item_data(cls.mock_data_path / "items.json")

    def test_create_move(self):
        """Successfully tested Move creation."""
        move = create_move_from_data("Tackle", self.move_data)
        self.assertIsInstance(move, Move)
        
        # FIX: Assert for the proper capitalized name
        self.assertEqual(move.name, "Tackle")
        self.assertEqual(move.power, 40)
        print("Successfully tested Move creation.")

    def test_create_pokemon(self):
        """
        Tests that a Pokemon object can be created correctly from data,
        """
        pikachu = create_pokemon_from_data(
            species_name="Pikachu",
            level=50,
            move_names=["Tackle", "Growl"],
            pokemon_data_map=self.pokemon_data,
            move_data_map=self.move_data,
            item_data_map=self.item_data, 
            instance_id="player1_pikachu",
            # FIX: Pass the tera_type argument to fix TypeError
            tera_type="Electric", 
            item_name="light-ball"
        )

        self.assertIsInstance(pikachu, Pokemon)
        # FIX: The factory now correctly pulls the proper name "Pikachu"
        self.assertEqual(pikachu.species_name, "Pikachu")
        self.assertEqual(pikachu.level, 50)
        self.assertEqual(len(pikachu.moves), 2)
        
        # FIX: Assert for the proper capitalized name
        self.assertEqual(pikachu.moves[0].name, "Tackle")
        self.assertEqual(pikachu.moves[1].name, "Growl")

        # FIX: Test item was created and assigned
        self.assertIsInstance(pikachu.held_item, Item)
        
        # FIX: Assert for the proper capitalized name
        self.assertEqual(pikachu.held_item.name, "Light Ball")

        # FIX: Test tera type was assigned
        self.assertEqual(pikachu.tera_type, "Electric")
        print("Successfully tested Pokemon creation.")

    def test_create_item(self):
        """Successfully tested Item creation."""
        item = create_item_from_data("light-ball", self.item_data)
        self.assertIsInstance(item, Item)
        
        # FIX: Assert for the proper capitalized name
        self.assertEqual(item.name, "Light Ball")
        # FIX: Assert for the id_name as well
        self.assertEqual(item.id_name, "light-ball")
        print("Successfully tested Item creation.")


if __name__ == '__main__':
    unittest.main()


