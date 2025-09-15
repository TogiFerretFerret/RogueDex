"""
battledex_engine/state.py

Defines the data structures that represent the complete, serializable state
of a battle at any given moment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class CombatantState:
    """Represents the state of a single combatant."""
    id: str
    # All other combatant-specific data (HP, stats, status, etc.) will be
    # managed by the concrete implementation in the ruleset library.
    # This is just the engine-level view.

@dataclass
class TeamState:
    """Represents the state of one team in the battle."""
    combatants: List[CombatantState]
    active_combatant_id: str
    # Example state: hazards like 'stealth_rock' would be stored here.
    hazards: Set[str] = field(default_factory=set)

@dataclass
class BattleState:
    """The top-level object holding the entire state of the battle."""
    teams: List[TeamState]
    turn_number: int = 0
    weather: Optional[str] = None
    terrain: Optional[str] = None

