#!/usr/bin/python3

import unittest
import sys
import io
import tcp_multi_connections
from unittest import mock


class TestPortOutputer(unittest.TestCase):
    @mock.patch('tcp_multi_connections.PortOutputer',
                return_value=None)
    def setUp(self, mock_portoutputer):
        suppress_text = io.StringIO()
        sys.stdout = suppress_text
        self.port_outputer = tcp_multi_connections.PortOutputer()

