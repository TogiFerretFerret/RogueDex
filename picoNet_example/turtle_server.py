"""
turtle_server.py

The server application that receives and executes turtle drawing commands.
"""
import turtle
import time
import sys
import os
from typing import Dict, Any

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from picoNet.connection import Connection, ConnectionState
from picoNet.socket import PicoSocket

def execute_command(t: turtle.Turtle, command: Dict[str, Any]):
    """
    Executes a parsed command dictionary by calling the appropriate turtle methods.
    """
    cmd_type = command.get("command")
    print(f"[SERVER] Executing command: {cmd_type}")
    
    try:
        if cmd_type == "FORWARD":
            t.forward(command.get('distance', 0))
        elif cmd_type == "BACKWARD":
            t.backward(command.get('distance', 0))
        elif cmd_type == "LEFT":
            t.left(command.get('degrees', 0))
        elif cmd_type == "RIGHT":
            t.right(command.get('degrees', 0))
        elif cmd_type == "CIRCLE":
            t.circle(command.get('radius', 0))
        elif cmd_type == "DOT":
            t.dot(command.get('radius', 0))
        elif cmd_type == "SPEED":
            t.speed(command.get('speed', 0))
        elif cmd_type == "CLEAR":
            t.clear()
        elif cmd_type == "RESET":
            t.reset()
        elif cmd_type == "PENUP":
            t.penup()
        elif cmd_type == "PENDOWN":
            t.pendown()
        elif cmd_type == "HOME":
            t.home()
        elif cmd_type == "GOTO":
            t.goto(command.get('x', 0), command.get('y', 0))
        elif cmd_type == "COLOR":
            t.color(command.get('color', 'black'))
        elif cmd_type == "STAMP":
            t.stamp()
        elif cmd_type == "PENSIZE":
            t.pensize(command.get('size', 1))
        else:
            print(f"[SERVER] Unknown command: {cmd_type}")
    except Exception as e:
        print(f"[SERVER] Error executing {cmd_type}: {e}")

def main():
    """
    Initializes the server, turtle window, and enters the main loop.
    """
    HOST = '127.0.0.1'
    PORT = 8000

    # Set up the turtle screen
    screen = turtle.Screen()
    screen.title("Networked Turtle Graphics over picoNet")
    screen.bgcolor("white")
    t = turtle.Turtle()
    t.shape("turtle")
    t.speed("fastest")

    # Set up the network connection
    connection = Connection(HOST, PORT)
    
    # Close the auto-created socket and create a new one on the specific port
    connection._socket.close()
    connection._socket = PicoSocket(HOST, PORT)
    
    actual_port = connection._socket.get_address()[1]
    print(f"[SERVER] Turtle server listening on {HOST}:{actual_port}")
    print("[SERVER] Waiting for a client to connect...")

    last_ack_time = 0.0
    ACK_INTERVAL = 0.05  # Send ACKs every 50ms

    try:
        while True:
            # Update network connection frequently
            connection.update(0.01)
            
            if connection.is_connected:
                payloads = connection.receive()
                for command_dict in payloads:
                    execute_command(t, command_dict)
                
                # Send periodic ACK-only packets to acknowledge received commands
                current_time = time.time()
                if current_time - last_ack_time > ACK_INTERVAL:
                    if connection._remote_sequence_number != -1:
                        connection.send_ack_only()  # Use the new ACK-only method
                    last_ack_time = current_time
            
            # Update turtle screen
            screen.update()
            time.sleep(0.001)

    except turtle.Terminator:
        print("[SERVER] Turtle window closed.")
    except KeyboardInterrupt:
        print("\n[SERVER] Server interrupted.")
    finally:
        print("[SERVER] Shutting down server.")
        connection.close()

if __name__ == "__main__":
    main()
