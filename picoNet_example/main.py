"""
main.py

Main entry point that runs both the turtle server and client in parallel using threads.
"""

import sys
import os
import time
import threading

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_server():
    """Run the turtle server in the main thread."""
    print("[MAIN] Starting Turtle Server...\n")
    import turtle_server
    turtle_server.main()

def run_client():
    """Run the turtle client in a separate thread."""
    # Wait for the server to start and display its port
    time.sleep(2.0)
    print("\n[MAIN] Starting Turtle Client...\n")
    import turtle_client
    turtle_client.main()

def main():
    """Main function that runs both server and client in parallel."""
    print("=" * 50)
    print("Turtle Graphics over picoNet")
    print("Running Server and Client in Parallel")
    print("Port: 8000")
    print("=" * 50)
    print()
    
    # Create a thread for the client
    client_thread = threading.Thread(target=run_client, daemon=True)
    
    # Start the client thread
    client_thread.start()
    
    # Run the server in the main thread (turtle needs main thread for graphics)
    run_server()
    
    # Wait for client thread to finish
    client_thread.join(timeout=5.0)
    
    print("\n[MAIN] Program completed.")

if __name__ == '__main__':
    main()
