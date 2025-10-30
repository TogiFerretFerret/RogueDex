"""
battledex-engine/item.py

Defines the class for an Item.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Item:
    """
    Represents a generalized item that a Combatant can hold or use.
    """
    name: str
    fling_power: int | None
    attributes: List[str] = field(default_factory=list)
    # 'attributes' can be things like:
    # 'holdable', 'usable-in-battle', 'consumable'


