
import sys
import os
import pygame
from unittest.mock import MagicMock

# Mock pygame to avoid "No video mode has been set" or headless issues during automated test
# We only want to verify logic flow and imports.
# But actually, if we want to test "headless", we can set SDL_VIDEODRIVER to dummy.
os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from roguedex_client.main import RogueDexClient

def test_initialization():
    print("Testing RogueDexClient initialization...")
    try:
        # Initialize client (this calls init_battle, pygame.init, etc.)
        client = RogueDexClient()
        
        print("Client initialized successfully.")
        print(f"Teams: {len(client.battle.state.teams)}")
        print(f"Active P1: {client.battle.state.teams[0].active_combatant_id}")
        
        # Test one turn processing
        print("Testing process_turn...")
        client.process_turn()
        print("Turn processed.")
        print(f"Turn number: {client.battle.state.turn_number}")
        
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_initialization()
