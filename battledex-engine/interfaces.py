"""
battledex_engine/interfaces.py

Defines the abstract base classes (ABCs) that form the contract between
the battle engine and a specific ruleset implementation (like rotomdex).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Combatant(ABC):
    """
    An interface representing a participant in a battle.
    A concrete implementation will hold all state for a single creature.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """A unique identifier for this combatant in the battle."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Is this combatant currently the active one on its team?"""
        pass

class Action(ABC):
    """
    An interface representing a choice made by a combatant for a turn.
    """
    @property
    @abstractmethod
    def priority(self) -> int:
        """The priority of the action, used for turn ordering."""
        pass

class Ruleset(ABC):
    """
    An interface for a collection of game mechanics and event handlers.
    This is where the specific rules of a game (like Pokémon) are defined.
    """
    @abstractmethod
    def get_event_handlers(self) -> Dict[str, List[callable]]:
        """
        Returns a dictionary mapping event types to a list of handler functions.
        Example: {"DAMAGE": [handle_ability_effect, handle_item_effect]}
        """
        pass

