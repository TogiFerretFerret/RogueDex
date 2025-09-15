"""
battledex_engine/event_queue.py

Contains the core logic for the event processing loop, which is the heart
of the deterministic simulation.
"""

import collections
from typing import List, Dict, Any, Callable
from .state import BattleState
from .interfaces import Ruleset

@dataclass
class Event:
    """A data structure representing a single thing that happened."""
    event_type: str  # e.g., "DAMAGE", "STATUS_APPLIED", "STAT_CHANGE"
    payload: Dict[str, Any]

class EventQueue:
    """
    Manages the processing of events in a battle turn.
    """
    def __init__(self, ruleset: Ruleset):
        self._queue = collections.deque()
        self._ruleset = ruleset
        # Cache the handlers for performance
        self._handlers = self._ruleset.get_event_handlers()

    def add(self, event: Event, to_front: bool = False):
        """Adds a new event to be processed."""
        if to_front:
            self._queue.appendleft(event)
        else:
            self._queue.append(event)

    def process_all(self, state: BattleState) -> List[Event]:
        """
        Processes all events in the queue until it is empty.

        Returns:
            A log of all events that were processed, in order.
        """
        event_log = []
        while self._queue:
            event = self._queue.popleft()
            event_log.append(event)

            # --- Core Logic ---
            # 1. Apply the event's direct effect to the battle state.
            #    (This will be implemented in the Battle class).

            # 2. Trigger any registered handlers from the ruleset.
            if event.event_type in self._handlers:
                for handler in self._handlers[event.event_type]:
                    # Handlers can add new events to the front of the queue
                    # to react to the current event.
                    handler(event, state, self)
        
        return event_log

