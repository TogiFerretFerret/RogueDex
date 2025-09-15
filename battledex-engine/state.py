"""
battledex_engine/state.py

Defines the data structures that hold the complete, serializable state of a
battle. These objects are designed to be pure data, making them easy to
send over a network or save for replays.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class CombatantState:
    """
    Holds all the dynamic state for a single combatant in a battle.
    This does not include static data like base stats or move lists,
    which are managed by the Combatant object in the ruleset.
    """
    id: str  # A unique identifier for this specific combatant instance
    
    # In a full implementation, these would be populated:
    # current_hp: int
    # status: Optional[str]
    # stat_stages: Dict[str, int] = field(default_factory=dict)
    
@dataclass
class TeamState:
    """
    Holds the state for one entire team in the battle.
    """
    combatants: List[CombatantState]
    active_combatant_id: str
    
    # Team-wide effects, e.g., "Stealth Rock", "Spikes"
    hazards: Set[str] = field(default_factory=set)

@dataclass
class BattleState:
    """
    The root object representing the entire state of a battle at a point in time.
    This is the object that is passed to and modified by the event handlers.
    """
    teams: List[TeamState]
    turn_number: int = 0
    
    # Global field conditions
    weather: Optional[str] = None
    terrain: Optional[str] = None


