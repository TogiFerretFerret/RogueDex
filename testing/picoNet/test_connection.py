import unittest
import time
import sys
import os
from unittest.mock import patch

# --- Path Setup ---
# This allows the test to find the picoNet module in the parent directory
# by adding the project's root directory to the Python path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from picoNet.connection import Connection, ConnectionState, PicoSocket

# A small helper to advance time in tests without waiting
def advance_time(duration):
    time.sleep(duration)

class TestConnection(unittest.TestCase):
    """
    Unit tests for the Connection class.
    These tests create two Connection instances that communicate with each other
    on the local machine to verify the handshake, reliability, and state logic.
    """

    def setUp(self):
        """
        Set up two Connection instances for testing.
        conn_a acts as the "client" initiating the connection.
        conn_b acts as the "server" listening for a connection.
        """
        print("\nSetting up connections for test...")
        # Note: We use '127.0.0.1' for explicit local testing
        server_address = ('127.0.0.1', 50001)
        
        # The "server" will listen on a known port.
        # We create a dummy connection object first, then replace its socket.
        self.conn_b = Connection('0.0.0.0', 0) # Target address is irrelevant for server
        self.conn_b._socket.close() # close the OS-assigned one
        self.conn_b._socket = PicoSocket(server_address[0], server_address[1])

        # The "client" will target the server's known port
        self.conn_a = Connection(server_address[0], server_address[1])
        
        print(f"Client (A) is on {self.conn_a._socket.get_address()}")
        print(f"Server (B) is on {self.conn_b._socket.get_address()}")
        
        # --- Handshake Simulation ---
        # 1. Client (A) starts the connection process
        self.conn_a.connect()
        self.assertEqual(self.conn_a.state, ConnectionState.CONNECTING)
        
        # 2. Run update loop until handshake completes or times out
        start_time = time.time()
        timeout = 2.0 # Test-specific timeout
        while not self.conn_a.is_connected and (time.time() - start_time) < timeout:
            self.conn_a.update(0.1)
            self.conn_b.update(0.1)
            advance_time(0.01) # Small delay to prevent tight loop

        # 3. Verify connection was established
        self.assertTrue(self.conn_a.is_connected, "Client (A) failed to connect within the test timeout.")
        self.assertTrue(self.conn_b.is_connected, "Server (B) failed to connect within the test timeout.")
        print("Handshake successful in test setup.")


    def tearDown(self):
        """Clean up by closing the sockets."""
        print("Tearing down connections.")
        self.conn_a.close()
        self.conn_b.close()

    def test_send_and_receive_single_packet(self):
        """Tests that a single payload sent from A is correctly received by B."""
        print("Running test_send_and_receive_single_packet...")
        payload_to_send = {'message': 'hello world', 'id': 1}
        self.conn_a.send(payload_to_send)

        # Allow time for the packet to be processed
        self.conn_a.update(0.1)
        self.conn_b.update(0.1)
        advance_time(0.01)
        self.conn_b.update(0.1) # One more to process the received packet

        received_payloads = self.conn_b.receive()
        self.assertEqual(len(received_payloads), 1, "Should have received exactly one payload.")
        self.assertEqual(received_payloads[0], payload_to_send)
        print("Single packet roundtrip successful.")

    def test_ack_processing(self):
        """Tests that a packet sent from A is ACKed by B, clearing it from A's sent buffer."""
        print("Running test_ack_processing...")
        # 1. A sends a packet to B
        self.conn_a.send({'initial_message': 'from A'})
        self.assertEqual(len(self.conn_a._sent_packets), 1, "Packet should be in A's sent buffer before ACK.")

        # 2. B receives the packet
        self.conn_b.update(0.1)
        advance_time(0.01)

        # 3. B sends a reply, which will carry the ACK for A's first packet
        self.conn_b.send({'reply_message': 'from B'})

        # 4. A receives B's packet and processes the ACK
        self.conn_a.update(0.1)
        self.conn_b.update(0.1) # Let B send its packet
        advance_time(0.01)
        self.conn_a.update(0.1) # Let A process the incoming packet with the ACK

        self.assertEqual(len(self.conn_a._sent_packets), 0, "Packet should be cleared from A's sent buffer after being ACKed.")
        print("ACK processing successful.")
        
    def test_packet_loss_and_resend(self):
        """Tests the packet resend logic by simulating packet loss."""
        print("Running test_packet_loss_and_resend...")
        self.conn_a.rtt = 0.1 # Set a predictable RTT for the test

        # Use mock to "lose" the packet by preventing B's socket from receiving it
        with patch.object(self.conn_b._socket, 'receive', return_value=None):
            self.conn_a.send({'important_data': 'must arrive'})
            self.assertEqual(len(self.conn_a._sent_packets), 1)

            # Let enough time pass for a resend to trigger (rtt * 1.5)
            advance_time(0.2)
            self.conn_a.update(0.2)
        
        # Now, allow B to receive again
        self.conn_b.update(0.1)
        received = self.conn_b.receive()
        self.assertEqual(len(received), 1, "B should have received the packet after it was resent.")
        self.assertEqual(received[0], {'important_data': 'must arrive'})
        print("Packet loss and resend successful.")

    def test_connection_timeout(self):
        """Tests that the connection times out if no packets are received."""
        print("Running test_connection_timeout...")
        self.conn_a.timeout = 0.1 # Set a short timeout for the test
        self.assertTrue(self.conn_a.is_connected, "Connection should be active initially.")

        # Wait longer than the timeout period without any network activity
        advance_time(0.2)
        self.conn_a.update(0.2)

        self.assertFalse(self.conn_a.is_connected, "Connection should have timed out.")
        print("Connection timeout successful.")

if __name__ == '__main__':
    unittest.main()


