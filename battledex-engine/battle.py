"""
battledex_engine/battle.py

The main Battle class that orchestrates the entire simulation.
"""

from typing import List
from .state import BattleState
from .interfaces import Action, Ruleset
from .event_queue import EventQueue, Event

class Battle:
    """
    Manages a single battle from start to finish.
    """
    def __init__(self, teams: List[List['Combatant']], ruleset: Ruleset):
        # The Battle class will initialize the BattleState from the provided teams
        self.state = self._create_initial_state(teams)
        self._ruleset = ruleset
        self._event_queue = EventQueue(self._ruleset)

    def _create_initial_state(self, teams) -> BattleState:
        """Creates the initial BattleState from the combatant lists."""
        # This will be implemented to set up the initial turn 0 state.
        pass

    def submit_actions(self, actions: List[Action]):
        """
        Players submit their chosen actions for the turn through this method.
        """
        # The actions will be sorted by priority and used to generate
        # the initial events for the turn, which are added to the queue.
        pass

    def process_turn(self) -> List[Event]:
        """
        Processes the entire turn and returns the event log.
        """
        print(f"--- Processing Turn {self.state.turn_number} ---")
        log = self._event_queue.process_all(self.state)
        self.state.turn_number += 1
        return log

