"""
testing/rotomdex/test_integration.py

End-to-end tests for the Rotomdex implementation of the engine.
"""
import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any

# --- Add project root to path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from battledex_engine.battle import Battle
from battledex_engine.interfaces import Combatant, SpecialAction
from rotomdex.pokemon import Pokemon
from rotomdex.move import Move
# FIX: Import item loader and Item class
from rotomdex.data_loader import load_pokemon_data, load_move_data, load_item_data
from battledex_engine.item import Item
from rotomdex.factory import create_pokemon_from_data
from rotomdex.ruleset import PokemonRuleset

# --- Test Case ---

class TestBattleIntegration(unittest.TestCase):
    """
    Tests the full integration of Rotomdex classes with the Battle engine.
    """

    @classmethod
    def setUpClass(cls):
        """
        Load all real game data from the JSON cache.
        This is a true integration test.
        """
        print("\nLoading all game data for integration tests...")
        
        # FIX: Load all three data files
        cls.pokemon_data = load_pokemon_data()
        cls.move_data = load_move_data()
        cls.item_data = load_item_data()
        print("Game data loaded.")

    def setUp(self):
        """Create fresh Pokémon and battle for each test."""
        
        # --- Create Pokémon ---
        # We type hint as Combatant to test against the interface
        self.pikachu: Combatant = create_pokemon_from_data(
            species_name="pikachu",
            level=50,
            move_names=["tackle", "growl"],
            pokemon_data_map=self.pokemon_data,
            move_data_map=self.move_data,
            item_data_map=self.item_data, # FIX: Pass item data
            instance_id="p1_pika",
            item_name="light-ball", # FIX: Give light ball
            is_active=True
        )
        
        self.charmander: Combatant = create_pokemon_from_data(
            species_name="charmander",
            level=50,
            move_names=["scratch", "growl"],
            pokemon_data_map=self.pokemon_data,
            move_data_map=self.move_data,
            item_data_map=self.item_data, # FIX: Pass item data
            instance_id="p2_char",
            is_active=True
        )
        
        # --- Create Ruleset and Battle ---
        self.combatants_list = [self.pikachu, self.charmander]
        self.ruleset = PokemonRuleset(self.combatants_list)
        self.battle = Battle(
            teams=[[self.pikachu], [self.charmander]],
            ruleset=self.ruleset
        )

    def test_pikachu_vs_charmander_turn_1(self):
        """An end-to-end test of a single battle turn."""
        print("\n--- Running Test: test_pikachu_vs_charmander_turn_1 ---")
        
        # We know these are Pokemon, so we can cast to get specific stats
        pika: Pokemon = self.pikachu
        char: Pokemon = self.charmander

        pika_initial_hp = pika.current_hp
        char_initial_hp = char.current_hp
        
        print(f"  Creating Pokémon...")
        print(f"  Pikachu HP: {pika_initial_hp}, Item: {pika.held_item.name}")
        print(f"  Charmander HP: {char_initial_hp}, Item: {char.held_item}")

        # 2. Action Submission
        pika_move = next(m for m in pika.moves if m.name == "tackle")
        char_move = next(m for m in char.moves if m.name == "scratch")
        
        actions = {
            pika.id: [pika_move],
            char.id: [char_move]
        }
        print(f"  Submitting actions: {pika_move.name} and {char_move.name}")
        self.battle.submit_actions(actions)

        # 3. Processing
        print("  Processing turn...")
        self.battle.process_turn()

        # 4. Assertions
        print("  Asserting results...")
        self.assertLess(pika.current_hp, pika_initial_hp, "Pikachu's HP did not decrease.")
        self.assertLess(char.current_hp, char_initial_hp, "Charmander's HP did not decrease.")
        
        print(f"  Pikachu HP: {pika.current_hp} / {pika_initial_hp}")
        print(f"  Charmander HP: {char.current_hp} / {char_initial_hp}")
        print("--- Test Complete ---")


    @unittest.skip("Terastallization logic not yet implemented in ruleset")
    def test_terastallization_success(self):
        """Tests that a Pokémon can successfully Terastallize."""
        print("\n--- Running Test: test_terastallization_success ---")
        pika: Pokemon = self.pikachu
        
        # FIX: Give Pikachu the Tera Orb
        pika.held_item = create_item_from_data("tera-orb", self.item_data)
        self.assertEqual(pika.held_item.id_name, "tera-orb")
        
        print(f"  Pikachu original types: {pika.current_types}")
        self.assertEqual(pika.current_types, ["electric"])
        self.assertFalse(pika.has_terastallized)

        # 2. Action Submission
        tera_action = SpecialAction(kind="terastalize")
        actions = { pika.id: [tera_action] }
        
        print(f"  Submitting: Terastallize")
        self.battle.submit_actions(actions)
        
        # 3. Processing
        print("  Processing turn...")
        self.battle.process_turn()
        
        # 4. Assertions
        print("  Asserting results...")
        self.assertTrue(pika.has_terastallized, "Pikachu did not Terastallize.")
        self.assertEqual(pika.current_types, [pika.tera_type], "Pikachu's type did not change to its Tera Type.")
        print(f"  Pikachu new types: {pika.current_types}")
        print("--- Test Complete ---")

    @unittest.skip("Terastallization logic not yet implemented in ruleset")
    def test_terastallization_fail_no_orb(self):
        """Tests that Terastallization fails if the Pokémon has no Tera Orb."""
        print("\n--- Running Test: test_terastallization_fail_no_orb ---")
        pika: Pokemon = self.pikachu
        
        # FIX: Ensure Pikachu has no item
        pika.held_item = None
        self.assertIsNone(pika.held_item)
        
        print(f"  Pikachu original types: {pika.current_types}")
        self.assertFalse(pika.has_terastallized)

        # 2. Action Submission
        tera_action = SpecialAction(kind="terastalize")
        actions = { pika.id: [tera_action] }
        
        print(f"  Submitting: Terastallize")
        self.battle.submit_actions(actions)
        
        # 3. Processing
        print("  Processing turn...")
        self.battle.process_turn()
        
        # 4. Assertions
        print("  Asserting results...")
        self.assertFalse(pika.has_terastallized, "Pikachu should not have Terastallized.")
        self.assertEqual(pika.current_types, ["electric"], "Pikachu's type should not have changed.")
        print(f"  Pikachu types unchanged: {pika.current_types}")
        print("--- Test Complete ---")


    # --- Placeholder Tests ---
    
    @unittest.skip("Feature not implemented")
    def test_mega_evolution(self):
        pass

    @unittest.skip("Feature not implemented")
    def test_z_moves(self):
        pass

    @unittest.skip("Feature not implemented")
    def test_dynamax(self):
        pass


if __name__ == '__main__':
    unittest.main()


