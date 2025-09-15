"""
battledex_engine/interfaces.py

Defines the abstract base classes (ABCs) that form the contract between
the battle engine and a specific ruleset implementation (like rotomdex).

These interfaces ensure that the engine can remain completely agnostic
of any specific game's rules, allowing for maximum modularity.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, TYPE_CHECKING

# Use a forward reference for type hints to avoid circular imports.
if TYPE_CHECKING:
    from .state import BattleState
    from .event_queue import EventQueue, Event

class Combatant(ABC):
    """
    An interface representing a participant in a battle.
    A concrete implementation will hold all state for a single creature,
    such as its HP, stats, status conditions, and moves.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """A unique identifier for this combatant within the battle."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """
        Is this combatant currently the active one on its team?
        In a standard 1v1 battle, only one combatant is active at a time.
        """
        pass

class Action(ABC):
    """
    An interface representing a choice made by a combatant for a turn.
    Examples would be using a specific move, switching out, or using an item.
    """
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        The priority of the action, used for turn ordering.
        Higher numbers go first. Most standard moves have a priority of 0.
        Moves like "Quick Attack" have a priority of 1.
        """
        pass

class Ruleset(ABC):
    """
    An interface for a collection of game mechanics and event handlers.
    This is where the specific rules of a game (like Pokémon) are defined.
    The Battle engine is given a concrete implementation of this class
    and uses it to drive all game logic.
    """
    @abstractmethod
    def get_event_handlers(self) -> Dict[str, List[Callable[['Event', 'BattleState', 'EventQueue'], None]]]:
        """
        Returns a dictionary mapping event types to a list of handler functions.
        When the EventQueue processes an event, it will call all handler
        functions registered for that event's type.

        Example:
            return {
                "DAMAGE": [self.handle_damage_calculation],
                "FAINT": [self.handle_fainting_logic],
                "SWITCH_IN": [self.handle_entry_hazards]
            }
        """
        pass


