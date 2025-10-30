"""
rotomdex/ruleset.py

This is the concrete implementation of the Ruleset interface.
This is the "brain" that plugs into the battledex-engine and
defines all Pokémon-specific game logic.
"""

from typing import Dict, List, Any, Callable
from battledex_engine.interfaces import Ruleset, Combatant
from battledex_engine.state import BattleState
from battledex_engine.event_queue import EventQueue, Event

from .pokemon import Pokemon
from .move import Move

class PokemonRuleset(Ruleset):
    """
    Implements all game logic for a Pokémon battle.
    """
    def __init__(self, combatant_map: Dict[str, Combatant]):
        """
        Args:
            combatant_map: A "master list" mapping a Combatant's
                           ID to its full object. This is necessary
                           so our handlers can retrieve the full
                           Pokemon object from just an ID.
        """
        self.combatant_map = combatant_map

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

    # --- Event Handler Implementations ---

    def _handle_action_request(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles the "ACTION_REQUEST" event created by the Battle class.
        This is where we determine what the action *does*.
        """
        action = event.payload.get("action")
        
        # We only know how to handle Moves right now
        if not isinstance(action, Move):
            return

        move: Move = action
        
        # In a real game, we'd get the user/target from the event payload.
        # For this simple test, we'll assume Team 0 attacks Team 1.
        user_id = state.teams[0].active_combatant_id
        target_id = state.teams[1].active_combatant_id
        
        user = self.combatant_map.get(user_id)
        target = self.combatant_map.get(target_id)
        
        if not user or not target:
            print(f"Ruleset Error: Could not find user {user_id} or target {target_id}")
            return
            
        print(f"Ruleset: {user.species_name} used {move.name} on {target.species_name}!")
        
        # --- Basic Damage Calculation ---
        # This is where your Terastal, Mega, etc. logic would go.
        damage = 10 # A placeholder
        if move.power:
            # A very simple, non-Poké formula for testing
            damage = move.power + user.stats.get("attack", 0) // 5
        
        # Create a new "DAMAGE" event
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
        
        target = self.combatant_map.get(target_id)
        if not target:
            return
            
        target.current_hp -= damage
        print(f"Ruleset: {target.species_name} took {damage} damage! Remaining HP: {target.current_hp}")
        
        if target.current_hp <= 0:
            target.current_hp = 0
            # Create a "FAINT" event
            faint_event = Event(
                event_type="FAINT",
                payload={"target_id": target.id}
            )
            queue.add(faint_event, to_front=True) # Fainting happens immediately

    def _handle_faint(self, event: Event, state: BattleState, queue: EventQueue):
        """
        Handles a Pokémon fainting.
        """
        target_id = event.payload.get("target_id")
        target = self.combatant_map.get(target_id)
        if not target:
            return
        
        print(f"Ruleset: {target.species_name} fainted!")
        # In a real game, you would add events here to
        # check for a winner or force the player to switch.

