#!/usr/bin/python3

import unittest
from datetime import timedelta
import tcp_multi_connections


class TestPortOutputer(unittest.TestCase):
    """
    Unit test for PortOutputer
    """

    def test_generate_result_pass(self):
        """
        Test if port test pass.
        """
        list_status = {
            0: {'time': timedelta(seconds=5), 'status': True},
            1: {'time': timedelta(seconds=10), 'status': True},
            2: {'time': timedelta(seconds=3), 'status': True},
        }
        port_outputer = tcp_multi_connections.PortOutputer(
            port=123,
            list_status=list_status)

        result = port_outputer.generate_result()
        self.assertEqual(result['port'], 123)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['message'], 'Received payload correct!')
        self.assertEqual(result['total_period'],
                         timedelta(seconds=18))
        self.assertEqual(result['avg_period'], timedelta(seconds=6))
        self.assertEqual(result['max_period'], timedelta(seconds=10))
        self.assertEqual(result['min_period'], timedelta(seconds=3))

    def test_generate_result_fail(self):
        """
        Test if port test fail.
        """
        list_status = {
            0: {'time': timedelta(seconds=5), 'status': True},
            1: {'time': timedelta(seconds=10), 'status': False},
            2: {'time': timedelta(seconds=3), 'status': True},
        }
        port_outputer = tcp_multi_connections.PortOutputer(
            port=123,
            list_status=list_status)

        result = port_outputer.generate_result()
        self.assertEqual(result['port'], 123)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['message'], 'Received payload incorrect!')
        self.assertEqual(result['total_period'],
                         timedelta(seconds=18))
        self.assertEqual(result['avg_period'], timedelta(seconds=6))
        self.assertEqual(result['max_period'], timedelta(seconds=10))
        self.assertEqual(result['min_period'], timedelta(seconds=3))

    def test_generate_result_error(self):
        """
        Test if port test with error.
        """
        port_outputer = tcp_multi_connections.PortOutputer(
            port=123,
            message="Connection error!"
            )

        result = port_outputer.generate_result()
        self.assertEqual(result['port'], 123)
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['message'], 'Connection error!')
        self.assertEqual(result['total_period'], None)
        self.assertEqual(result['avg_period'], None)
        self.assertEqual(result['max_period'], None)
        self.assertEqual(result['min_period'], None)


if __name__ == '__main__':
    unittest.main()
