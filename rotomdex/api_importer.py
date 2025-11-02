"""
rotomdex/api_importer.py

Fetches all required data from the public PokéAPI and saves it
to the local 'rotomdex/data/' cache.

FIX: This version is complete and correctly fetches the proper
English names for Pokémon, Moves, and Items, saving them
as the 'name' field in the JSON. This is required by
the factory.py.
"""

import httpx
import json
from pathlib import Path
from typing import Dict, Any, List

# --- Constants ---
API_URL = "https://pokeapi.co/api/v2"
# We'll fetch the first 151 Pokémon (Gen 1)
POKEMON_LIMIT =125600 
# We'll fetch all moves (Gen 1-9)
MOVE_LIMIT = 1000
# We'll fetch all items
ITEM_LIMIT = 3110

CACHE_DIR = Path(__file__).parent / "data"

# --- Helper Function ---

def _find_english_name(names_list: List[Dict[str, Any]]) -> str:
    """Helper to extract the English name from a 'names' list."""
    for entry in names_list:
        if entry["language"]["name"] == "en":
            return entry["name"]
    return "Unknown" # Fallback

def _fetch_resource_list(endpoint: str, limit: int) -> List[Dict[str, str]]:
    """Fetches the list of all resources (e.g., all Pokémon)."""
    print(f"Fetching resource list for: {endpoint}")
    try:
        response = httpx.get(f"{API_URL}/{endpoint}/?limit={limit}", timeout=10.0)
        response.raise_for_status()
        return response.json()["results"]
    except httpx.RequestError as e:
        print(f"Error fetching resource list {endpoint}: {e}")
        return []

def _fetch_resource_data(url: str, client: httpx.Client) -> Dict[str, Any] | None:
    """Fetches data for a single resource (e.g., 'pikachu')."""
    try:
        response = client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        print(f"Error fetching {url}: {e}")
        return None

# --- Data Transformation Functions ---

def _transform_pokemon_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts only the data we need for a Pokémon."""
    
    # FIX: The 'names' field is not in the main /pokemon/ endpoint.
    # We must fetch it from the /pokemon-species/ endpoint.
    species_url = data["species"]["url"]
    try:
        # Note: This makes an extra request for each Pokémon.
        # This is less efficient but required to get the proper name.
        species_response = httpx.get(species_url, timeout=10.0)
        species_response.raise_for_status()
        species_data = species_response.json()
        proper_name = _find_english_name(species_data["names"])
    except Exception as e:
        print(f"  > Warning: Could not fetch species data from {species_url}. Defaulting to key name. Error: {e}")
        # Fallback to the lowercase name if the species fetch fails
        proper_name = data["name"].capitalize() 

    return {
        "id": data["id"],
        "name": proper_name, # Use the fetched proper name
        "types": [t["type"]["name"] for t in data["types"]],
        "base_stats": {
            s["stat"]["name"].replace("-", "_"): s["base_stat"]
            for s in data["stats"]
        }
    }

def _transform_move_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts only the data we need for a move."""
    return {
        "id": data["id"],
        "name": _find_english_name(data["names"]), # FIX: Get proper name
        "move_type": data["type"]["name"],
        "category": data["damage_class"]["name"],
        "power": data.get("power"),
        "accuracy": data.get("accuracy"),
        "pp": data.get("pp"),
        "priority": data.get("priority", 0)
    }

def _transform_item_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts only the data we need for an item."""
    return {
        "id": data["id"],
        "name": _find_english_name(data["names"]), # FIX: Get proper name
        "fling_power": data.get("fling_power"),
        # FIX: Get the English effect description
        "effect": next(
            (
                entry["effect"]
                for entry in data.get("effect_entries", [])
                if entry["language"]["name"] == "en"
            ),
            None,
        ),
    }

# --- Main Fetching Function ---

def fetch_and_save_data(
    endpoint: str,
    limit: int,
    transform_func: callable,
    output_filename: str
):
    """
    Core logic to fetch a list of resources, get data for each,
    transform it, and save it to a JSON file.
    """
    resource_list = _fetch_resource_list(endpoint, limit)
    if not resource_list:
        print(f"No resources found for {endpoint}. Aborting.")
        return

    final_data: Dict[str, Any] = {}
    total = len(resource_list)
    
    # Use a client for connection pooling
    with httpx.Client() as client:
        for i, resource in enumerate(resource_list):
            name_key = resource["name"]
            data_url = resource["url"]
            
            print(f"[{i+1}/{total}] Fetching {endpoint}: {name_key}")
            
            data = _fetch_resource_data(data_url, client)
            if data:
                try:
                    # This is where _transform_pokemon_data (and its extra fetch) is called
                    transformed_data = transform_func(data)
                    final_data[name_key] = transformed_data
                except Exception as e:
                    print(f"Error transforming data for {name_key}: {e}")
                    # Print the keys to help debug if it happens again
                    print(f"Data keys: {data.keys()}")

    # Ensure the cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save the final data to the file
    output_path = CACHE_DIR / output_filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully saved data to {output_path}")
    except IOError as e:
        print(f"Error writing data to {output_path}: {e}")

# --- Main Execution ---

def main():
    print("Starting RotomDex API Importer...")
    
    # 1. Fetch Pokémon
    fetch_and_save_data(
        endpoint="pokemon",
        limit=POKEMON_LIMIT,
        transform_func=_transform_pokemon_data,
        output_filename="pokemon.json"
    )
    
    # 2. Fetch Moves
    fetch_and_save_data(
        endpoint="move",
        limit=MOVE_LIMIT,
        transform_func=_transform_move_data,
        output_filename="moves.json"
    )
    
    # 3. Fetch Items
    fetch_and_save_data(
        endpoint="item",
        limit=ITEM_LIMIT,
        transform_func=_transform_item_data,
        output_filename="items.json"
    )
    
    print("\nData import complete!")

if __name__ == "__main__":
    main()


