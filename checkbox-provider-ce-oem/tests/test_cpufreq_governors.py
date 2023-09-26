#!/usr/bin/python3

import unittest
import subprocess
from unittest import mock
"""
We probbley could remove append path while mirge back to ppc.
Since checkbox has __init__.py for unit tests.
ref:
https://github.com/canonical/checkbox/blob/main/checkbox-support/checkbox_support/tests/__init__.py
"""
import sys
import os

# Add the path to the 'bin' directory for the import to work
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bin'))

from cpufreq_governors import probe_governor_module


class TestProbeGovernorModule(unittest.TestCase):
    def setUp(self):
        self.expected_governor = ["conservative", "powersave", "ondemand",
                                  "userspace", "performance", "schedutil"]

    def test_governor_module_supported(self):
        # Simulate a scenario where all expected governors are supported
        governor = ["conservative", "powersave", "ondemand",
                    "userspace", "performance", "schedutil"]
        # Simulate a successful modprobe
        status = probe_governor_module(governor, self.expected_governor)
        self.assertEqual(status, 0)

    @mock.patch('subprocess.run')
    def test_governor_module_unsupported_and_probe_success(
            self,
            mock_subprocess_run
            ):
        # Simulate a scenario where some governors are not supported.
        # And probe module success.
        # Create a mock subprocess.CompletedProcess object with a
        # return code of 0
        governor = ["powersave", "ondemand",
                    "userspace", "performance", "schedutil"]
        mock_subprocess_run.returncode = 0
        result = probe_governor_module(governor, self.expected_governor)

        self.assertEqual(result, 0)

    @mock.patch('subprocess.run')
    def test_governor_module_unsupported_and_probe_fail(
            self,
            mock_subprocess_run
            ):
        # Simulate a scenario where some governors are not supported.
        # And probe module success.
        # Create a mock subprocess.CompletedProcess object with a
        # return code of 1
        governor = ["powersave", "ondemand",
                    "userspace", "performance", "schedutil"]
        cmd = ["modprobe", "cpufreq_powersave"]
        error_message = "Not able to probe cpufreq_conservative!"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=cmd,
            stderr=error_message
        )
        result = probe_governor_module(governor, self.expected_governor)

        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
