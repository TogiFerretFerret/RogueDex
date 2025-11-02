"""
rotomdex/factory.py

Contains factory functions for creating Pokemon and Move objects from the
raw data loaded by the data_loader. This decouples the data format
from the class implementation.
"""

from typing import Dict, List, Any, Optional

# <<< FIX: Import ItemData and Item >>>
from .data_loader import PokemonData, MoveData, ItemData
from .pokemon import Pokemon
from .move import Move
from battledex_engine.item import Item


def create_move_from_data(move_name: str, move_data_map: Dict[str, MoveData]) -> Move:
    """
    Creates a Move instance from its name and the global move data map.

    Args:
        move_name: The name of the move to create (e.g., "Tackle").
        move_data_map: The dictionary of all move data, loaded from JSON.

    Returns:
        An instance of the Move class.

    Raises:
        KeyError: if the move_name is not found in the data map.
    """
    # FIX: Add .lower() to handle capitalization mismatches like "Growl"
    data = move_data_map[move_name.lower()]
    return Move(
        name=move_name,
        move_type=data.get("move_type"),
        category=data.get("category"),
        power=data.get("power"),
        accuracy=data.get("accuracy"),
        pp=data.get("pp"),
        _priority=data.get("priority", 0)
    )

#
# <<< FIX: Replaced stub with full implementation >>>
#
def create_item_from_data(item_name: str, item_data_map: Dict[str, ItemData]) -> Item:
    """
    Creates an Item instance from its name and the global item data map.

    Args:
        item_name: The name of the item to create (e.g., "Choice Scarf").
        item_data_map: The dictionary of all item data, loaded from JSON.

    Returns:
        An instance of the Item class.
    """
    # FIX: Add .lower() to handle capitalization
    # FIX: Get data from map to find fling_power
    data = item_data_map[item_name.lower()]
    
    # FIX: Pass fling_power to constructor to solve TypeError
    return Item(
        name=item_name,
        fling_power=data.get("fling_power")
    )


#
# <<< FIX: Updated function signature and body >>>
#
def create_pokemon_from_data(
    species_name: str,
    level: int,
    move_names: List[str],
    pokemon_data_map: Dict[str, PokemonData],
    move_data_map: Dict[str, MoveData],
    item_data_map: Optional[Dict[str, ItemData]], # <<< FIX: Added to signature
    instance_id: str,
    item_name: Optional[str] = None,              # <<< FIX: Added item_name
    tera_type: Optional[str] = None,              # <<< FIX: Added tera_type
    is_active: bool = False
) -> Pokemon:
    """
    Creates a Pokemon instance from its species name and other parameters.

    Args:
        species_name: The species name (e.g., "Pikachu").
        level: The level of the Pokemon.
        move_names: A list of names for the moves this Pokemon knows.
        pokemon_data_map: The dictionary of all Pokemon data.
        move_data_map: The dictionary of all move data.
        item_data_map: The dictionary of all item data.
        instance_id: A unique ID for this specific Pokemon instance.
        item_name: (Optional) The name of the item this Pokemon is holding.
        tera_type: (Optional) The Tera Type of this Pokemon.
        is_active: Whether this Pokemon starts as the active combatant.

    Returns:
        An instance of the Pokemon class.
    """
    # FIX: Add .lower() to handle capitalization mismatches like "Pikachu"
    pokemon_data = pokemon_data_map[species_name.lower()]

    # Create the move objects for this Pokemon
    pokemon_moves = [create_move_from_data(name, move_data_map) for name in move_names]

    # Create the held_item object (if one is given)
    held_item = None
    if item_name and item_data_map:
        try:
            # FIX: Add .lower() to handle capitalization
            held_item = create_item_from_data(item_name.lower(), item_data_map)
        except KeyError:
            print(f"Warning: Item '{item_name}' not found in item_data_map. Creating Pokemon with no item.")

    # Determine Tera Type (defaults to first base type)
    final_tera_type = tera_type or pokemon_data.get("types", ["normal"])[0]

    return Pokemon(
        _id=instance_id,
        species_name=species_name,
        level=level,
        types=pokemon_data.get("types", []),
        base_stats=pokemon_data.get("base_stats", {}),
        moves=pokemon_moves,
        held_item=held_item,        # <<< FIX: Passed to constructor
        tera_type=final_tera_type,  # <<< FIX: Passed to constructor
        _is_active=is_active,
    )


