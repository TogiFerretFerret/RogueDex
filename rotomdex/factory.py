"""
rotomdex/factory.py

Contains factory functions for creating Pokemon and Move objects from the
raw data loaded by the data_loader. This decouples the data format
from the class implementation.

FIX: This version correctly reads the proper, capitalized 'name'
field from the data dictionaries for items, moves, and Pokemon.
This will fix the `StopIteration` error in the integration test.
"""

from typing import Dict, List, Any

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
    
    # Read the proper 'name' field from the data.
    # Use the key as a fallback if 'name' doesn't exist.
    proper_name = data.get("name", item_key)
    
    return Item(
        id_name=item_key,
        name=proper_name,
        fling_power=data.get("fling_power")
    )

def create_move_from_data(move_name: str, move_data_map: Dict[str, MoveData]) -> Move:
    """
    Creates a Move instance from its name and the global move data map.
    """
    # Use .lower() to match the keys from the API importer
    move_key = move_name.lower()
    
    if move_key not in move_data_map:
        # Handle moves (like "Growl" in mock data) not being found
        # This is a robust way to handle incomplete data sets.
        print(f"Warning: Move key '{move_key}' not found. Creating placeholder.")
        # Return a placeholder with the capitalized name
        return Move(name=move_name.capitalize(), move_type="normal", category="status",
                    power=0, accuracy=100, pp=20, _priority=0)

    data = move_data_map[move_key]
    
    # FIX: Read the proper 'name' field from the data.
    # This will set move.name to "Tackle", not "tackle".
    proper_name = data.get("name", move_key)
    
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
    tera_type: str | None = None,
    item_name: str | None = None,
    is_active: bool = False
) -> Pokemon:
    """
    Creates a Pokemon instance from its species name and other parameters.
    """
    # Use .lower() to match the keys from the API importer
    pokemon_key = species_name.lower()
    
    if pokemon_key not in pokemon_data_map:
         raise KeyError(f"Pokemon key '{pokemon_key}' not found in pokemon_data_map.")
         
    pokemon_data = pokemon_data_map[pokemon_key]
    
    # FIX: Read the proper 'name' field from the data
    # This will set pokemon.species_name to "Pikachu"
    proper_species_name = pokemon_data.get("name", species_name)

    # Create the move objects for this Pokemon
    pokemon_moves = [create_move_from_data(name, move_data_map) for name in move_names]

    # Create the held item object, if one is given
    item_object = None
    if item_name:
        item_object = create_item_from_data(item_name, item_data_map)
        
    # Handle the optional tera_type
    pokemon_types = pokemon_data.get("types", [])
    if tera_type is None:
        tera_type = pokemon_types[0] if pokemon_types else "normal"

    return Pokemon(
        _id=instance_id,
        species_name=proper_species_name, # Use the proper name
        level=level,
        types=pokemon_types,
        base_stats=pokemon_data.get("base_stats", {}),
        moves=pokemon_moves,
        _held_item=item_object,
        _tera_type= tera_type,
        _is_active=is_active,
    )


