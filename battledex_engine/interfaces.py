"""
battledex_engine/interfaces.py

Defines the core abstract interfaces for the battledex engine:
- Action: A move or other action a combatant can take.
- Combatant: The entity that performs actions (e.g., a Pokemon).
- Ruleset: The "brain" of the simulation, defining all game logic.
"""

from abc import ABC, abstractmethod, abstractproperty
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

# We'll import these later, but define the types here for hinting
class BattleState: pass
class EventQueue: pass
class Event: pass
class Item: pass


@dataclass
class Action(ABC):
    """
    Abstract Base Class for any action a combatant can perform.
    e.g., a Move, using an Item, switching out.
    """
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        The priority of the action. Higher values go first.
        (e.g., Quick Attack = 1, regular moves = 0, switching = 6)
        """
        pass


@dataclass
class SpecialAction(Action):
    """A simple, concrete implementation for special battle actions."""
    kind: str  # e.g., "switch", "terastalize"
    _priority: int = 0
    
    @property
    def priority(self) -> int:
        return self._priority


@dataclass
class Combatant(ABC):
    """
    Abstract Base Class for a combatant.
    e.g., a Pokemon, a Final Fantasy character, etc.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """A unique instance ID for this combatant."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Whether this combatant is currently active in battle."""
        pass
        
    # --- New Properties for Tera/Items ---

    @property
    @abstractmethod
    def held_item(self) -> Optional[Item]:
        """The item this combatant is holding."""
        pass
        
    @property
    @abstractmethod
    def current_types(self) -> List[str]:
        """The combatant's current types (can be changed by effects)."""
        pass
        
    @property
    @abstractmethod
    def tera_type(self) -> str:
        """The combatant's Terastal type."""
        pass
        
    @property
    @abstractmethod
    def has_terastallized(self) -> bool:
        """Whether the combatant has already Terastallized."""
        pass


class Ruleset(ABC):
    """
    Abstract Base Class for a game's ruleset.
    This is the "brain" that contains all game-specific logic.
    """
    
    @abstractmethod
    def get_event_handlers(self) -> Dict[str, List[Callable[[Event, BattleState, EventQueue], None]]]:
        """
        Returns a dictionary mapping event types (e.g., "DAMAGE")
        to a list of functions that should handle that event.
        """
        pass

    # FIX: Add an abstract property for the combatant map.
    # This is necessary for the engine to find combatants by ID.
    @property
    @abstractmethod
    def combatant_map(self) -> Dict[str, Combatant]:
        """A dictionary mapping combatant IDs to their objects."""
        pass
