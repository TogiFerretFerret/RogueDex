import sys
import os
import random
import pygame

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battledex_engine.battle import Battle
from battledex_engine.interfaces import Action
from rotomdex.data_loader import load_pokemon_data, load_move_data, load_item_data
from rotomdex.factory import create_pokemon_from_data
from rotomdex.ruleset import PokemonRuleset
from roguedex_client.battle_visualizer import BattleVisualizer

class RogueDexClient:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RogueDex Battle Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

        # Game State
        self.running = True
        self.turn_logs = []
        
        # Initialize Battle
        self.init_battle()
        
        # Initialize Visualizer
        self.visualizer = BattleVisualizer(self.screen, self.font, self.combatant_map)

    def init_battle(self):
        print("Initializing Battle...")
        try:
            pokemon_data = load_pokemon_data()
            move_data = load_move_data()
            item_data = load_item_data()
        except Exception as e:
            print(f"Failed to load data: {e}")
            sys.exit(1)
            
        # Create Teams
        p1_name = "pikachu" if "pikachu" in pokemon_data else list(pokemon_data.keys())[0]
        p2_name = "charmander" if "charmander" in pokemon_data else list(pokemon_data.keys())[1]
        
        p1_moves = ["tackle", "thunder-shock"] 
        p2_moves = ["scratch", "ember"]
        
        # Create Combatants
        p1 = create_pokemon_from_data(p1_name, 5, p1_moves, pokemon_data, move_data, item_data, "player_1", is_active=True)
        p2 = create_pokemon_from_data(p2_name, 5, p2_moves, pokemon_data, move_data, item_data, "cpu_1", is_active=True)
        
        teams = [[p1], [p2]]
        
        # Create Ruleset
        self.combatant_map = {p1.id: p1, p2.id: p2}
        ruleset = PokemonRuleset(self.combatant_map)
        
        # Create Battle
        self.battle = Battle(teams, ruleset)
        
        print(f"Battle Started: {p1.species_name} vs {p2.species_name}")

    def process_turn(self):
        print(f"\n--- Turn {self.battle.state.turn_number + 1} ---")
        
        # 1. Choose Random Actions
        actions = {}
        for team in self.battle.state.teams:
            active_id = team.active_combatant_id
            combatant = self.combatant_map[active_id]
            
            # Simple AI: Pick a random move
            if combatant.moves:
                chosen_move = random.choice(combatant.moves)
                actions[active_id] = [chosen_move]
                # Log to console for debug
                # print(f"{combatant.species_name} chose {chosen_move.name}")
        
        # 2. Submit Actions
        self.battle.submit_actions(actions)
        
        # 3. Process Turn
        self.turn_logs = self.battle.process_turn()
        
        # Check game over (simplified)
        for c in self.combatant_map.values():
            if c.current_hp <= 0:
                print(f"{c.species_name} is defeated!")
                self.turn_logs.append(f"{c.species_name} is defeated!")

    def run(self):
        print("Press SPACE to simulate a turn.")
        while self.running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.process_turn()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

            # Draw
            self.visualizer.draw(self.battle.state, self.turn_logs)
            
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = RogueDexClient()
    app.run()