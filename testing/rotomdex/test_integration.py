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

# Type hint for our concrete Pokemon class
# We can't import it directly due to test discovery paths,
# but we can use this for better type hints in the test.
try:
    from rotomdex.pokemon import Pokemon
except ImportError:
    # This is fine, we'll just use the Combatant interface
    Pokemon = Combatant 

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
        pika_pokemon: Pokemon = pikachu
        char_pokemon: Pokemon = charmander
        
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

    # --- Feature Checklist (To-Do) ---

    @unittest.skip("Feature not yet implemented in ruleset")
    def test_terastallization(self):
        """
        Tests that a Pokémon can Terastallize and that its
        move damage is correctly modified.
        """
        # 1. Create a Pikachu (Electric) and a Ogerpon (Grass)
        # 2. Give Pikachu a 'terastalize' action (will need new Action type)
        #    and set its Tera Type to 'Normal'
        # 3. Submit 'terastalize' for Pikachu and 'tackle' for Ogerpon
        # 4. Assert Pikachu's type is now 'Normal'
        # 5. On Turn 2, have Pikachu use Tackle (now STAB)
        # 6. Assert damage is calculated based on 'Normal' type
        pass

    @unittest.skip("Feature not yet implemented in ruleset")
    def test_mega_evolution(self):
        """
        Tests that a Pokémon can Mega Evolve and its stats
        and abilities change.
        """
        # 1. Create a Charizard (with 'charizardite-x')
        # 2. Submit a 'mega_evolve' action
        # 3. Process turn
        # 4. Assert Charizard's species is now 'charizard-mega-x'
        # 5. Assert Charizard's stats have been recalculated
        # 6. Assert Charizard's type is now Fire/Dragon
        pass

    @unittest.skip("Feature not yet implemented in ruleset")
    def test_z_move(self):
        """
        Tests that a Pokémon can use a Z-Move one time.
        """
        # 1. Create a Pikachu (with 'pikanium-z')
        # 2. Submit a 'z_move' action for 'volt-tackle'
        # 3. Process turn
        # 4. Assert that the 'catastropika' event was generated
        # 5. Assert target took massive damage
        # 6. On Turn 2, assert Pikachu can no longer use a Z-Move
        pass

    @unittest.skip("Feature not yet implemented in ruleset")
    def test_dynamax(self):
        """
        Tests that a Pokémon can Dynamax for 3 turns.
        """
        # 1. Create a Charizard
        # 2. Submit 'dynamax' action
        # 3. Assert Charizard's HP has doubled
        # 4. Assert its moves have been replaced with 'Max' moves
        # 5. Process 3 more turns
        # 6. Assert Charizard has reverted to normal
        pass

# This allows running the test file directly
if __name__ == '__main__':
    unittest.main()


