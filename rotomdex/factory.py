"""
rotomdex/factory.py

Contains factory functions for creating Pokemon and Move objects from the
raw data loaded by the data_loader. This decouples the data format
from the class implementation.
"""

from typing import Dict, List, Any

# FIX: Import Item from battledex_engine and ItemData from data_loader
from battledex_engine.item import Item
from .data_loader import PokemonData, MoveData, ItemData
from .pokemon import Pokemon
from .move import Move

def create_item_from_data(item_name: str, item_data_map: Dict[str, ItemData]) -> Item | None:
    """
    Creates an Item instance from its name and the global item data map.
    """
    # Use .lower() to match API keys
    item_key = item_name.lower()
    if item_key not in item_data_map:
        return None
    
    data = item_data_map[item_key]
    
    # FIX: Read the proper 'name' field from the data.
    # Use the key as a fallback if 'name' doesn't exist.
    proper_name = data.get("name", item_key)
    
    return Item(
        name=proper_name,
        # Make sure your Item class in battledex_engine accepts this
        fling_power=data.get("fling_power")
    )

def create_move_from_data(move_name: str, move_data_map: Dict[str, MoveData]) -> Move:
    """
    Creates a Move instance from its name and the global move data map.
    """
    # Use .lower() to match the keys from the API importer
    data = move_data_map[move_name.lower()]
    
    # FIX: Read the proper 'name' field from the data
    proper_name = data.get("name", move_name)
    
    return Move(
        name=proper_name,
        move_type=data.get("move_type"),
        category=data.get("category"),
        power=data.get("power"),
        accuracy=data.get("accuracy"),
        pp=data.get("pp"),
        _priority=data.get("priority", 0)
    )

def create_pokemon_from_data(
    species_name: str,
    level: int,
    move_names: List[str],
    pokemon_data_map: Dict[str, PokemonData],
    move_data_map: Dict[str, MoveData],
    item_data_map: Dict[str, ItemData],
    instance_id: str,
    tera_type: str,
    item_name: str | None = None,
    is_active: bool = False
) -> Pokemon:
    """
    Creates a Pokemon instance from its species name and other parameters.
    """
    # Use .lower() to match the keys from the API importer
    pokemon_data = pokemon_data_map[species_name.lower()]

    # Create the move objects for this Pokemon
    pokemon_moves = [create_move_from_data(name, move_data_map) for name in move_names]

    # Create the held item object, if one is given
    item_object = None
    if item_name:
        item_object = create_item_from_data(item_name, item_data_map)

    # FIX: Pass _held_item and _tera_type (with underscores)
    # to the Pokemon constructor to match pokemon.py
    return Pokemon(
        _id=instance_id,
        # Use the capitalized name for the object property
        species_name=species_name, 
        level=level,
        types=pokemon_data.get("types", []),
        base_stats=pokemon_data.get("base_stats", {}),
        moves=pokemon_moves,
        _held_item=item_object,
        _tera_type=tera_type,
        _is_active=is_active,
    )
