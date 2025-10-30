"""
rotomdex/api_importer.py

A utility script to fetch Pokémon and Move data from the public
PokéAPI, transform it into the format our factories expect,
and save it to local JSON files (pokemon.json, moves.json).

This version is optimized for LOW MEMORY usage by writing
data to disk incrementally instead of building a large
dictionary in memory.

It also fetches all Pokémon *varieties* (Megas, Alolan, etc.),
not just base forms.

Requires the 'requests' library:
pip install requests
"""

import requests
import json
import io
from pathlib import Path
from typing import Dict, Any, Generator, Tuple

# --- Configuration ---

# The public PokéAPI endpoint
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

# We'll create a 'data' directory inside 'rotomdex' to hold our cache
DATA_CACHE_DIR = Path(__file__).parent / "data"
POKEMON_CACHE_FILE = DATA_CACHE_DIR / "pokemon.json"
MOVE_CACHE_FILE = DATA_CACHE_DIR / "moves.json"

# Limits for fetching. ~1300 species (Gen 9) -> ~1500 varieties
# ~920 moves. We'll set a high ceiling.
SPECIES_LIMIT = 1500
MOVE_LIMIT = 1500

# This mapping is CRITICAL. It translates PokéAPI's stat names
# to the stat names our `Pokemon` class expects.
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
    Converts a full Pokémon data object (a "variety") from PokéAPI
    into our simplified format.
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
    simplified format.
    """
    return {
        "move_type": api_data['type']['name'],
        "category": api_data['damage_class']['name'],
        "power": api_data.get('power'),
        "accuracy": api_data.get('accuracy'),
        "pp": api_data.get('pp'),
        "priority": api_data.get('priority', 0),
    }

# --- Data Fetching Generators (Low Memory) ---

def _fetch_all_pokemon_varieties() -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """
    Generator that fetches all Pokémon species, then all varieties
    (including Megas, Alolan, etc.) one by one.
    
    Yields:
        A tuple of (pokemon_variety_name, transformed_data_dict)
    """
    print(f"Fetching {SPECIES_LIMIT} Pokémon species list...")
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}pokemon-species?limit={SPECIES_LIMIT}")
        response.raise_for_status()
        species_list = response.json()['results']
        
        total_species = len(species_list)
        for i, species_entry in enumerate(species_list):
            species_name = species_entry['name']
            print(f"  Fetching species {i+1}/{total_species}: {species_name}...")
            
            species_data = requests.get(species_entry['url']).json()
            
            for variety_entry in species_data['varieties']:
                variety_name = variety_entry['pokemon']['name']
                print(f"    -> Fetching variety: {variety_name}")
                
                try:
                    poke_data = requests.get(variety_entry['pokemon']['url']).json()
                    transformed_data = _transform_pokemon_data(poke_data)
                    yield variety_name, transformed_data
                except requests.RequestException as e:
                    print(f"    WARNING: Failed to fetch variety {variety_name}: {e}")
                    
    except requests.RequestException as e:
        print(f"\nFATAL: Failed to download Pokémon species list: {e}")
        return

def _fetch_all_moves() -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """
    Generator that fetches all moves one by one.
    
    Yields:
        A tuple of (move_name, transformed_data_dict)
    """
    print(f"Fetching {MOVE_LIMIT} move list...")
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}move?limit={MOVE_LIMIT}")
        response.raise_for_status()
        move_list = response.json()['results']
        
        total_moves = len(move_list)
        for i, move_entry in enumerate(move_list):
            move_name = move_entry['name']
            print(f"  Fetching move {i+1}/{total_moves}: {move_name}...")
            
            try:
                move_data = requests.get(move_entry['url']).json()
                transformed_data = _transform_move_data(move_data)
                yield move_name, transformed_data
            except requests.RequestException as e:
                print(f"    WARNING: Failed to fetch move {move_name}: {e}")

    except requests.RequestException as e:
        print(f"\nFATAL: Failed to download move list: {e}")
        return

# --- Main Stream-to-File Function ---

def _stream_generator_to_json_file(generator: Generator, file_path: Path):
    """
    Takes a generator that yields (key, data) tuples and streams
    them into a large JSON file on disk without storing them
    all in memory.
    """
    print(f"Streaming data to {file_path}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{\n")
        
        is_first_entry = True
        count = 0
        for name, data in generator:
            json_string = json.dumps(data)
            
            if not is_first_entry:
                f.write(",\n")
            
            f.write(f'  "{name}": {json_string}')
            is_first_entry = False
            count += 1
            
        f.write("\n}\n")
    print(f"Successfully streamed {count} entries to {file_path}.")

def update_data_cache(force_update: bool = False):
    """
    Fetches all Pokémon and Move data from PokéAPI and saves it
    to the local JSON cache using a low-memory stream.
    
    Args:
        force_update: If True, will re-download all data even if
                      cache files already exist.
    """
    print("Checking for data cache...")
    DATA_CACHE_DIR.mkdir(exist_ok=True)
    
    if POKEMON_CACHE_FILE.exists() and MOVE_CACHE_FILE.exists() and not force_update:
        print("Data cache is already up to date. Skipping download.")
        return

    # --- Process Pokémon ---
    if not POKEMON_CACHE_FILE.exists() or force_update:
        pokemon_generator = _fetch_all_pokemon_varieties()
        _stream_generator_to_json_file(pokemon_generator, POKEMON_CACHE_FILE)
    else:
        print(f"{POKEMON_CACHE_FILE} already exists. Skipping Pokémon.")

    # --- Process Moves ---
    if not MOVE_CACHE_FILE.exists() or force_update:
        move_generator = _fetch_all_moves()
        _stream_generator_to_json_file(move_generator, MOVE_CACHE_FILE)
    else:
        print(f"{MOVE_CACHE_FILE} already exists. Skipping moves.")

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


