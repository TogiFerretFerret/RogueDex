"""
rotomdex/data_loader.py

Functions for loading and validating Pokémon, move, and other game data
from the local JSON data cache.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

# --- Type Aliases for Clarity ---
PokemonData = Dict[str, Any]
MoveData = Dict[str, Any]

def load_pokemon_data(data_path: Path) -> Dict[str, PokemonData]:
    """
    Loads all Pokémon data from a given JSON file.

    Args:
        data_path: The path to the pokemon.json file.

    Returns:
        A dictionary mapping Pokémon species names to their data.
    """
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # In a real application, you'd add schema validation here (e.g., with Pydantic)
        # to ensure the loaded data has the expected structure.
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading Pokémon data from {data_path}: {e}")
        return {}


def load_move_data(data_path: Path) -> Dict[str, MoveData]:
    """
    Loads all move data from a given JSON file.

    Args:
        data_path: The path to the moves.json file.

    Returns:
        A dictionary mapping move names to their data.
    """
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Add schema validation here in a real application.
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading move data from {data_path}: {e}")
        return {}


