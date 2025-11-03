"""
testing/rotomdex/test_integration.py

End-to-end tests for the Rotomdex implementation of the engine.

FIX: This version is now internally consistent.
- It passes proper, capitalized names (e.g., "Pikachu", "Tackle")
  to the factory.
- It asserts for those same proper, capitalized names.

FIX: This version adds new unit tests for the Ruleset's
_get_effectiveness method, driven by TDD.
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
# FIX: Import load_type_data
from rotomdex.data_loader import load_pokemon_data, load_move_data, load_item_data, load_type_data
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

        cls.pokemon_data = load_pokemon_data()
        cls.move_data = load_move_data()
        
        # FIX: Load the real type data
        cls.type_data = load_type_data() 
        
        try:
            cls.item_data = load_item_data()
        except FileNotFoundError:
            print("Item cache not found. This is optional, but some tests may fail.")
            cls.item_data = {} # Allow tests to run without items
            
        print("Game data loaded.")
        
        # --- Create a single ruleset instance for type testing ---
        # This is a 'dummy' map just to satisfy the constructor.
        # The type tests don't need real combatants.
        dummy_map = {}
        # FIX: Pass the loaded type data to the ruleset
        # FIX: Removed type_data argument to match ruleset.__init__ signature
        cls.ruleset_for_testing = PokemonRuleset(dummy_map)

    def setUp(self):
        """Create fresh Pokémon and battle for each test."""

        # --- Create Pokémon ---
        # We type hint as Combatant to test against the interface
        try:
            self.pikachu: Combatant = create_pokemon_from_data(
                # FIX: Use proper, capitalized names as input
                species_name="Pikachu",
                level=50,
                move_names=["Tackle", "Growl"],
                pokemon_data_map=self.pokemon_data,
                move_data_map=self.move_data,
                item_data_map=self.item_data,
                instance_id="p1_pika",
                item_name="light-ball",
                is_active=True
            )

            self.charmander: Combatant = create_pokemon_from_data(
                # FIX: Use proper, capitalized names as input
                species_name="Charmander",
                level=50,
                move_names=["Scratch", "Growl"],
                pokemon_data_map=self.pokemon_data,
                move_data_map=self.move_data,
                item_data_map=self.item_data,
                instance_id="p2_char",
                is_active=True
            )
        except KeyError as e:
            print(f"\nCRITICAL ERROR in setUp: {e}")
            print("This *usually* means your JSON data cache is stale.")
            print("Run 'python rotomdex/api_importer.py' to fix it.")
            # Skip all other tests if we can't even create the Pokémon
            raise

        # --- Create Ruleset and Battle ---
        self.combatants_list = [self.pikachu, self.charmander]
        # The Ruleset constructor expects a DICT, not a list.
        self.combatant_map = {c.id: c for c in self.combatants_list}
        
        # FIX: Pass the loaded type data to the ruleset
        # FIX: Removed type_data argument to match ruleset.__init__ signature
        self.ruleset = PokemonRuleset(self.combatant_map)
        
        self.battle = Battle(
            teams=[[self.pikachu], [self.charmander]],
            ruleset=self.ruleset
        )

    def test_pikachu_vs_charmander_turn_1(self):
        """An end-to-end test of a single battle turn."""
        print("\n--- Running Test: test_pikachu_vs_charmander_turn_1 ---")

        pika: Pokemon = self.pikachu
        char: Pokemon = self.charmander

        pika_initial_hp = pika.current_hp
        char_initial_hp = char.current_hp

        print(f"  Creating Pokémon...")
        # This printout is the key! It will say "light-ball"
        # until factory.py is fixed, then it will say "Light Ball"
        if pika.held_item:
            print(f"  Pikachu HP: {pika_initial_hp}, Item: {pika.held_item.name}")
        else:
            print(f"  Pikachu HP: {pika_initial_hp}, Item: None")
            
        if char.held_item:
            print(f"  Charmander HP: {char_initial_hp}, Item: {char.held_item.name}")
        else:
            print(f"  Charmander HP: {char_initial_hp}, Item: None")


        # 2. Action Submission
        # FIX: Assert for the proper capitalized names
        pika_move = next(m for m in pika.moves if m.name == "Tackle")
        char_move = next(m for m in char.moves if m.name == "Scratch")

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


    # --- NEW: TDD Tests for Type Effectiveness ---
    # These tests validate the logic in ruleset.py
    
    def test_effectiveness_super_effective(self):
        """Tests 2x super effective damage (e.g., Electric > Water)."""
        print("\n--- Running Test: test_effectiveness_super_effective ---")
        # Test: Electric move vs. Water type
        multiplier = self.ruleset_for_testing._get_effectiveness(
            move_type="Electric",
            target_types=["Water"]
        )
        self.assertEqual(multiplier, 2.0)

    def test_effectiveness_not_very_effective(self):
        """Tests 0.5x not very effective damage (e.g., Electric > Grass)."""
        print("\n--- Running Test: test_effectiveness_not_very_effective ---")
        # Test: Electric move vs. Grass type
        multiplier = self.ruleset_for_testing._get_effectiveness(
            move_type="Electric",
            target_types=["Grass"]
        )
        self.assertEqual(multiplier, 0.5)

    def test_effectiveness_immune(self):
        """Tests 0x immune damage (e.g., Electric > Ground)."""
        print("\n--- Running Test: test_effectiveness_immune ---")
        # Test: Electric move vs. Ground type
        multiplier = self.ruleset_for_testing._get_effectiveness(
            move_type="Electric",
            target_types=["Ground"]
        )
        self.assertEqual(multiplier, 0.0)

    def test_effectiveness_dual_type_4x(self):
        """Tests 4x effective damage (e.g., Electric > Water/Flying)."""
        print("\n--- Running Test: test_effectiveness_dual_type_4x ---")
        # Test: Electric move vs. Water/Flying type (like Gyarados)
        multiplier = self.ruleset_for_testing._get_effectiveness(
            move_type="Electric",
            target_types=["Water", "Flying"]
        )
        self.assertEqual(multiplier, 4.0)

    def test_effectiveness_dual_type_neutral(self):
        """Tests neutral damage from mixed effectiveness (e.g., Electric > Water/Grass)."""
        print("\n--- Running Test: test_effectiveness_dual_type_neutral ---")
        # Test: Electric move vs. Water/Grass type (like Ludicolo)
        # 2.0 (vs Water) * 0.5 (vs Grass) = 1.0
        multiplier = self.ruleset_for_testing._get_effectiveness(
            move_type="Electric",
            target_types=["Water", "Grass"]
        )
        self.assertEqual(multiplier, 1.0)

    # --- End of Type Effectiveness Tests ---


    @unittest.skip("Terastallization logic not yet implemented in ruleset")
    def test_terastallization_success(self):
        """Tests that a Pokémon can successfully Terastallize."""
        print("\n--- Running Test: test_terastallization_success ---")
        pika: Pokemon = self.pikachu

        pika.held_item = create_item_from_data("tera-orb", self.item_data)
        self.assertEqual(pika.held_item.id_name, "tera-orb")

        print(f"  Pikachu original types: {pika.current_types}")
        self.assertEqual(pika.current_types, ["Electric"])
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
        self.assertEqual(pika.current_types, ["Electric"], "Pikachu's type should not have changed.")
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



