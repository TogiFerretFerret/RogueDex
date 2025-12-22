import sys
import os
import random
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import AmbientLight, DirectionalLight, Vec4, TextNode

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battledex_engine.battle import Battle
from battledex_engine.interfaces import Action
from rotomdex.data_loader import load_pokemon_data, load_move_data, load_item_data
from rotomdex.factory import create_pokemon_from_data
from rotomdex.ruleset import PokemonRuleset
from roguedex_client.battle_visualizer import BattleVisualizer

class RogueDexClient(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Basic Scene Setup
        self.setup_lighting()
        self.setup_camera()
        
        # Initialize Game Logic
        self.init_battle()
        
        # Initialize Visualizer
        self.visualizer = BattleVisualizer(self)
        self.visualizer.update(self.battle.state)
        
        # Start Battle Loop Task
        self.taskMgr.doMethodLater(2.0, self.game_loop, "GameLoopTask")
        
        print("RogueDex Client Initialized")

    def setup_lighting(self):
        ambient = AmbientLight('ambient')
        ambient.setColor(Vec4(0.5, 0.5, 0.5, 1))
        ambient_node = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_node)
        
        directional = DirectionalLight('directional')
        directional.setColor(Vec4(0.8, 0.8, 0.8, 1))
        directional_node = self.render.attachNewNode(directional)
        directional_node.setHpr(0, -60, 0)
        self.render.setLight(directional_node)

    def setup_camera(self):
        self.disableMouse()
        self.camera.setPos(0, -40, 20)
        self.camera.lookAt(0, 0, 0)

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
        # We'll pick two random pokemon if specific ones aren't guaranteed, 
        # but let's try some starters.
        p1_name = "pikachu" if "pikachu" in pokemon_data else list(pokemon_data.keys())[0]
        p2_name = "charmander" if "charmander" in pokemon_data else list(pokemon_data.keys())[1]
        
        p1_moves = ["tackle", "thundershock"] # Simplified
        p2_moves = ["scratch", "ember"]
        
        # Create Combatants
        p1 = create_pokemon_from_data(p1_name, 5, p1_moves, pokemon_data, move_data, item_data, "player_1", is_active=True)
        p2 = create_pokemon_from_data(p2_name, 5, p2_moves, pokemon_data, move_data, item_data, "cpu_1", is_active=True)
        
        teams = [[p1], [p2]]
        
        # Create Ruleset
        combatant_map = {p1.id: p1, p2.id: p2}
        ruleset = PokemonRuleset(combatant_map)
        
        # Create Battle
        self.battle = Battle(teams, ruleset)
        self.combatant_map = combatant_map # Keep reference for easy access
        
        print(f"Battle Started: {p1.species_name} vs {p2.species_name}")

    def game_loop(self, task):
        # Simulate a turn
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
                print(f"{combatant.species_name} chose {chosen_move.name}")
            else:
                print(f"{combatant.species_name} has no moves!")

        # 2. Submit Actions
        self.battle.submit_actions(actions)
        
        # 3. Process Turn
        logs = self.battle.process_turn()
        
        # 4. Update Visualizer
        self.visualizer.update(self.battle.state)
        
        # Check for faint/game over (simplified)
        for c in self.combatant_map.values():
            if c.current_hp <= 0:
                print(f"{c.species_name} is defeated!")
                # For demo, just reset or stop
                # return Task.done
        
        return Task.again

if __name__ == "__main__":
    app = RogueDexClient()
    app.run()