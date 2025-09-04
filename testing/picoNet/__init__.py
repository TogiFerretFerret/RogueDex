import unittest
import test_packet
import test_serializer
import test_socket

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_packet))
    suite.addTests(loader.loadTestsFromModule(test_serializer))
    suite.addTests(loader.loadTestsFromModule(test_socket))
    runner = unittest.TextTestRunner()
    runner.run(suite)

