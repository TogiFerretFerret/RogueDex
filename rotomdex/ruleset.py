"""
rotomdex/ruleset.py

This is the concrete implementation of the Ruleset interface.
This is the "brain" that plugs into the battledex-engine and
defines all Pokémon-specific game logic.

FIX: This version now imports the type chart from the data_loader
instead of a hardcoded file.
"""

from typing import Dict, List, Any, Callable
from battledex_engine.interfaces import Ruleset, Combatant
from battledex_engine.state import BattleState
from battledex_engine.event_queue import EventQueue, Event

from .pokemon import Pokemon
from .move import Move
# FIX: Import the new data loader function
from .data_loader import load_type_data 

class PokemonRuleset(Ruleset):
    """
    Implements all game logic for a Pokémon battle.
    """
    def __init__(self, combatant_map: Dict[str, Combatant]):
        """
        Args:
            combatant_map: A "master list" mapping a Combatant's
                           ID to its full object.
        """
        self._combatant_map = combatant_map
        # FIX: Load the type chart from the JSON file at init
        # This assumes rotomdex/data/types.json exists!
        try:
            self.TYPE_CHART = load_type_data()
        except FileNotFoundError:
            print("="*50)
            print("FATAL ERROR: rotomdex/data/types.json not found.")
            print("Please run the API importer first:")
            print("python rotomdex/api_importer.py")
            print("="*50)
            raise

    @property
    def combatant_map(self) -> Dict[str, Combatant]:
        """A dictionary mapping combatant IDs to their objects."""
        return self._combatant_map

    def get_event_handlers(self) -> Dict[str, List[Callable[[Event, BattleState, EventQueue], None]]]:
        """
        Returns the dictionary that maps event types to the
        functions that should handle them.
        """
        return {
            "ACTION_REQUEST": [self._handle_action_request],
            "DAMAGE": [self._handle_damage],
            "FAINT": [self._handle_faint],
        }

    def _find_target_id(self, user_id: str, state: BattleState) -> str | None:
        """
        Simple helper for 1v1 battles to find the opponent.
        """
        for team in state.teams:
            if team.active_combatant_id == user_id:
                continue
            return team.active_combatant_id
        return None

    def _get_effectiveness(self, move_type: str, target_types: List[str]) -> float:
        """
        Calculates the type effectiveness multiplier by using the loaded chart.
        """
        if not move_type or not target_types:
            return 1.0
            
        # Get the offensive chart for the move's type
        # FIX: Use the loaded TYPE_CHART from the instance
        offense_chart = self.TYPE_CHART.get(move_type.lower())
        if not offense_chart:
            # This handles "shadow" or "unknown" types from the API
            print(f"Warning: Unknown move type '{move_type}'. Defaulting to 1.0x.")
            return 1.0 # Default for unknown types

        multiplier = 1.0
        for def_type in target_types:
            multiplier *= offense_chart.get(def_type.lower(), 1.0)
            
        return multiplier

    # --- Event Handler Implementations ---

    def _handle_action_request(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles the "ACTION_REQUEST" event created by the Battle class.
        This is where we determine what the action *does*.
        """
        action = event.payload.get("action")
        user_id = event.payload.get("user_id")

        if not isinstance(action, Move) or not user_id:
            return

        move: Move = action
        user = self._combatant_map.get(user_id)
        target_id = self._find_target_id(user_id, state)
        target = self._combatant_map.get(target_id)

        if not user or not target or not isinstance(user, Pokemon) or not isinstance(target, Pokemon):
            print(f"Ruleset Error: Could not find user {user_id} or target {target_id}")
            return

        print(f"Ruleset: {user.species_name} used {move.name} on {target.species_name}!")
        
        # --- 1. Handle Status Moves (no damage) ---
        if move.category.lower() == "status":
            print(f"Ruleset: {move.name} is a Status move. (Logic not implemented)")
            # In a real game, you'd add events for stat changes, status, etc.
            return

        # --- 2. Calculate Offensive Stat (with Item logic) ---
        # This is the pattern for manual item logic.
        # We check the item's id_name and manually apply the logic.
        
        offensive_stat = 0
        if move.category.lower() == "physical":
            offensive_stat = user.stats.get("attack", 0)
            # Example: Choice Band
            if user.held_item and user.held_item.id_name == "choice-band":
                print("Ruleset: Choice Band boosts Attack!")
                offensive_stat *= 1.5
                
        elif move.category.lower() == "special":
            offensive_stat = user.stats.get("sp_attack", 0)
            # Example: Light Ball
            if user.held_item and user.held_item.id_name == "light-ball" and user.species_name == "Pikachu":
                 print("Ruleset: Pikachu's Light Ball flared!")
                 offensive_stat *= 2
        
    def _calculate_damage(self, user: Pokemon, target: Pokemon, move: Move, offensive_stat: int) -> int:
        """
        Calculates damage using the standard Gen 3+ formula:
        Damage = ((((2 * Level / 5 + 2) * Power * A / D) / 50) + 2) * Modifier
        """
        import random
        
        if move.power is None or move.power == 0:
            return 0

        # Get defensive stat
        defensive_stat = 0
        if move.category.lower() == "physical":
            defensive_stat = target.stats.get("defense", 1) 
        elif move.category.lower() == "special":
            defensive_stat = target.stats.get("sp_defense", 1)
        
        # Avoid division by zero
        defensive_stat = max(1, defensive_stat)

        # 1. Base Damage Calculation
        level_factor = (2 * user.level / 5) + 2
        raw_damage = (level_factor * move.power * (offensive_stat / defensive_stat)) / 50 + 2
        
        # 2. Modifiers
        modifier = 1.0
        
        # Type Effectiveness
        effectiveness = self._get_effectiveness(move.move_type, target.current_types)
        modifier *= effectiveness
        
        if effectiveness > 1.5:
            print("Ruleset: It's super effective!")
        elif effectiveness < 0.8:
            print("Ruleset: It's not very effective...")
        elif effectiveness == 0:
            print(f"Ruleset: It doesn't affect {target.species_name}...")
            return 0

        # STAB (Same Type Attack Bonus)
        # Check against current types (which handles Terastallization automatically)
        if move.move_type and move.move_type.lower() in [t.lower() for t in user.current_types]:
            print("Ruleset: STAB bonus applied!")
            modifier *= 1.5

        # Random Variance (0.85 to 1.00)
        random_factor = random.uniform(0.85, 1.00)
        modifier *= random_factor
        
        final_damage = int(raw_damage * modifier)
        
        # Ensure at least 1 damage if effectiveness > 0
        return max(1, final_damage)

    def _handle_action_request(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles the "ACTION_REQUEST" event created by the Battle class.
        This is where we determine what the action *does*.
        """
        action = event.payload.get("action")
        user_id = event.payload.get("user_id")

        if not isinstance(action, Move) or not user_id:
            return

        move: Move = action
        user = self._combatant_map.get(user_id)
        target_id = self._find_target_id(user_id, state)
        target = self._combatant_map.get(target_id)

        if not user or not target or not isinstance(user, Pokemon) or not isinstance(target, Pokemon):
            print(f"Ruleset Error: Could not find user {user_id} or target {target_id}")
            return

        print(f"Ruleset: {user.species_name} used {move.name} on {target.species_name}!")
        
        # --- 1. Handle Status Moves (no damage) ---
        if move.category.lower() == "status":
            print(f"Ruleset: {move.name} is a Status move. (Logic not implemented)")
            # In a real game, you'd add events for stat changes, status, etc.
            return

        # --- 2. Calculate Offensive Stat (with Item logic) ---
        # This is the pattern for manual item logic.
        # We check the item's id_name and manually apply the logic.
        
        offensive_stat = 0
        if move.category.lower() == "physical":
            offensive_stat = user.stats.get("attack", 0)
            # Example: Choice Band
            if user.held_item and user.held_item.id_name == "choice-band":
                print("Ruleset: Choice Band boosts Attack!")
                offensive_stat *= 1.5
                
        elif move.category.lower() == "special":
            offensive_stat = user.stats.get("sp_attack", 0)
            # Example: Light Ball
            if user.held_item and user.held_item.id_name == "light-ball" and user.species_name == "Pikachu":
                 print("Ruleset: Pikachu's Light Ball flared!")
                 offensive_stat *= 2
        
        # --- 3. Calculate Damage ---
        damage = self._calculate_damage(user, target, move, offensive_stat)
        
        if damage == 0:
            return

        # --- 4. Create Damage Event ---
        damage_event = Event(
            event_type="DAMAGE",
            payload={
                "target_id": target.id,
                "damage": damage,
                "move_name": move.name
            }
        )
        queue.add(damage_event)

    def _handle_damage(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles applying damage to a Pokémon.
        """
        target_id = event.payload.get("target_id")
        damage = event.payload.get("damage", 0)

        target = self._combatant_map.get(target_id)
        if not target or not isinstance(target, Pokemon):
            return

        target.current_hp -= damage
        print(f"Ruleset: {target.species_name} took {damage} damage! Remaining HP: {target.current_hp}")

        if target.current_hp <= 0:
            target.current_hp = 0
            faint_event = Event(
                event_type="FAINT",
                payload={"target_id": target.id}
            )
            queue.add(faint_event, to_front=True) 

    def _handle_faint(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles a Pokémon fainting.
        """
        target_id = event.payload.get("target_id")
        target = self._combatant_map.get(target_id)
        if not target:
            return

        print(f"Ruleset: {target.species_name} fainted!")
        # In a real game, you would add events here to
        # check for a winner or force the player to switch.


