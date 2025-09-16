"""
rotomdex/factory.py

Contains factory functions for creating Pokemon and Move objects from the
raw data loaded by the data_loader. This decouples the data format
from the class implementation.
"""

from typing import Dict, List, Any

from .data_loader import PokemonData, MoveData
from .pokemon import Pokemon
from .move import Move

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
    data = move_data_map[move_name]
    return Move(
        name=move_name,
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
    instance_id: str,
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
        instance_id: A unique ID for this specific Pokemon instance.
        is_active: Whether this Pokemon starts as the active combatant.

    Returns:
        An instance of the Pokemon class.
    """
    pokemon_data = pokemon_data_map[species_name]
    
    # Create the move objects for this Pokemon
    pokemon_moves = [create_move_from_data(name, move_data_map) for name in move_names]

    return Pokemon(
        _id=instance_id,
        species_name=species_name,
        level=level,
        types=pokemon_data.get("types", []),
        base_stats=pokemon_data.get("base_stats", {}),
        moves=pokemon_moves,
        _is_active=is_active,
    )


