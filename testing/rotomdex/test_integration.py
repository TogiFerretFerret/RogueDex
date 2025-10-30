"""
test_integration.py

This is the main "heart" of the application, converted into
a proper integration test.

It connects all the pieces:
1. Loads data (from rotomdex.data_loader)
2. Creates Pokémon (from rotomdex.factory)
3. Creates the ruleset (from rotomdex.ruleset)
4. Creates the battle (from battledex_engine.battle)
5. Runs a test turn and asserts the results.

To run (from the top-level RogueDex/ directory):
    python -m unittest discover tests
"""

import unittest
from rotomdex import (
    load_pokemon_data,
    load_move_data,
    create_pokemon_from_data,
    PokemonRuleset
)
from battledex_engine.battle import Battle
from battledex_engine.interfaces import Combatant

class TestBattleIntegration(unittest.TestCase):

    pokemon_data_map = {}
    move_data_map = {}
    
    @classmethod
    def setUpClass(cls):
        """
        Load all game data once for all tests in this class.
        This is expensive, so we don't want to do it for every test.
        """
        print("Loading all game data for integration tests...")
        try:
            # FIX: Pass no arguments to use the default cache path
            cls.pokemon_data_map = load_pokemon_data()
            cls.move_data_map = load_move_data()
            
            if not cls.pokemon_data_map or not cls.move_data_map:
                raise Exception("Failed to load data, JSON files might be missing.")
        except Exception as e:
            # If data loading fails, we can't run the tests.
            raise unittest.SkipTest(f"Skipping integration tests: Failed to load game data. {e}")

    def test_pikachu_vs_charmander_turn_1(self):
        """
        An end-to-end test of a single battle turn.
        """
        print("\n--- Running Test: test_pikachu_vs_charmander_turn_1 ---")
        
        # --- 2. Create Pokémon ---
        print("  Creating Pokémon...")
        try:
            pikachu: Combatant = create_pokemon_from_data(
                species_name="pikachu",
                level=50,
                move_names=["tackle", "growl"],
                pokemon_data_map=self.pokemon_data_map,
                move_data_map=self.move_data_map,
                instance_id="pika-1",
                is_active=True
            )
            
            charmander: Combatant = create_pokemon_from_data(
                species_name="charmander",
                level=50,
                move_names=["scratch", "growl"],
                pokemon_data_map=self.pokemon_data_map,
                move_data_map=self.move_data_map,
                instance_id="char-1",
                is_active=True
            )
        except KeyError as e:
            self.fail(f"Failed to create Pokémon. Missing data for: {e}. "
                      "Make sure 'pikachu', 'charmander', 'tackle', etc. exist in your JSON.")

        # Store initial HP for comparison
        # We need to cast to Pokemon to access 'stats' and 'current_hp'
        pika_pokemon = pikachu
        char_pokemon = charmander
        
        pika_initial_hp = pika_pokemon.stats['hp']
        char_initial_hp = char_pokemon.stats['hp']
        self.assertEqual(pika_pokemon.current_hp, pika_initial_hp)
        self.assertEqual(char_pokemon.current_hp, char_initial_hp)

        all_combatants = {
            pikachu.id: pikachu,
            charmander.id: charmander,
        }

        # --- 3. Create Ruleset ---
        ruleset = PokemonRuleset(all_combatants)

        # --- 4. Create Battle ---
        battle = Battle(
            teams=[[pikachu], [charmander]],
            ruleset=ruleset
        )

        # --- 5. Run a Test Turn ---
        pika_action = pika_pokemon.moves[0] # Tackle
        char_action = char_pokemon.moves[0] # Scratch
        
        print(f"  Submitting actions: {pika_action.name} and {char_action.name}")
        
        # FIX: Submit actions as a dictionary mapping user_id to their action.
        # This is how the engine will know *who* is doing *what*.
        actions_to_submit = {
            pikachu.id: pika_action,
            charmander.id: char_action,
        }
        battle.submit_actions(actions_to_submit)
        
        log = battle.process_turn()
        
        print("  Processing turn...")
        
        # --- 6. Assert Results ---
        print("  Asserting results...")
        
        # Check that events actually happened
        self.assertGreater(len(log), 0)
        # Check that our ruleset correctly created DAMAGE events
        has_damage_event = any(e.event_type == "DAMAGE" for e in log)
        self.assertTrue(has_damage_event, "No 'DAMAGE' event was found in the log.")
        
        # Check that HP has *actually* decreased for both
        self.assertLess(pika_pokemon.current_hp, pika_initial_hp, "Pikachu's HP did not decrease.")
        self.assertLess(char_pokemon.current_hp, char_initial_hp, "Charmander's HP did not decrease.")
        
        print(f"  Pikachu HP: {pika_pokemon.current_hp} / {pika_initial_hp}")
        print(f"  Charmander HP: {char_pokemon.current_hp} / {char_initial_hp}")
        print("--- Test Complete ---")

# This allows running the test file directly
if __name__ == '__main__':
    unittest.main()


