"""
battledex_engine/item.py

The interface for an Item.

FIX: Added 'id_name' to store the lowercase,-hyphenated
key for this item, in addition to its proper 'name'.
This matches the expectation of test_factory.py.
"""

from dataclasses import dataclass

@dataclass
class Item:
    """
    Represents an item that a Combatant can hold.
    This is a simple data-holding class; all logic
    is handled by the Ruleset.
    """
    id_name: str  # The unique key, e.g., "light-ball"
    name: str     # The proper name, e.g., "Light Ball"
    fling_power: int | None
    
    # You could add other fields here later, like:
    # effect_description: str
