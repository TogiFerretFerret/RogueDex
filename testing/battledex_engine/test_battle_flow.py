"""
testing/battledex_engine/test_battle_flow.py

Unit tests for the complete battledex_engine flow.
"""

import unittest
import sys
import os
from typing import List, Dict, Any, Callable, Optional

# --- Add project root to path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from battledex_engine.battle import Battle
from battledex_engine.state import BattleState, TeamState, CombatantState
from battledex_engine.interfaces import Action, Ruleset, Combatant, SpecialAction
from battledex_engine.event_queue import EventQueue, Event
from battledex_engine.item import Item

# --- Mock Implementations for Testing ---

class MockCombatant(Combatant):
    """A mock combatant that implements the full Combatant interface."""
    def __init__(self, c_id: str, active: bool = False):
        self._id = c_id
        self._is_active = active
        self._held_item: Optional[Item] = None
        self._tera_type: str = "normal"
        self._has_terastallized: bool = False
        self._current_types: List[str] = ["normal"]

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_active(self) -> bool:
        return self._is_active
        
    # --- FIX: Implement new abstract properties ---
    @property
    def held_item(self) -> Optional[Item]:
        return self._held_item

    @property
    def tera_type(self) -> str:
        return self._tera_type
        
    @property
    def has_terastallized(self) -> bool:
        return self._has_terastallized
        
    @property
    def current_types(self) -> List[str]:
        return self._current_types

class MockAction(Action):
    """A mock action for testing purposes."""
    def __init__(self, p: int, name: str, user_id: str, target_id: str):
        self._priority = p
        self.name = name
        self.user_id = user_id
        self.target_id = target_id

    @property
    def priority(self) -> int:
        return self._priority

class MockRuleset(Ruleset):
    """A simplified ruleset for testing the event flow."""

    def __init__(self, combatants: List[MockCombatant]):
        # FIX: Store HP here, as CombatantState is just data
        self.hp: Dict[str, int] = {}
        # FIX: Implement combatant_map
        self._combatant_map = {c.id: c for c in combatants}

    @property
    def combatant_map(self) -> Dict[str, Combatant]:
        return self._combatant_map

    def handle_action_request(self, event: Event, state: BattleState, queue: EventQueue):
        """When an action is requested, create a DAMAGE event."""
        action = event.payload['action']
        
        # Handle both mock and special actions
        if isinstance(action, MockAction):
            print(f"Handler: Processing action '{action.name}'")
            damage_event = Event(
                event_type="DAMAGE",
                payload={"target_id": action.target_id, "amount": 10}
            )
            queue.add(damage_event)
        elif isinstance(action, SpecialAction):
            print(f"Handler: Processing special action '{action.kind}'")
            # In a real ruleset, this would add more events
            pass

    def handle_damage(self, event: Event, state: BattleState, queue: EventQueue):
        """When a damage event occurs, reduce the target's HP."""
        target_id = event.payload['target_id']
        amount = event.payload['amount']
        print(f"Handler: Applying {amount} damage to {target_id}")
        
        # FIX: Modify HP stored in the ruleset, not the state object
        if target_id in self.hp:
            self.hp[target_id] -= amount
        else:
            print(f"Handler Error: Unknown combatant {target_id} in HP map.")

    def get_event_handlers(self) -> Dict[str, List[Callable]]:
        return {
            "ACTION_REQUEST": [self.handle_action_request],
            "DAMAGE": [self.handle_damage],
        }

# --- Test Case ---

class TestBattleFlow(unittest.TestCase):
    """
    Tests the full process of submitting actions and processing a turn.
    """

    def test_turn_processing_flow(self):
        """
        Tests that actions are submitted, converted to events, and processed
        by the ruleset to correctly modify the battle state.
        """
        print("\nRunning test_turn_processing_flow...")

        # 1. Setup: Create combatants, teams, and the battle itself
        p1 = MockCombatant(c_id="player1_char", active=True)
        p2 = MockCombatant(c_id="player2_squirt", active=True)
        
        ruleset = MockRuleset(combatants=[p1, p2])
        
        battle = Battle(teams=[[p1], [p2]], ruleset=ruleset)
        
        # Manually set the HP for our test state
        initial_hp = 100
        # FIX: Store HP in the ruleset's mock HP tracker
        ruleset.hp[p1.id] = initial_hp
        ruleset.hp[p2.id] = initial_hp

        # 2. Action Submission: Create and submit actions for the turn
        action = MockAction(p=0, name="Tackle", user_id=p1.id, target_id=p2.id)
        
        # FIX: Submit actions as a dictionary
        actions_map = {p1.id: [action]}
        battle.submit_actions(actions_map)

        # 3. Processing: Run the turn
        event_log = battle.process_turn()

        # 4. Assertions: Verify the outcome
        self.assertEqual(len(event_log), 2, "Should have processed two events (ACTION_REQUEST and DAMAGE).")
        self.assertEqual(event_log[0].event_type, "ACTION_REQUEST")
        self.assertEqual(event_log[1].event_type, "DAMAGE")
        
        # FIX: Check the HP in the ruleset's mock HP tracker
        expected_hp = initial_hp - 10
        self.assertEqual(ruleset.hp[p2.id], expected_hp, 
                         f"Target's HP should be reduced to {expected_hp}.")
        self.assertEqual(ruleset.hp[p1.id], initial_hp,
                         "Attacker's HP should not have changed.")
        print("Turn processing flow test successful.")


if __name__ == '__main__':
    unittest.main()

