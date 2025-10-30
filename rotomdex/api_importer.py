"""
rotomdex/api_importer.py

A utility script to fetch Pokémon and Move data from the public
PokéAPI, transform it into the format our factories expect,
and save it to local JSON files (pokemon.json, moves.json).

This allows us to update our game data without changing the source code.

Requires the 'requests' library:
pip install requests
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any

# --- Configuration ---

# The public PokéAPI endpoint
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

# We'll create a 'data' directory inside 'rotomdex' to hold our cache
DATA_CACHE_DIR = Path(__file__).parent / "data"
POKEMON_CACHE_FILE = DATA_CACHE_DIR / "pokemon.json"
MOVE_CACHE_FILE = DATA_CACHE_DIR / "moves.json"

# Limits for fetching. ~1025 Pokémon and ~920 moves as of Gen 9.
# We'll go higher to be safe for the future.
POKEMON_LIMIT = 1500
MOVE_LIMIT = 1500

# This mapping is CRITICAL. It translates PokéAPI's stat names
# to the stat names your `Pokemon` class expects.
STAT_NAME_MAP = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special-attack": "sp_attack",
    "special-defense": "sp_defense",
    "speed": "speed",
}

# --- Data Transformation Functions ---

def _transform_pokemon_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a full Pokémon data object from PokéAPI into our
    simplified format needed by `create_pokemon_from_data`.
    """
    types = [t['type']['name'] for t in api_data['types']]
    
    # Transform base stats using our STAT_NAME_MAP
    base_stats = {}
    for api_stat in api_data['stats']:
        stat_name_api = api_stat['stat']['name']
        if stat_name_api in STAT_NAME_MAP:
            stat_name_internal = STAT_NAME_MAP[stat_name_api]
            base_stats[stat_name_internal] = api_stat['base_stat']
            
    return {
        "types": types,
        "base_stats": base_stats,
    }

def _transform_move_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a full Move data object from PokéAPI into our
    simplified format needed by `create_move_from_data`.
    """
    return {
        "move_type": api_data['type']['name'],
        "category": api_data['damage_class']['name'],
        "power": api_data.get('power'),
        "accuracy": api_data.get('accuracy'),
        "pp": api_data.get('pp'),
        "priority": api_data.get('priority', 0),
    }

# --- Main Fetching Function ---

def update_data_cache(force_update: bool = False):
    """
    Fetches all Pokémon and Move data from PokéAPI and saves it
    to the local JSON cache.
    
    Args:
        force_update: If True, will re-download all data even if
                      cache files already exist.
    """
    print("Checking for data cache...")
    DATA_CACHE_DIR.mkdir(exist_ok=True)
    
    if POKEMON_CACHE_FILE.exists() and MOVE_CACHE_FILE.exists() and not force_update:
        print("Data cache is already up to date. Skipping download.")
        return

    # --- Fetch Pokémon ---
    print(f"Fetching {POKEMON_LIMIT} Pokémon from PokéAPI...")
    all_pokemon_data = {}
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}pokemon?limit={POKEMON_LIMIT}")
        response.raise_for_status()
        pokemon_list = response.json()['results']

        for i, entry in enumerate(pokemon_list):
            name = entry['name']
            print(f"  Fetching Pokémon {i+1}/{len(pokemon_list)}: {name}...")
            poke_data = requests.get(entry['url']).json()
            all_pokemon_data[name] = _transform_pokemon_data(poke_data)
        
        print(f"Saving {len(all_pokemon_data)} Pokémon to {POKEMON_CACHE_FILE}")
        with open(POKEMON_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_pokemon_data, f, indent=2)

    except requests.RequestException as e:
        print(f"\nFATAL: Failed to download Pokémon data: {e}")
        return

    # --- Fetch Moves ---
    print(f"\nFetching {MOVE_LIMIT} moves from PokéAPI...")
    all_move_data = {}
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}move?limit={MOVE_LIMIT}")
        response.raise_for_status()
        move_list = response.json()['results']

        for i, entry in enumerate(move_list):
            name = entry['name']
            print(f"  Fetching move {i+1}/{len(move_list)}: {name}...")
            move_data = requests.get(entry['url']).json()
            all_move_data[name] = _transform_move_data(move_data)
        
        print(f"Saving {len(all_move_data)} moves to {MOVE_CACHE_FILE}")
        with open(MOVE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_move_data, f, indent=2)

    except requests.RequestException as e:
        print(f"\nFATAL: Failed to download move data: {e}")
        return

    print("\nData cache update complete!")

# --- Make it runnable ---
if __name__ == "__main__":
    """
    This allows you to run the file directly from your terminal
    to update your data:
    
    python rotomdex/api_importer.py
    """
    
    # You can pass a command-line argument like "force" to force an update
    import sys
    force = "force" in sys.argv
    update_data_cache(force_update=force)

