
import unittest
import picoNet.test_packet as test_packet
import picoNet.test_serializer as test_serializer
import picoNet.test_socket as test_socket
import picoNet.test_connection as test_connection
import battledex_engine.test_battle_flow as test_battle_flow

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_packet))
    suite.addTests(loader.loadTestsFromModule(test_serializer))
    suite.addTests(loader.loadTestsFromModule(test_socket))
    suite.addTests(loader.loadTestsFromModule(test_connection))
    suite.addTests(loader.loadTestsFromModule(test_battle_flow))
    runner = unittest.TextTestRunner()
    runner.run(suite)

