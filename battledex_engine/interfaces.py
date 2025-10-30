"""
battledex-engine/interfaces.py

Defines the abstract base classes (ABCs) that form the contract between
the battle engine and a specific ruleset implementation (like rotomdex).

FIX: Added 'SpecialAction' and new properties to 'Combatant'
for items and Terastalization. We also now import Item from
the correct 'battledex_engine' package.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, TYPE_CHECKING, Optional

# Use a forward reference for type hints to avoid circular imports.
if TYPE_CHECKING:
    from .state import BattleState
    from .event_queue import EventQueue, Event
    
# Import the generalized Item class from its new location
from .item import Item

class Combatant(ABC):
    """
    An interface representing a participant in a battle.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """A unique identifier for this combatant within the battle."""
        pass

    @property
    @abstractabstractmethod
    def is_active(self) -> bool:
        """Is this combatant currently the active one on its team?"""
        pass
        
    # --- NEW PROPERTIES FOR ITEMS ---
    @property
    @abstractmethod
    def held_item(self) -> Optional[Item]:
        """The item this combatant is currently holding."""
        pass

    # --- NEW PROPERTIES FOR TERASTALLIZATION ---
    @property
    @abstractmethod
    def tera_type(self) -> str:
        """The Terastal type of this Pokémon."""
        pass
        
    @property
    @abstractmethod
    def has_terastallized(self) -> bool:
        """True if this Pokémon has already Terastallized."""
        pass
        
    @property
    @abstractmethod
    def current_types(self) -> List[str]:
        """The current in-battle types (can be changed by Tera)."""
        pass

class Action(ABC):
    """
    An interface representing a choice made by a combatant for a turn.
    """
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        The priority of the action, used for turn ordering.
        """
        pass

# --- NEW ACTION TYPE FOR SPECIAL MECHANICS ---
class SpecialAction(Action):
    """
    An action that represents a special mechanic, like
    Terastallizing, Mega Evolving, etc.
    """
    def __init__(self, kind: str, priority: int = 100):
        """
        Args:
            kind (str): The type of special action, e.g., "terastalize"
            priority (int): Special actions usually have very high
                            priority to ensure they happen first.
        """
        self._kind = kind
        self._priority = priority
        
    @property
    def kind(self) -> str:
        return self._kind
        
    @property
    def priority(self) -> int:
        return self._priority
        

class Ruleset(ABC):
    """
    An interface for a collection of game mechanics and event handlers.
    """
    @abstractmethod
    def get_event_handlers(self) -> Dict[str, List[Callable[['Event', 'BattleState', 'EventQueue'], None]]]:
        """
        Returns a dictionary mapping event types to a list of handler functions.
        """
        pass

    # NEW: Added a property to access the combatant map
    @property
    @abstractmethod
    def combatant_map(self) -> Dict[str, Combatant]:
        """A map of combatant IDs to their objects."""
        pass

