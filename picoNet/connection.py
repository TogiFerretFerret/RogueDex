"""
picoNet/connection.py

Provides the main Connection class, which manages the state of a connection
to a remote host and handles the reliability layer. This is the primary
user-facing API for the picoNet library.
"""

import time
import collections
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any

from .socket import PicoSocket
from .packet import Packet, PacketHeader, pack_packet, unpack_packet
from .serializer import serialize, deserialize

# --- Constants for the handshake protocol ---
HANDSHAKE_CHALLENGE = b'\xDE\xAD\xBE\xEF'
HANDSHAKE_RESPONSE = b'\xCA\xFE\xBA\xBE'
HANDSHAKE_TIMEOUT = 5.0
HANDSHAKE_RESEND_INTERVAL = 1.0

class ConnectionState(Enum):
    """Represents the different states of the connection."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()

def is_sequence_greater(s1: int, s2: int) -> bool:
    """
    Compares two sequence numbers, accounting for wrapping.
    Returns True if s1 is greater than s2.
    """
    return ((s1 > s2) and (s1 - s2 <= 32768)) or \
           ((s1 < s2) and (s2 - s1 > 32768))

class Connection:
    """
    Manages a connection to a single remote host, providing a reliable layer
    over the underlying UDP socket.
    """
    def __init__(self, host: str, port: int):
        """
        Initializes the connection object. Does not establish a connection yet.

        Args:
            host: The IP address of the remote host.
            port: The port of the remote host.
        """
        self.remote_address = (host, port)
        self._socket = PicoSocket('0.0.0.0', 0)

        # Connection State
        self.state = ConnectionState.DISCONNECTED
        self.timeout = 5.0  # Seconds before considering a connection timed out
        self.last_receive_time = 0.0
        self.rtt = 0.1  # Smoothed Round-Trip Time, starts at 100ms
        self._handshake_start_time = 0.0
        self._last_handshake_send_time = 0.0

        # Packet Sequencing (Outgoing)
        self._sequence_number = 0

        # Packet Sequencing (Incoming)
        self._remote_sequence_number = -1 # The latest sequence number received from the remote host
        self._ack_bitfield = 0

        # Reliability Management
        self._sent_packets: Dict[int, Tuple[float, bytes]] = {}
        self._received_sequences: collections.deque = collections.deque(maxlen=32)
        self._received_payloads: collections.deque = collections.deque()

    @property
    def is_connected(self) -> bool:
        """Returns True if the connection state is CONNECTED."""
        return self.state == ConnectionState.CONNECTED

    def connect(self):
        """
        Begins the connection process by sending a handshake challenge.
        The connection is not established until a response is received, which is
        handled in the update() loop.
        """
        if self.state != ConnectionState.DISCONNECTED:
            return

        print(f"Starting connection handshake with {self.remote_address}...")
        self.state = ConnectionState.CONNECTING
        self._handshake_start_time = time.time()
        self._send_handshake_challenge()

    def _send_handshake_challenge(self):
        """Sends the initial handshake packet."""
        self._socket.send(self.remote_address, HANDSHAKE_CHALLENGE)
        self._last_handshake_send_time = time.time()

    def send(self, payload: Any):
        """
        Serializes and sends a payload to the remote host. Only works if the
        connection is fully established.
        """
        if self.state != ConnectionState.CONNECTED:
            return

        ack_to_send = self._remote_sequence_number if self._remote_sequence_number != -1 else 0
        header = PacketHeader(
            protocol_id=12345,
            sequence=self._sequence_number,
            ack=ack_to_send,
            ack_bitfield=self._ack_bitfield
        )
        packet = Packet(header=header, payload=serialize(payload))
        packed_data = pack_packet(packet)
        self._socket.send(self.remote_address, packed_data)
        self._sent_packets[self._sequence_number] = (time.time(), packed_data)
        self._sequence_number = (self._sequence_number + 1) % 65536

    def receive(self) -> List[Any]:
        """
        Deserializes and returns all pending payloads received from the remote host.
        """
        payloads = list(self._received_payloads)
        self._received_payloads.clear()
        return payloads

    def update(self, dt: float):
        """
        The main update loop for the connection. This must be called regularly.
        """
        # Handle state-specific logic for timeouts and resends
        if self.state == ConnectionState.CONNECTING:
            if time.time() - self._handshake_start_time > HANDSHAKE_TIMEOUT:
                print("Handshake timed out.")
                self.state = ConnectionState.DISCONNECTED
                return
            if time.time() - self._last_handshake_send_time > HANDSHAKE_RESEND_INTERVAL:
                self._send_handshake_challenge()
        
        if self.state == ConnectionState.CONNECTED:
            if time.time() - self.last_receive_time > self.timeout:
                print("Connection timed out.")
                self.state = ConnectionState.DISCONNECTED
                return

        # Receive and process all incoming packets
        self._receive_packets()

        # If connected, resend any lost application packets
        if self.state == ConnectionState.CONNECTED:
            self._resend_lost_packets()
    
    def _receive_packets(self):
        """Internal helper to process all data waiting on the socket."""
        while True:
            received = self._socket.receive()
            if received is None:
                break

            data, address = received
            
            # --- Handshake Packet Handling ---
            # This logic is processed regardless of the current connection state,
            # making the handshake robust and idempotent.
            if data == HANDSHAKE_CHALLENGE:
                # A peer has initiated or re-sent a connection request.
                print(f"Received handshake challenge from {address}. Sending response.")
                if self.state == ConnectionState.DISCONNECTED:
                    # This is a new connection from our perspective (acting as server).
                    self.remote_address = address
                    self.state = ConnectionState.CONNECTED
                    self.last_receive_time = time.time()
                    self._remote_sequence_number = -1
                    self._sequence_number = 0
                self._socket.send(address, HANDSHAKE_RESPONSE)
                continue # Handshake packet processed.

            if data == HANDSHAKE_RESPONSE:
                # We received a response to our challenge.
                if self.state == ConnectionState.CONNECTING and address == self.remote_address:
                    print("Handshake successful. Connection established.")
                    self.state = ConnectionState.CONNECTED
                    self.last_receive_time = time.time()
                continue # Handshake packet processed.

            # --- Application Packet Handling ---
            # If we are not fully connected, ignore any non-handshake packets.
            if self.state != ConnectionState.CONNECTED or address != self.remote_address:
                continue

            try:
                packet = unpack_packet(data)
                self.last_receive_time = time.time()
                self._process_received_packet(packet)
            except (ValueError, TypeError):
                print("Received a malformed packet.")
                continue

    def _process_received_packet(self, packet: Packet):
        """Processes a single, valid, application-level packet."""
        seq = packet.header.sequence
        self._process_acks(packet.header.ack, packet.header.ack_bitfield)

        if seq in self._received_sequences:
            return
        
        self._received_sequences.append(seq)
        self._received_payloads.append(deserialize(packet.payload))

        if self._remote_sequence_number == -1 or is_sequence_greater(seq, self._remote_sequence_number):
            if self._remote_sequence_number != -1:
                diff = seq - self._remote_sequence_number
                if diff <= 16:
                    # A new latest packet has arrived. Shift the existing bitfield
                    # to match the new sequence number and mark the bit for the
                    # *previous* latest sequence number as received.
                    self._ack_bitfield = (self._ack_bitfield << diff) | (1 << (diff - 1))
                else:
                    # The gap is too large; the old bitfield is irrelevant.
                    self._ack_bitfield = 0
            self._remote_sequence_number = seq
        else:
            # An older packet arrived out of order. Mark its bit.
            diff = self._remote_sequence_number - seq
            if diff <= 16:
                self._ack_bitfield |= (1 << (diff - 1))

    def _process_acks(self, ack: int, bitfield: int):
        """Removes acknowledged packets from the sent packets buffer."""
        if ack in self._sent_packets:
            del self._sent_packets[ack]
        for i in range(16):
            if (bitfield >> i) & 1:
                seq_to_ack = (ack - 1 - i) % 65536
                if seq_to_ack in self._sent_packets:
                    del self._sent_packets[seq_to_ack]
    
    def _resend_lost_packets(self):
        """Iterates through sent packets and resends those that are likely lost."""
        timeout_threshold = self.rtt * 1.5 
        now = time.time()
        for seq, (sent_time, data) in list(self._sent_packets.items()):
            if now - sent_time > timeout_threshold:
                print(f"Resending likely lost packet: {seq}")
                self._socket.send(self.remote_address, data)
                self._sent_packets[seq] = (now, data)

    def close(self):
        """Closes the underlying socket."""
        self.state = ConnectionState.DISCONNECTED
        self._socket.close()


