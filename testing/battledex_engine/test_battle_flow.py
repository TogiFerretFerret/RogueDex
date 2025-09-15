"""
testing/battledex_engine/test_battle_flow.py

Unit tests for the complete battledex_engine flow.
"""

import unittest
import sys
import os
from typing import List, Dict, Any, Callable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

from battledex_engine.battle import Battle
from battledex_engine.state import BattleState, TeamState, CombatantState
from battledex_engine.interfaces import Action, Ruleset, Combatant
from battledex_engine.event_queue import EventQueue, Event

# --- Mock Implementations for Testing ---

class MockCombatant(Combatant):
    """A mock combatant for testing purposes."""
    def __init__(self, c_id: str, active: bool = False):
        self._id = c_id
        self._is_active = active

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_active(self) -> bool:
        return self._is_active

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

    def handle_action_request(self, event: Event, state: BattleState, queue: EventQueue):
        """When an action is requested, create a DAMAGE event."""
        action = event.payload['action']
        print(f"Handler: Processing action '{action.name}'")
        damage_event = Event(
            event_type="DAMAGE",
            payload={"target_id": action.target_id, "amount": 10}
        )
        queue.add(damage_event)

    def handle_damage(self, event: Event, state: BattleState, queue: EventQueue):
        """When a damage event occurs, reduce the target's HP."""
        target_id = event.payload['target_id']
        amount = event.payload['amount']
        print(f"Handler: Applying {amount} damage to {target_id}")
        for team in state.teams:
            for combatant in team.combatants:
                if combatant.id == target_id:
                    combatant.current_hp -= amount
                    return

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
        
        ruleset = MockRuleset()
        
        battle = Battle(teams=[[p1], [p2]], ruleset=ruleset)
        
        # Manually set the HP for our test state. In a real game,
        # the ruleset would do this on a BATTLE_START event.
        initial_hp = 100
        for team in battle.state.teams:
            for cs in team.combatants:
                cs.current_hp = initial_hp

        # 2. Action Submission: Create and submit actions for the turn
        action = MockAction(p=0, name="Tackle", user_id=p1.id, target_id=p2.id)
        battle.submit_actions([action])

        # 3. Processing: Run the turn
        event_log = battle.process_turn()

        # 4. Assertions: Verify the outcome
        self.assertEqual(len(event_log), 2, "Should have processed two events (ACTION_REQUEST and DAMAGE).")
        self.assertEqual(event_log[0].event_type, "ACTION_REQUEST")
        self.assertEqual(event_log[1].event_type, "DAMAGE")
        
        # Find the state of the target (p2)
        p2_state = next(c for team in battle.state.teams for c in team.combatants if c.id == p2.id)
        
        expected_hp = initial_hp - 10
        self.assertEqual(p2_state.current_hp, expected_hp, 
                         f"Target's HP should be reduced to {expected_hp}.")
        print("Turn processing flow test successful.")


if __name__ == '__main__':
    unittest.main()


