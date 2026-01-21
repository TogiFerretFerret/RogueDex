#!/bin/bash
# Usage: ./run_client.sh [SERVER_IP]
# If SERVER_IP is provided, connects to multiplayer. Otherwise runs in singleplayer.

# Force X11 backend for Pygame compatibility
export SDL_VIDEODRIVER=x11

if [ ! -z "$1" ]; then
    export SERVER_IP="$1"
fi

uv run roguedex_client/main.py
