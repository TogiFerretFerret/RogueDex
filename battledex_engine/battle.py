"""
battledex_engine/battle.py

The main Battle class that orchestrates the entire simulation.

FIX: `submit_actions` now accepts a dictionary of {user_id: action}
to correctly link actions to their users.
"""

from typing import List, Dict, cast
from .state import BattleState, TeamState, CombatantState
from .interfaces import Action, Ruleset, Combatant
from .event_queue import EventQueue, Event

class Battle:
    """
    Manages a single battle from start to finish.
    """
    def __init__(self, teams: List[List[Combatant]], ruleset: Ruleset):
        """
        Initializes a battle with the given teams and ruleset.

        Args:
            teams: A list of teams. Each team is a list of Combatant objects.
            ruleset: The ruleset implementation to use for this battle.
        """
        self.state = self._create_initial_state(teams)
        self._ruleset = ruleset
        self._event_queue = EventQueue(self._ruleset)

    def _create_initial_state(self, teams: List[List[Combatant]]) -> BattleState:
        """Creates the initial BattleState from the combatant lists."""
        team_states: List[TeamState] = []
        for team_combatants in teams:
            combatant_states: List[CombatantState] = []
            active_combatant_id: str | None = None
            for combatant in team_combatants:
                combatant_states.append(CombatantState(id=combatant.id))
                if combatant.is_active:
                    # We assume only one combatant is active per team at the start.
                    active_combatant_id = combatant.id

            if not active_combatant_id:
                raise ValueError("A team was provided with no active combatant.")

            team_states.append(
                TeamState(
                    combatants=combatant_states,
                    active_combatant_id=active_combatant_id
                )
            )

        return BattleState(teams=team_states)

    def submit_actions(self, actions_map: Dict[str, List[Action]]):
        """
        Players submit their chosen actions for the turn through this method.
        
        Args:
            actions_map: A dictionary mapping combatant_id to a *list*
                         of their chosen Action objects.
        """
        # Create a list of (user_id, action_list) tuples
        action_pairs = []
        for user_id, action_list in actions_map.items():
            # In a real game, you'd verify that user_id is allowed
            # to make a move this turn.
            action_pairs.append((user_id, action_list))

        # Filter out empty action lists and sort actions by their priority value.
        valid_action_pairs = []
        for user_id, action_list in action_pairs:
            if action_list:
                valid_action_pairs.append((user_id, action_list))
        
        # Sort by the priority of the first action in the list.
        sorted_pairs = sorted(valid_action_pairs, key=lambda pair: pair[1][0].priority, reverse=True)

        for user_id, action_list in sorted_pairs:
            # Create a generic event for each action.
            # We currently process all actions in the list for that user.
            for action in action_list:
                initial_event = Event(
                    event_type="ACTION_REQUEST",
                    payload={
                        "action": action,
                        "user_id": user_id
                    }
                )
                self._event_queue.add(initial_event)

    def process_turn(self) -> List[Event]:
        """
        Processes the entire turn by running the event queue until it is empty.
        Increments the turn number after processing.

        Returns:
            A log of all events that were processed during the turn.
        """
        print(f"--- Processing Turn {self.state.turn_number + 1} ---")
        log = self._event_queue.process_all(self.state)
        self.state.turn_number += 1
        return log



