"""
rotomdex/pokemon.py

Defines the concrete implementation of the 'Combatant' interface.

FIX: This version fully implements all abstract methods from the
Combatant interface (held_item, tera_type, etc.) to fix the
TypeError: Can't instantiate abstract class.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from battledex_engine.interfaces import Combatant
# FIX: Import Item from its new engine location
from battledex_engine.item import Item
from .move import Move

@dataclass
class Pokemon(Combatant):
    """
    Represents a single Pokemon instance. Implements the Combatant interface.
    """
    # --- Fields without default values must come first ---
    _id: str
    species_name: str
    level: int
    types: List[str]
    base_stats: Dict[str, int]
    moves: List[Move]

    # --- NEW: Fields to implement the Combatant interface ---
    # FIX: Rename fields to avoid conflict with abstract properties
    _held_item: Optional[Item]
    _tera_type: str

    # --- Fields with default values ---
    _is_active: bool = False
    status: Optional[str] = None
    stat_stages: Dict[str, int] = field(default_factory=lambda: {
        "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0
    })

    # --- NEW: Internal state for Terastallization ---
    _has_terastallized: bool = False
    _current_types: List[str] = field(init=False)

    # --- Fields that are calculated, not passed to the constructor ---
    current_hp: int = field(init=False)
    stats: Dict[str, int] = field(init=False)

    def __post_init__(self):
        """Calculate final stats after the object is created."""
        self.stats = self._calculate_stats()
        self.current_hp = self.stats["hp"]
        # NEW: Initialize current_types
        self._current_types = list(self.types)

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_active(self) -> bool:
        return self._is_active

    # --- NEW: Property implementations for the interface ---

    # FIX: Add 'held_item' property to satisfy the abstract class
    @property
    def held_item(self) -> Optional[Item]:
        """Implements the Combatant.held_item abstract property."""
        return self._held_item

    @property
    def has_terastallized(self) -> bool:
        return self._has_terastallized

    @property
    def tera_type(self) -> str:
        # This is a read-only property, so we just return the value.
        # The ruleset will use this to set the new type.
        # FIX: Point to renamed private field to avoid recursion
        return self._tera_type

    @property
    def current_types(self) -> List[str]:
        return self._current_types

    # --- Public methods for the ruleset to call ---

    def apply_terastallization(self):
        """
        Transforms the Pokémon by setting its type to its Tera Type.
        This is called by the ruleset.
        """
        if not self._has_terastallized:
            print(f"{self.species_name} terastallized into {self._tera_type} type!")
            self._current_types = [self._tera_type]
            self._has_terastallized = True

    def _calculate_stats(self) -> Dict[str, int]:
        """Calculates final stats based on level and base stats. Simplified for now."""
        # Note: This is the simplified formula, not the exact official one.
        return {
            "hp": int(((2 * self.base_stats["hp"]) * self.level) / 100 + self.level + 10),
            "attack": int(((2 * self.base_stats["attack"]) * self.level) / 100 + 5),
            "defense": int(((2 * self.base_stats["defense"]) * self.level) / 100 + 5),
            "sp_attack": int(((2 * self.base_stats["special_attack"]) * self.level) / 100 + 5),
            "sp_defense": int(((2 * self.base_stats["special_defense"]) * self.level) / 100 + 5),
            "speed": int(((2 * self.base_stats["speed"]) * self.level) / 100 + 5),
        }


