"""
rotomdex/move.py

Defines the concrete implementation of the `Action` interface from the
battledex-engine, specific to Pokémon moves.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from battledex_engine.interfaces import Action

@dataclass
class Move(Action):
    """
    Represents a single move a Pokemon can use. Implements the Action interface.
    """
    name: str
    move_type: str
    category: str  # "Physical", "Special", "Status"
    power: int | None
    accuracy: int | None
    pp: int
    _priority: int = 0
    effects: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def priority(self) -> int:
        return self._priority

