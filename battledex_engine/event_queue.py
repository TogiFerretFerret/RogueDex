"""
battledex_engine/event_queue.py

Contains the core logic for the event processing loop, which is the heart
of the deterministic simulation.
"""

import collections
from typing import List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

# Use a forward reference for type hints to avoid circular imports.
# The actual classes are defined in other modules.
if TYPE_CHECKING:
    from .state import BattleState
    from .interfaces import Ruleset

@dataclass
class Event:
    """
    A data structure representing a single thing that happened in a battle.
    Events are the primary way that the battle state is modified.
    """
    event_type: str  # e.g., "DAMAGE", "STATUS_APPLIED", "STAT_CHANGE"
    payload: Dict[str, Any]

class EventQueue:
    """
    Manages the processing of events in a battle turn.

    This class is the core of the engine. It processes events one by one,
    calling the appropriate handler functions provided by a specific game
    ruleset. These handlers are responsible for modifying the battle state
    and can, in turn, add new events to the queue to be processed.
    """
    def __init__(self, ruleset: 'Ruleset'):
        self._queue: collections.deque[Event] = collections.deque()
        self._ruleset = ruleset
        # Cache the handlers from the ruleset for performance. This dictionary
        # maps an event type string to a list of functions that should be
        # called when that event type is processed.
        self._handlers = self._ruleset.get_event_handlers()

    def add(self, event: Event, to_front: bool = False):
        """
        Adds a new event to be processed.

        Args:
            event: The Event object to add to the queue.
            to_front: If True, the event is added to the beginning of the
                      queue, to be processed next. This is useful for
                      reactions to another event (e.g., an ability
                      triggering when damage is taken).
        """
        if to_front:
            self._queue.appendleft(event)
        else:
            self._queue.append(event)

    def process_all(self, state: 'BattleState') -> List[Event]:
        """
        Processes all events in the queue until it is empty. This method
        drives the entire turn forward.

        Args:
            state: The current BattleState object, which will be modified
                   by the event handlers.

        Returns:
            A log of all events that were processed, in order. This log
            can be used by the client to display animations.
        """
        event_log: List[Event] = []
        while self._queue:
            event = self._queue.popleft()
            event_log.append(event)

            # Look up the handlers registered for this specific event type.
            # If no handlers are found, the event still gets logged, but
            # it has no effect on the battle state.
            event_handlers = self._handlers.get(event.event_type, [])
            
            for handler in event_handlers:
                # The handler function is responsible for all game logic.
                # It receives the event, the current state, and a reference
                # to this queue, allowing it to add new, subsequent events.
                handler(event, state, self)
        
        return event_log


