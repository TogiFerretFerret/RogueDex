"""
picoNet/connection.py

Provides the main Connection class, which manages the state of a connection
to a remote host and handles the reliability layer. This is the primary
user-facing API for the picoNet library.
"""

import time
import collections
from typing import Dict, List, Optional, Tuple, Any

from .socket import PicoSocket
from .packet import Packet, PacketHeader, pack_packet, unpack_packet
from .serializer import serialize, deserialize

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
        # We bind to port 0 to let the OS choose an ephemeral port for us.
        self._socket = PicoSocket('0.0.0.0', 0)

        # Connection State
        self.is_connected = False
        self.timeout = 5.0  # Seconds before considering a connection timed out
        self.last_receive_time = 0.0
        self.rtt = 0.1  # Smoothed Round-Trip Time, starts at 100ms

        # Packet Sequencing (Outgoing)
        self._sequence_number = 0

        # Packet Sequencing (Incoming)
        self._remote_sequence_number = -1 # The latest sequence number received from the remote host
        self._ack_bitfield = 0

        # Reliability Management
        # A dictionary to store reliable packets that have been sent but not yet ACKed.
        # {sequence_number: (send_time, packed_packet_data)}
        self._sent_packets: Dict[int, Tuple[float, bytes]] = {}

        # A queue for payloads received from the remote host that are ready to be
        # processed by the application layer.
        self._received_payloads: collections.deque = collections.deque()

    def connect(self):
        """
        Establishes the connection with the remote host.
        (For now, this is a placeholder. A real implementation would have a
        handshake protocol.)
        """
        print(f"Attempting to 'connect' to {self.remote_address}...")
        self.is_connected = True
        self.last_receive_time = time.time()

    def send(self, payload: Any):
        """
        Serializes and sends a payload to the remote host.
        """
        if not self.is_connected:
            return

        # Sanitize the ack number for packing. -1 is a sentinel value for
        # "no packets received yet" and is invalid for an unsigned short.
        ack_to_send = self._remote_sequence_number if self._remote_sequence_number != -1 else 0

        header = PacketHeader(
            protocol_id=12345, # Our project's magic number
            sequence=self._sequence_number,
            ack=ack_to_send,
            ack_bitfield=self._ack_bitfield
        )
        packet = Packet(header=header, payload=serialize(payload))
        packed_data = pack_packet(packet)

        self._socket.send(self.remote_address, packed_data)

        # Store the packet for reliability tracking
        self._sent_packets[self._sequence_number] = (time.time(), packed_data)
        
        # Increment sequence number, handling wrap-around
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
        It handles receiving packets, processing ACKs, and resending lost packets.

        Args:
            dt: The time delta since the last update call.
        """
        if not self.is_connected:
            return

        # 1. Check for connection timeout
        if time.time() - self.last_receive_time > self.timeout:
            print("Connection timed out.")
            self.is_connected = False
            return

        # 2. Receive all incoming packets from the socket
        while True:
            received = self._socket.receive()
            if received is None:
                break # No more data to read

            data, address = received
            if address != self.remote_address:
                continue # Ignore packets from unknown sources

            try:
                packet = unpack_packet(data)
                self.last_receive_time = time.time()
                self._process_received_packet(packet)
            except (ValueError, TypeError):
                print("Received a malformed packet.")
                continue

        # 3. Resend any lost packets
        self._resend_lost_packets()


    def _process_received_packet(self, packet: Packet):
        """Processes a single, valid packet received from the remote host."""
        # Update our record of which packets the remote host has received
        self._process_acks(packet.header.ack, packet.header.ack_bitfield)

        # Update our incoming sequence number and bitfield
        if self._remote_sequence_number == -1 or is_sequence_greater(packet.header.sequence, self._remote_sequence_number):
            diff = packet.header.sequence - self._remote_sequence_number if self._remote_sequence_number != -1 else 1
            self._ack_bitfield = (self._ack_bitfield << diff) | (1 << (diff - 1)) if diff > 0 else 0
            self._remote_sequence_number = packet.header.sequence
        else:
            diff = self._remote_sequence_number - packet.header.sequence
            if diff <= 16:
                self._ack_bitfield |= (1 << (diff - 1))
        
        # Add the payload to the queue for the application to process
        self._received_payloads.append(deserialize(packet.payload))

    def _process_acks(self, ack: int, bitfield: int):
        """Removes acknowledged packets from the sent packets buffer."""
        # The main ACK number acknowledges the latest packet they received
        if ack in self._sent_packets:
            del self._sent_packets[ack]
        
        # The bitfield acknowledges the 16 packets before the main ACK
        for i in range(16):
            if (bitfield >> i) & 1:
                seq_to_ack = (ack - 1 - i) % 65535
                if seq_to_ack in self._sent_packets:
                    del self._sent_packets[seq_to_ack]
    
    def _resend_lost_packets(self):
        """Iterates through sent packets and resends those that are likely lost."""
        # A simple loss detection: if a packet hasn't been ACKed after 1.5x the RTT,
        # assume it's lost and resend it.
        timeout_threshold = self.rtt * 1.5 
        now = time.time()
        for seq, (sent_time, data) in list(self._sent_packets.items()):
            if now - sent_time > timeout_threshold:
                print(f"Resending likely lost packet: {seq}")
                self._socket.send(self.remote_address, data)
                # We should update the sent_time to avoid resending in a tight loop
                self._sent_packets[seq] = (now, data)


    def close(self):
        """
        Closes the underlying socket.
        """
        self._socket.close()


