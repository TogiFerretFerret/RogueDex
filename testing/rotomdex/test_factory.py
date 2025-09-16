"""
testing/rotomdex/test_factory.py

Unit tests for the rotomdex.factory module.
"""

import unittest
import sys
import os
from pathlib import Path

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from rotomdex.data_loader import load_pokemon_data, load_move_data
from rotomdex.factory import create_move_from_data, create_pokemon_from_data
from rotomdex.pokemon import Pokemon
from rotomdex.move import Move

class TestFactory(unittest.TestCase):
    """
    Test suite for creating game objects from loaded data.
    """

    @classmethod
    def setUpClass(cls):
        """
        Load all necessary mock data once for all tests in this class.
        """
        mock_data_path = Path(__file__).parent / "mock_data"
        cls.pokemon_data = load_pokemon_data(mock_data_path / "pokemon.json")
        cls.move_data = load_move_data(mock_data_path / "moves.json")

    def test_create_move(self):
        """
        Tests that a Move object can be created correctly from data.
        """
        move = create_move_from_data("Thunder Shock", self.move_data)
        
        self.assertIsInstance(move, Move)
        self.assertEqual(move.name, "Thunder Shock")
        self.assertEqual(move.power, 40)
        self.assertEqual(move.move_type, "Electric")
        print("\nSuccessfully tested Move creation.")

    def test_create_pokemon(self):
        """
        Tests that a Pokemon object can be created correctly from data,
        including its moves and calculated stats.
        """
        pikachu = create_pokemon_from_data(
            species_name="Pikachu",
            level=50,
            move_names=["Thunder Shock", "Tackle"],
            pokemon_data_map=self.pokemon_data,
            move_data_map=self.move_data,
            instance_id="player1_pikachu"
        )

        self.assertIsInstance(pikachu, Pokemon)
        self.assertEqual(pikachu.species_name, "Pikachu")
        self.assertEqual(pikachu.level, 50)
        
        # Check that stats were calculated correctly for Lv. 50
        # Formula: floor(((2 * base) * level) / 100 + 5)
        # Pikachu speed: floor(((2 * 90) * 50) / 100 + 5) = floor(90 + 5) = 95
        self.assertEqual(pikachu.stats['speed'], 95)

        # Check that moves were created and attached
        self.assertEqual(len(pikachu.moves), 2)
        self.assertIsInstance(pikachu.moves[0], Move)
        self.assertEqual(pikachu.moves[0].name, "Thunder Shock")
        print("Successfully tested Pokemon creation.")

if __name__ == '__main__':
    unittest.main()

