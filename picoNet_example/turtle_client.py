"""
turtle_client.py

Client that sends turtle commands to the server.
"""
import time
import sys
import os

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from picoNet.connection import Connection, ConnectionState

# The list of commands to be sent automatically
COMMAND_SCRIPT = [
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'BACKWARD', 'distance': 100},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 90},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'RIGHT', 'degrees': 90},
    {'command': 'CLEAR'},
    {'command': 'CIRCLE', 'radius': 100},
    {'command': 'DOT', 'radius': 50},
    {'command': 'CLEAR'},
    {'command': 'PENUP'},
    {'command': 'HOME'},
    {'command': 'PENDOWN'},
    {'command': 'SPEED', 'speed': 10},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'LEFT', 'degrees': 60},
    {'command': 'RESET'},
    {'command': 'PENUP'},
    {'command': 'FORWARD', 'distance': 50},
    {'command': 'PENDOWN'},
    {'command': 'FORWARD', 'distance': 50},
    {'command': 'PENUP'},
    {'command': 'FORWARD', 'distance': 50},
    {'command': 'PENDOWN'},
    {'command': 'FORWARD', 'distance': 50},
    {'command': 'COLOR', 'color': 'red'},
    {'command': 'CIRCLE', 'radius': 50},
    {'command': 'STAMP'},
    {'command': 'PENSIZE', 'size': 5},
    {'command': 'FORWARD', 'distance': 100},
    {'command': 'RESET'},
    {'command': 'GOTO', 'x': 0, 'y': 0},
    {'command': 'GOTO', 'x': 100, 'y': 0},
    {'command': 'GOTO', 'x': 100, 'y': 100},
    {'command': 'GOTO', 'x': 0, 'y': 100},
    {'command': 'GOTO', 'x': 0, 'y': 0},
]

def main():
    """
    Initializes the client, connects to the server, and sends a script of commands.
    """
    HOST = '127.0.0.1'
    PORT = 8000

    connection = Connection(HOST, PORT)
    connection.connect()

    print("[CLIENT] Connecting to turtle server...")
    # Wait for the connection to be established
    connect_start_time = time.time()
    while connection.state == ConnectionState.CONNECTING:
        if time.time() - connect_start_time > 5.0:  # 5 second connect timeout
            print("[CLIENT] Connection attempt timed out.")
            return
        connection.update(0.1)
        time.sleep(0.1)

    if not connection.is_connected:
        print("[CLIENT] Failed to connect to the server. Exiting.")
        return

    print("[CLIENT] Connection successful! Sending commands...")

    try:
        # Loop through the command script and send each one
        for command_dict in COMMAND_SCRIPT:
            cmd_name = command_dict.get('command', 'UNKNOWN')
            print(f"[CLIENT] Sending: {cmd_name}")
            connection.send(command_dict)

            # We must call update() regularly to process ACKs and keep the connection alive
            connection.update(0.1)
            # Pause briefly to allow the server to process and draw
            time.sleep(0.3)

        print("\n[CLIENT] All commands sent. Keeping connection alive for 2 seconds...")
        # Keep connection alive for a final moment to ensure last packets are sent/acked
        time.sleep(2)

    except KeyboardInterrupt:
        print("\n[CLIENT] Script interrupted.")
    finally:
        print("[CLIENT] Closing connection.")
        connection.close()

if __name__ == "__main__":
    main()
