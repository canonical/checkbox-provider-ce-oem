#!/usr/bin/python3

import unittest
from datetime import timedelta, datetime
import tcp_multi_connections
from unittest.mock import patch, Mock, MagicMock
import logging


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


class TestTcpMulitConnections(unittest.TestCase):
    """
    Test TCP mulit-Connections test script
    """

    def test_send_payload_connection_refused(self):
        """
        Test connections refused.
        """
        payload = "test"
        host = '0.0.0.0'
        port = '1234'
        start_time = datetime.now() + timedelta(seconds=1)
        results = []
        result = tcp_multi_connections.send_payload(host, port,
                                                    payload,
                                                    start_time,
                                                    results)
        log = "Connection refused"
        self.assertIn(log, result[0]['message'])

    @patch('socket.create_connection')
    def test_send_payload_success(self,
                                  mock_create_connection,):
        """
        Test send_paylaod success and receive expect payload.
        """
        payload = "test"
        host = '0.0.0.0'
        port = '1234'
        start_time = datetime.now() + timedelta(seconds=1)
        results = []
        mock_socket = Mock(recv=Mock(return_value=payload.encode()))
        mock_create_connection.return_value.__enter__.return_value \
            = mock_socket

        result = tcp_multi_connections.send_payload(host, port,
                                                    payload,
                                                    start_time,
                                                    results)
        self.assertEqual(result[0]['status'], 'PASS')
        self.assertEqual(result[0]['port'], '1234')

    @patch('socket.create_connection')
    def test_send_payload_fail(self,
                               mock_create_connection,):
        """
        Test send_paylaod success and receive unexpect payload.
        """
        payload = "test"
        host = '0.0.0.0'
        port = '1234'
        start_time = datetime.now() + timedelta(seconds=1)
        results = []
        mock_socket = Mock(recv=Mock(return_value="unexpect".encode()))
        mock_create_connection.return_value.__enter__.return_value \
            = mock_socket

        result = tcp_multi_connections.send_payload(host, port,
                                                    payload,
                                                    start_time,
                                                    results)
        self.assertEqual(result[0]['status'], 'FAIL')
        self.assertEqual(result[0]['port'], '1234')


if __name__ == '__main__':
    unittest.main()
