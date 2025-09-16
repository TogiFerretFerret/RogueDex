"""
rotomdex/pokemon.py

Defines the concrete implementation of the `Combatant` interface from the
battledex-engine, specific to Pokémon.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from battledex_engine.interfaces import Combatant
from .move import Move

@dataclass
class Pokemon(Combatant):
    """
    Represents a single Pokemon instance. Implements the Combatant interface.
    """
    _id: str
    _is_active: bool = False
    
    # Core Pokemon Attributes
    species_name: str
    level: int
    types: List[str]
    base_stats: Dict[str, int]
    moves: List[Move]
    
    # Battle-specific state
    current_hp: int = field(init=False)
    stats: Dict[str, int] = field(init=False)
    status: Optional[str] = None
    stat_stages: Dict[str, int] = field(default_factory=lambda: {
        "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0
    })

    def __post_init__(self):
        """Calculate final stats after the object is created."""
        self.stats = self._calculate_stats()
        self.current_hp = self.stats["hp"]

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_active(self) -> bool:
        return self._is_active

    def _calculate_stats(self) -> Dict[str, int]:
        """Calculates final stats based on level and base stats. Simplified for now."""
        # This formula is a simplification. A real implementation
        # would account for IVs, EVs, and Nature.
        return {
            "hp": int(((2 * self.base_stats["hp"]) * self.level) / 100 + self.level + 10),
            "attack": int(((2 * self.base_stats["attack"]) * self.level) / 100 + 5),
            "defense": int(((2 * self.base_stats["defense"]) * self.level) / 100 + 5),
            "sp_attack": int(((2 * self.base_stats["sp_attack"]) * self.level) / 100 + 5),
            "sp_defense": int(((2 * self.base_stats["sp_defense"]) * self.level) / 100 + 5),
            "speed": int(((2 * self.base_stats["speed"]) * self.level) / 100 + 5),
        }

