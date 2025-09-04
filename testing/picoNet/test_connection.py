"""
testing/picoNet/test_connection.py

Unit tests for the picoNet.connection module.
"""

import unittest
import time
import sys
import os
from unittest.mock import patch

# Add the root project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from picoNet.connection import Connection

class TestConnection(unittest.TestCase):
    """
    Test suite for the Connection class.
    """

    def setUp(self):
        """
        Set up two Connection objects for testing. They will be configured
        to send packets to each other.
        """
        print("\nSetting up connections for test...")
        # We use 'localhost' which resolves to 127.0.0.1
        self.conn_a = Connection('localhost', 50001)
        self.conn_b = Connection('localhost', 50002)

        # Manually set the remote addresses to point to each other
        self.conn_a.remote_address = self.conn_b._socket.socket.getsockname()
        self.conn_b.remote_address = self.conn_a._socket.socket.getsockname()
        
        # "Connect" them
        self.conn_a.connect()
        self.conn_b.connect()

    def tearDown(self):
        """
        Clean up and close connection sockets after each test.
        """
        print("Tearing down connections.")
        self.conn_a.close()
        self.conn_b.close()

    def test_send_and_receive_single_packet(self):
        """
        Tests that a single payload sent from A is correctly received by B.
        """
        print("Running test_send_and_receive_single_packet...")
        payload_to_send = {'message': 'hello', 'data': 123}
        
        # 1. A sends a packet to B
        self.conn_a.send(payload_to_send)
        
        # 2. A's update loop should process the send queue (conceptually)
        self.conn_a.update(0.01)

        # 3. Give time for the packet to travel
        time.sleep(0.01)

        # 4. B's update loop should receive the packet from the socket
        self.conn_b.update(0.01)
        
        # 5. B retrieves the payload from its internal queue
        received_payloads = self.conn_b.receive()
        
        # 6. Assertions
        self.assertEqual(len(received_payloads), 1, "Should have received exactly one payload.")
        self.assertEqual(received_payloads[0], payload_to_send, "Received payload does not match sent payload.")
        print("Single packet send/receive successful.")

    def test_ack_processing(self):
        """
        Tests that a packet sent from A is ACKed by B, clearing it from A's sent buffer.
        """
        print("Running test_ack_processing...")
        # 1. A sends a packet to B
        self.conn_a.send({'initial_message': 'from A'})
        self.conn_a.update(0.01)
        self.assertEqual(len(self.conn_a._sent_packets), 1, "Packet should be in A's sent buffer before ACK.")
        
        time.sleep(0.01)
        
        # 2. B receives A's packet and sends one back. This response will contain the ACK.
        self.conn_b.update(0.01) # B processes the packet from A
        self.conn_b.send({'response': 'from B'})
        self.conn_b.update(0.01) # B sends its response
        
        time.sleep(0.01)
        
        # 3. A receives B's packet, which implicitly ACKs A's original packet.
        self.conn_a.update(0.01)
        
        # 4. Assert that A's sent buffer is now empty for that packet.
        self.assertEqual(len(self.conn_a._sent_packets), 0, "Packet should be cleared from A's sent buffer after being ACKed.")
        print("ACK processing successful.")
    
    @patch('picoNet.socket.PicoSocket.send')
    def test_packet_loss_and_resend(self, mock_send):
        """
        Tests the packet resend logic by simulating packet loss.
        """
        print("Running test_packet_loss_and_resend...")
        # Set a very low RTT to speed up the test
        self.conn_a.rtt = 0.05
        
        # 1. A sends a packet. We use the mock to track the 'send' call.
        self.conn_a.send({'important_data': 'must arrive'})
        
        # 2. Let enough time pass for the packet to be considered "lost".
        # We DON'T call conn_b.update(), simulating the packet never arriving at B.
        time.sleep(self.conn_a.rtt * 1.6) # Wait for 1.6x the RTT
        
        # 3. Call A's update loop, which should trigger the resend logic.
        self.conn_a.update(0.01)
        
        # 4. Assert that the socket's send method was called at least twice:
        #    once for the original send, and at least once for the resend.
        self.assertGreaterEqual(mock_send.call_count, 2, "Socket.send() should have been called for original send and resend.")
        print("Packet resend successful.")

    def test_connection_timeout(self):
        """
        Tests that the connection times out if no packets are received.
        """
        print("Running test_connection_timeout...")
        # Set a very short timeout for the test
        self.conn_a.timeout = 0.1
        self.assertTrue(self.conn_a.is_connected, "Connection should be active initially.")
        
        # Wait for longer than the timeout period without any traffic
        time.sleep(0.15)
        
        # Call the update loop, which should detect the timeout
        self.conn_a.update(0.01)
        
        self.assertFalse(self.conn_a.is_connected, "Connection should be timed out.")
        print("Connection timeout successful.")


if __name__ == '__main__':
    unittest.main()

