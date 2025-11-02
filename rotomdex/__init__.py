"""
RotomDex: The Pokémon-specific implementation for the RogueDex engine.

This package contains:
- `Pokemon` and `Move` classes (implementing Combatant and Action)
- `factory` functions to build them from data
- `data_loader` to load data from the JSON cache
- `api_importer` to build that cache from PokéAPI
- `ruleset` to define all Pokémon-specific game logic
"""

from .pokemon import Pokemon
from .move import Move
# <<< FIX: Added create_item_from_data >>>
from .factory import create_pokemon_from_data, create_move_from_data, create_item_from_data
# <<< FIX: Added load_item_data >>>
from .data_loader import load_pokemon_data, load_move_data, load_item_data
from .ruleset import PokemonRuleset

