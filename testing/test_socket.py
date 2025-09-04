"""
testing/test_socket.py

Unit tests for the picoNet.socket module.
"""

import unittest
import sys
import os
import time

# Add the root project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picoNet.socket import PicoSocket

class TestPicoSocket(unittest.TestCase):
    """
    Test suite for the PicoSocket wrapper.
    """

    def setUp(self):
        """
        Set up two sockets for testing communication.
        We bind to port 0 to let the OS choose available ephemeral ports.
        """
        print("\nSetting up sockets for test...")
        self.socket_a = PicoSocket('127.0.0.1', 0)
        self.socket_b = PicoSocket('127.0.0.1', 0)
        self.assertIsNotNone(self.socket_a.socket, "Socket A failed to initialize.")
        self.assertIsNotNone(self.socket_b.socket, "Socket B failed to initialize.")

    def tearDown(self):
        """
        Clean up and close sockets after each test.
        """
        print("Tearing down sockets.")
        self.socket_a.close()
        self.socket_b.close()

    def test_send_receive(self):
        """
        Tests a basic send from socket_a and receive on socket_b.
        """
        print("Running test_send_receive...")
        # 1. Define the message and destination address
        message = b'hello world'
        address_b = self.socket_b.socket.getsockname() # Get the OS-assigned port
        print(f"Socket A is sending '{message.decode()}' to {address_b}")

        # 2. Send the message from A to B
        self.socket_a.send(address_b, message)

        # 3. Give the OS a moment to process the packet
        time.sleep(0.01)

        # 4. Receive the message on socket B
        received = self.socket_b.receive()
        self.assertIsNotNone(received, "Socket B should have received data, but got None.")

        # 5. Unpack the received data and address
        received_data, from_address = received
        print(f"Socket B received '{received_data.decode()}' from {from_address}")

        # 6. Assert that the data is correct
        self.assertEqual(received_data, message, "The received data does not match the sent message.")

        # 7. Assert that the sender address is correct
        address_a = self.socket_a.socket.getsockname()
        self.assertEqual(from_address, address_a, "The sender address is incorrect.")
        print("Send/Receive successful.")

    def test_receive_non_blocking(self):
        """
        Tests that receive() returns None immediately when no data is available,
        verifying its non-blocking behavior.
        """
        print("Running test_receive_non_blocking...")
        # Call receive on a socket that hasn't been sent any data
        received = self.socket_a.receive()

        # Assert that the result is None, not a blocking wait
        self.assertIsNone(received, "receive() should return None when no data is available.")
        print("Non-blocking receive works as expected.")

if __name__ == '__main__':
    unittest.main()

