"""
picoNet/socket.py

A high-level wrapper around Python's native UDP socket functionality.
This class handles the creation and configuration of a non-blocking socket,
which is essential for real-time applications like games.
"""

import socket

class PicoSocket:
    """A non-blocking UDP socket wrapper."""

    def __init__(self, host: str, port: int):
        """
        Creates and binds a non-blocking UDP socket.

        Args:
            host: The IP address to bind to.
            port: The port to bind to. Use 0 to let the OS choose a port.
        """
        self.socket = None
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Set the socket to be non-blocking. This is crucial.
            self.socket.setblocking(False)
            # --- FIX: Allow address reuse ---
            # This prevents "Address already in use" errors in rapid testing.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((host, port))
            print(f"PicoSocket bound to {self.socket.getsockname()}")
        except OSError as e:
            print(f"Error creating or binding socket: {e}")
            if self.socket:
                self.socket.close()
            self.socket = None

    def send(self, address: tuple, data: bytes):
        """
        Sends data to a specified address.

        Args:
            address: A (host, port) tuple for the destination.
            data: The bytes to send.
        """
        if not self.socket:
            return
        self.socket.sendto(data, address)

    def receive(self) -> tuple[bytes, tuple] | None:
        """
        Receives data from the socket.

        Returns:
            A tuple containing (data, address) if data is available,
            otherwise None.
        """
        if not self.socket:
            return None
        try:
            # A large buffer size is fine for UDP.
            data, address = self.socket.recvfrom(65535)
            return data, address
        except BlockingIOError:
            # This is expected when no data is available on a non-blocking socket.
            return None

    def get_address(self) -> tuple | None:
        """
        --- NEW: Returns the address the socket is bound to. ---
        """
        if not self.socket:
            return None
        return self.socket.getsockname()

    def close(self):
        """Closes the socket."""
        if self.socket:
            print("Closing PicoSocket.")
            self.socket.close()
            self.socket = None


