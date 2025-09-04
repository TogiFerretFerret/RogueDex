"""
picoNet/socket.py

Provides a high-level, non-blocking UDP socket wrapper for sending and
receiving raw datagrams.
"""

import socket
from typing import Optional, Tuple

class PicoSocket:
    """
    A simple wrapper around a non-blocking UDP socket.
    """
    def __init__(self, host: str, port: int):
        """
        Initializes and binds the UDP socket.

        Args:
            host: The hostname or IP address to bind to.
            port: The port to bind to. A port of 0 will let the OS
                  pick an ephemeral port, which is useful for clients.
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self._buffer_size = 4096  # 4KB buffer, ample for our packet size

        try:
            # Create a UDP socket (AF_INET for IPv4, SOCK_DGRAM for UDP)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Set the socket to non-blocking mode. This is crucial for games,
            # as it prevents the program from halting while waiting for data.
            self.socket.setblocking(False)
            # Bind the socket to the specified host and port
            self.socket.bind((self.host, self.port))
            print(f"PicoSocket bound to {self.socket.getsockname()}")
        except socket.error as e:
            print(f"Error creating or binding socket: {e}")
            self.socket = None

    def send(self, address: Tuple[str, int], data: bytes):
        """
        Sends data to a specific address.

        Args:
            address: A tuple containing the (host, port) of the recipient.
            data: The bytes to be sent.
        """
        if not self.socket:
            return
        try:
            self.socket.sendto(data, address)
        except socket.error as e:
            # In a non-blocking socket, a "send" can fail if the network buffer
            # is full. In a real game, we'd handle this more gracefully.
            print(f"Error sending data: {e}")

    def receive(self) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        """
        Receives data from the socket.

        Since the socket is non-blocking, this will return None if there is
        no data to be read.

        Returns:
            A tuple containing (data, address) if data was received,
            otherwise None.
        """
        if not self.socket:
            return None
        try:
            data, address = self.socket.recvfrom(self._buffer_size)
            return data, address
        except BlockingIOError:
            # This is the expected exception when there's no data to read
            # on a non-blocking socket. We can safely ignore it.
            return None
        except socket.error as e:
            print(f"Error receiving data: {e}")
            return None

    def close(self):
        """
        Closes the socket.
        """
        if self.socket:
            print("Closing PicoSocket.")
            self.socket.close()
            self.socket = None

