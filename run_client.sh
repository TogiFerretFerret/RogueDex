#!/bin/bash
# Usage: ./run_client.sh [SERVER_IP]
# If SERVER_IP is provided, connects to multiplayer. Otherwise runs in singleplayer.

if [ ! -z "$1" ]; then
    export SERVER_IP="$1"
fi

uv run roguedex_client/main.py
