"""
rotomdex/data_loader.py

Functions for loading and validating Pokémon, move, and other game data
from the local JSON data cache.

FIX: This version is updated to accept an optional file path.
If no path is given, it uses the default 'data/' directory.
This makes it compatible with both the integration test and
the other unit tests.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

# --- Type Aliases for Clarity ---
PokemonData = Dict[str, Any]
MoveData = Dict[str, Any]

# --- Default cache directory ---
DEFAULT_CACHE_DIR = Path(__file__).parent / "data"

def load_pokemon_data(data_path: Path | None = None) -> Dict[str, PokemonData]:
    """
    Loads all Pokémon data from the 'data/pokemon.json' cache.
    
    If data_path is provided, it will be used instead.
    """
    if data_path is None:
        data_path = DEFAULT_CACHE_DIR / "pokemon.json"
        
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Pokémon data not found at {data_path}.")
        if data_path == (DEFAULT_CACHE_DIR / "pokemon.json"):
            print("Please run the API importer script:")
            print("python rotomdex/api_importer.py")
        raise e # Re-raise error to fail tests


def load_move_data(data_path: Path | None = None) -> Dict[str, MoveData]:
    """
    Loads all move data from the 'data/moves.json' cache.
    
    If data_path is provided, it will be used instead.
    """
    if data_path is None:
        data_path = DEFAULT_CACHE_DIR / "moves.json"
        
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Move data not found at {data_path}.")
        if data_path == (DEFAULT_CACHE_DIR / "moves.json"):
            print("Please run the API importer script:")
            print("python rotomdex/api_importer.py")
        raise e # Re-raise error to fail tests
