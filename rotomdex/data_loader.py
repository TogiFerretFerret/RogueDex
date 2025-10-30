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

# --- NEW: Point to the 'data' subdirectory ---
DATA_CACHE_DIR = Path(__file__).parent / "data"

def load_pokemon_data() -> Dict[str, PokemonData]:
    """
    Loads all Pokémon data from the 'data/pokemon.json' cache.
    """
    data_path = DATA_CACHE_DIR / "pokemon.json"
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Pokémon data not found at {data_path}.")
        print("Please run the API importer script:")
        print("python rotomdex/api_importer.py")
        return {}


def load_move_data() -> Dict[str, MoveData]:
    """
    Loads all move data from the 'data/moves.json' cache.
    """
    data_path = DATA_CACHE_DIR / "moves.json"
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Move data not found at {data_path}.")
        print("Please run the API importer script:")
        print("python rotomdex/api_importer.py")
        return {}

