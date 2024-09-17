#!/usr/bin/python3

import unittest
import subprocess
from unittest.mock import patch, mock_open, Mock, MagicMock
import logging
import sys
import io

from cpufreq_governors import (
    CPUScalingHandler,
    CPUScalingTest,
    init_logger,
    probe_governor_module,
    stress_cpus,
    stop_stress_cpus,
    context_stress_cpus,
)


class TestInitLogger(unittest.TestCase):
    @patch("logging.StreamHandler")
    @patch("logging.Formatter")
    @patch("logging.getLogger")
    def test_init_logger(
        self, mock_get_logger, mock_formatter, mock_stream_handler
    ):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        returned_logger = init_logger()

        self.assertEqual(returned_logger, mock_logger)

        # Directly accessing the methods on the mock object
        mock_stream_handler_instance = mock_stream_handler.return_value
        mock_formatter_instance = mock_formatter.return_value

        # Check if setFormatter is called with the mock formatter
        mock_stream_handler_instance.setFormatter.assert_called_with(
            mock_formatter_instance
        )
        self.assertEqual(mock_logger.addHandler.call_count, 2)


class TestProbeGovernorModule(unittest.TestCase):
    @patch("subprocess.check_call")
    @patch("sys.exit")
    @patch("logging.info")
    def test_probe_governor_module_success(
        self, mock_logging_info, mock_sys_exit, mock_subprocess_check_call
    ):
        mock_subprocess_check_call.return_value = None

        probe_governor_module("ondemand")

        mock_logging_info.assert_called_with("Probe module Successfully!")
        # Ensure sys.exit was not called
        mock_sys_exit.assert_not_called()

    @patch("subprocess.check_call")
    @patch("sys.exit")
    @patch("logging.error")
    def test_probe_governor_module_error(
        self, mock_logging_error, mock_sys_exit, mock_subprocess_check_call
    ):
        mock_subprocess_check_call.side_effect = subprocess.CalledProcessError(
            1, "modprobe"
        )

        probe_governor_module("invalid_governor")

        mock_logging_error.assert_called_with(
            "%s governor not supported", "invalid_governor"
        )
        # Ensure sys.exit was called with 1
        mock_sys_exit.assert_called_with(1)


class TestCPUSStress(unittest.TestCase):
    @patch("cpufreq_governors.subprocess.Popen")
    @patch("cpufreq_governors.cpu_count")
    def test_stress_cpus(self, mock_cpu_count, mock_popen):
        mock_cpu_count.return_value = 4  # Simulating 4 CPU cores
        mock_popen_instance = MagicMock()
        mock_popen.return_value = (
            mock_popen_instance  # Mocking the Popen object
        )

        stress_cpus()

        # Assert that the Popen was called 4 times
        self.assertEqual(mock_popen.call_count, 4)
        # Check if the Popen was called with the correct command
        mock_popen.assert_called_with(["dd", "if=/dev/zero", "of=/dev/null"])

    @patch("cpufreq_governors.subprocess.Popen")
    def test_stop_stress_cpus(self, mock_popen):
        # Mocking a list of mock Popen objects
        mock_processes = [
            MagicMock() for _ in range(4)
        ]  # Simulating 4 CPU cores

        stop_stress_cpus(mock_processes)

        for mock_process in mock_processes:
            self.assertEqual(mock_process.terminate.call_count, 1)
            self.assertEqual(mock_process.wait.call_count, 1)

    @patch("cpufreq_governors.stress_cpus")
    def test_context_stress_cpus(self, mock_stress_cpus):
        # Mocking the return value of stress_cpus
        mock_stress_cpus.return_value = [
            MagicMock() for _ in range(4)
        ]  # Simulating 4 CPU cores

        # Using the context manager for context_stress_cpus
        with context_stress_cpus():
            pass

        self.assertEqual(mock_stress_cpus.call_count, 1)


class TestCPUScalingHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_stdout = sys.stdout
        suppress_text = io.StringIO()
        sys.stdout = suppress_text
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.cpu_scaling_info = CPUScalingHandler()
        self.cpu_scaling_info.sys_cpu_dir = "/sys/devices/system/cpu"

    @classmethod
    def tearDownClass(cls):
        sys.stdout = cls.original_stdout
        logging.disable(logging.NOTSET)

    @patch("os.listdir")
    def test_get_cpu_policies_success(self, mock_listdir):
        """Check if a sorted list contains cpu policy number can be returned
        while policies exist.
        """
        mock_listdir.return_value = ["policy0", "policy1", "policy2"]

        policies = self.cpu_scaling_info.get_cpu_policies()

        self.assertEqual(policies, [0, 1, 2])

    @patch("os.listdir")
    def test_get_cpu_policies_failure(self, mock_listdir):
        """Check if an empty list be returned while OSError"""
        # Mock the listdir function to raise an OSError
        mock_listdir.side_effect = OSError("OSError")

        result = self.cpu_scaling_info.get_cpu_policies()

        self.assertEqual(result, [])

    @patch("os.listdir")
    def test_get_cpu_policies_failure_empty(self, mock_listdir):
        """Check if an empty list be returned while no policy exists"""
        # Mock the listdir function to return an empty list
        mock_listdir.return_value = []

        result = self.cpu_scaling_info.get_cpu_policies()

        self.assertEqual(result, [])

    @patch("builtins.open", mock_open(read_data="Driver"))
    def test_get_scaling_driver_success(self):
        """Check if the name of driver be returned"""
        # Mock the open function to return a scaling driver
        result = self.cpu_scaling_info.get_scaling_driver()

        self.assertEqual(result, "Driver")

    @patch("builtins.open")
    def test_get_scaling_driver_oserror(self, mock_open):
        """Check if an empty string be returned while OSError"""
        # Mock the open function to raise an OSError
        mock_open.side_effect = OSError("OSError")

        result = self.cpu_scaling_info.get_scaling_driver()

        self.assertEqual(result, "")

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_scaling_driver",
        return_value="some_driver_name",
    )
    @patch("builtins.print")  # Mock the built-in print function
    def test_print_policies_list_success(
        self, mock_print, mock_get_scaling_driver
    ):
        scaling_info = CPUScalingHandler(policy=0)
        scaling_info.cpu_policies = [0, 1]

        result = scaling_info.print_policies_list()

        mock_get_scaling_driver.assert_any_call(0)
        mock_get_scaling_driver.assert_any_call(1)
        # Ensure that the method returns True when successful
        self.assertTrue(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_scaling_driver",
        return_value="",
    )
    @patch("builtins.print")  # Mock the built-in print function
    def test_print_policies_list_failure(
        self, mock_print, mock_get_scaling_driver
    ):
        scaling_info = CPUScalingHandler(policy=0)

        with patch.object(scaling_info, "cpu_policies", False):
            result = scaling_info.print_policies_list()
            self.assertFalse(result)

    @patch("builtins.open", mock_open(read_data="Attribute_Value"))
    def test_get_attribute_success(self):
        """Check if get_attribute gets the contain of specific node"""
        # Mock the open function to return a attribute value
        result = self.cpu_scaling_info.get_attribute("Attribute")

        self.assertEqual(result, "Attribute_Value")

    @patch("builtins.open", side_effect=OSError)
    def test_get_attribute_oserror(self, mock_open):
        """Check if get_attribute gets an empty string while OSError occurs"""
        # Mock the open function to raise an OSError
        result = self.cpu_scaling_info.get_attribute("Attribute")

        self.assertEqual(result, "")

    @patch("builtins.open", new_callable=mock_open, create=True)
    def test_set_attribute_success(self, mock_open):
        """Check if returns True while setting a value to a specific node"""
        mock_file = mock_open.return_value
        result = self.cpu_scaling_info.set_attribute(
            "attribute_name", "new_value"
        )

        mock_file.write.assert_called_once_with("new_value")
        self.assertTrue(result)

    @patch("builtins.open", side_effect=PermissionError)
    def test_set_attribute_permissionerror(self, mock_open):
        """Check if returns False while PermissionError occurs"""
        # Mock the open function to raise an PermissionError
        result = self.cpu_scaling_info.set_attribute(
            "attribute_name", "new_value"
        )

        self.assertFalse(result)

    @patch("builtins.open", side_effect=OSError)
    def test_set_attribute_oserror(self, mock_open):
        """Check if returns False while OSError occurs"""
        # Mock the open function to raise an OSError
        result = self.cpu_scaling_info.set_attribute(
            "attribute_name", "new_value"
        )

        self.assertFalse(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_attribute",
        return_value=True,
    )
    def test_set_policy_attribute_success(self, mock_set_attribute):
        result = self.cpu_scaling_info.set_policy_attribute(
            "some_attr", "some_value"
        )

        self.assertTrue(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value="1000000",
    )
    def test_get_min_frequency_success(self, mock_get_policy_attribute):
        result = self.cpu_scaling_info.get_min_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_min_freq")

        self.assertEqual(result, 1000000)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value=None,
    )
    def test_get_min_frequency_with_no_frequency(
        self, mock_get_policy_attribute
    ):
        result = self.cpu_scaling_info.get_min_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_min_freq")

        # Expected frequency is 0 when no value is returned
        self.assertEqual(result, 0)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value="1000000",
    )
    def test_get_max_frequency_success(self, mock_get_policy_attribute):
        result = self.cpu_scaling_info.get_max_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_max_freq")

        self.assertEqual(result, 1000000)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value=None,
    )
    def test_get_max_frequency_with_no_frequency(
        self, mock_get_policy_attribute
    ):
        result = self.cpu_scaling_info.get_max_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_max_freq")

        # Expected frequency is 0 when no value is returned
        self.assertEqual(result, 0)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value="1000000",
    )
    def test_get_current_frequency_success(self, mock_get_policy_attribute):
        result = self.cpu_scaling_info.get_current_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_cur_freq")

        self.assertEqual(result, 1000000)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value=None,
    )
    def test_get_current_frequency_with_no_frequency(
        self, mock_get_policy_attribute
    ):
        result = self.cpu_scaling_info.get_current_frequency()

        mock_get_policy_attribute.assert_called_once_with("scaling_cur_freq")

        self.assertEqual(result, 0)

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value="0 1 2 3",
    )
    def test_get_affected_cpus_with_spaces_success(
        self, mock_get_policy_attribute
    ):
        result = self.cpu_scaling_info.get_affected_cpus()

        mock_get_policy_attribute.assert_called_once_with("affected_cpus")

        self.assertEqual(result, ["0", "1", "2", "3"])

    @patch(
        "cpufreq_governors.CPUScalingHandler.get_policy_attribute",
        return_value="",
    )
    def test_get_affected_cpus_with_no_value(self, mock_get_policy_attribute):
        result = self.cpu_scaling_info.get_affected_cpus()

        mock_get_policy_attribute.assert_called_once_with("affected_cpus")

        self.assertEqual(result, [])

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=True,
    )
    def test_set_governor_success(self, mock_set_policy_attribute):
        result = self.cpu_scaling_info.set_governor("ondemand")

        mock_set_policy_attribute.assert_called_once_with(
            "scaling_governor", "ondemand"
        )

        self.assertTrue(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=False,
    )
    def test_set_governor_failure(self, mock_set_policy_attribute):
        result = self.cpu_scaling_info.set_governor("performance")

        mock_set_policy_attribute.assert_called_once_with(
            "scaling_governor", "performance"
        )

        self.assertFalse(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=True,
    )
    def test_context_set_governor_success(self, mock_set_policy_attribute):
        # Using the context manager
        with self.cpu_scaling_info.context_set_governor("ondemand"):
            mock_set_policy_attribute.assert_called_once_with(
                "scaling_governor", "ondemand"
            )

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=False,
    )
    def test_context_set_governor_failure(self, mock_set_policy_attribute):
        # Using the context manager with an expected failure
        try:
            with self.cpu_scaling_info.context_set_governor("performance"):
                mock_set_policy_attribute.assert_called_once_with(
                    "scaling_governor", "performance"
                )
        except SystemExit:
            # Exception caught as expected
            pass
        else:
            self.fail("Expected SystemExit")

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_frequency", return_value=True
    )
    def test_context_set_frequency_success(self, mock_set_frequency):
        # Using the context manager
        with self.cpu_scaling_info.context_set_frequency("1200000"):
            mock_set_frequency.assert_called_once_with("1200000")

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_frequency", return_value=False
    )
    def test_context_set_frequency_failure(self, mock_set_frequency):
        # Using the context manager with an expected failure
        try:
            with self.cpu_scaling_info.context_set_frequency("1200000"):
                mock_set_frequency.assert_called_once_with("1200000")
        except SystemExit:
            # Exception caught as expected
            pass
        else:
            self.fail("Expected SystemExit")

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=True,
    )
    def test_set_frequency_success(self, mock_set_policy_attribute):
        result = self.cpu_scaling_info.set_frequency("1200000")

        mock_set_policy_attribute.assert_called_once_with(
            "scaling_setspeed", "1200000"
        )

        self.assertTrue(result)

    @patch(
        "cpufreq_governors.CPUScalingHandler.set_policy_attribute",
        return_value=False,
    )
    def test_set_frequency_failure(self, mock_set_policy_attribute):
        result = self.cpu_scaling_info.set_frequency("1200000")

        mock_set_policy_attribute.assert_called_once_with(
            "scaling_setspeed", "1200000"
        )

        self.assertFalse(result)


class TestCPUScalingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_print_policy_info(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.affected_cpus = [0, 1, 2]
        mock_handler_instance.min_freq = 1000000  # 1000 kHz
        mock_handler_instance.max_freq = 3000000  # 3000 kHz
        mock_handler_instance.governors = ["governor1", "governor2"]
        mock_handler_instance.original_governor = "original_governor_value"

        mock_cpuscalinghandler.return_value = mock_handler_instance

        cpu_scaling_test = CPUScalingTest(policy=0)
        expected_logs = [
            "INFO:root:## CPUfreq Policy0 Info ##",
            "INFO:root:Affected CPUs:",
            "INFO:root:    cpu0",
            "INFO:root:    cpu1",
            "INFO:root:    cpu2",
            "INFO:root:Supported CPU Frequencies: 1000.0 - 3000.0 MHz",
            "INFO:root:Supported Governors:",
            "INFO:root:    governor1",
            "INFO:root:    governor2",
            "INFO:root:Current Governor: original_governor_value",
        ]
        with self.assertLogs(level="INFO") as lc:
            logging.disable(logging.NOTSET)
            cpu_scaling_test.print_policy_info()
            for i in range(len(expected_logs)):
                self.assertEqual(expected_logs[i], lc.output[i])
            logging.disable(logging.CRITICAL)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_print_policy_info_no_governor(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.affected_cpus = [0, 1, 2]
        mock_handler_instance.min_freq = 1000000  # 1000 kHz
        mock_handler_instance.max_freq = 3000000  # 3000 kHz
        mock_handler_instance.governors = []
        mock_handler_instance.original_governor = "original_governor_value"

        mock_cpuscalinghandler.return_value = mock_handler_instance

        cpu_scaling_test = CPUScalingTest(policy=0)
        expected_logs = [
            "INFO:root:## CPUfreq Policy0 Info ##",
            "INFO:root:Affected CPUs:",
            "INFO:root:    None",
            "INFO:root:Supported CPU Frequencies: 1000.0 - 3000.0 MHz",
            "INFO:root:Supported Governors:",
            "INFO:root:    None",
            "INFO:root:Current Governor: original_governor_value",
        ]
        with self.assertLogs(level="INFO") as lc:
            logging.disable(logging.NOTSET)
            cpu_scaling_test.print_policy_info()
            for i in range(len(expected_logs)):
                self.assertEqual(expected_logs[i], lc.output[i])
            logging.disable(logging.CRITICAL)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_driver_detect_empty_policies(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.cpu_policies = []
        mock_handler_instance.get_scaling_driver.return_value = "driver_a"
        mock_cpuscalinghandler.return_value = mock_handler_instance

        instance = CPUScalingTest(policy=0)
        result = instance.test_driver_detect()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_driver_detect_single_driver(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.cpu_policies = [1, 2]
        mock_handler_instance.get_scaling_driver.return_value = "driver_a"
        mock_cpuscalinghandler.return_value = mock_handler_instance

        instance = CPUScalingTest(policy=0)
        result = instance.test_driver_detect()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_driver_detect_multiple_drivers(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.cpu_policies = [1, 2]
        mock_handler_instance.get_scaling_driver.side_effect = [
            "driver_a",
            "driver_b",
        ]
        mock_cpuscalinghandler.return_value = mock_handler_instance

        instance = CPUScalingTest(policy=0)
        result = instance.test_driver_detect()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingHandler")
    def test_driver_detect_no_drivers_found(self, mock_cpuscalinghandler):
        mock_handler_instance = Mock()
        mock_handler_instance.cpu_policies = [1, 2]
        mock_handler_instance.get_scaling_driver.return_value = []
        mock_cpuscalinghandler.return_value = mock_handler_instance

        instance = CPUScalingTest(policy=0)

        result = instance.test_driver_detect()
        self.assertFalse(result)

    @patch("cpufreq_governors.time")
    def test_is_frequency_equal_to_target_success(self, mock_time):
        # Mocking the current time and the get_current_frequency method
        # This simulates time-based checks
        mock_time.time.side_effect = [0, 0.5, 1]
        instance = CPUScalingTest(policy=0)

        mock_handler = Mock()
        mock_handler.get_current_frequency.return_value = 1000
        instance.handler = mock_handler

        # Set the target frequency to 1000 for this test
        target_freq = 1000

        result = instance.is_frequency_equal_to_target(target_freq)
        self.assertTrue(result)

    @patch("cpufreq_governors.time")
    def test_is_frequency_equal_to_target_timeout(self, mock_time):
        # Mocking the current time and the get_current_frequency method
        # This simulates time-based checks
        mock_time.time.side_effect = [0, 0.5, 11]
        instance = CPUScalingTest(policy=0)

        mock_handler = Mock()
        mock_handler.get_current_frequency.return_value = 900
        instance.handler = mock_handler

        target_freq = 1000

        result = instance.is_frequency_equal_to_target(target_freq)
        self.assertFalse(result)

    @patch("cpufreq_governors.time")
    def test_is_frequency_settled_down_success(self, mock_time):
        # Mocking the current time and the get_current_frequency method
        # This simulates time-based checks
        mock_time.time.side_effect = [0, 0.5, 1]
        instance = CPUScalingTest(policy=0)

        mock_handler = Mock()
        mock_handler.get_current_frequency.return_value = 900
        mock_handler.max_freq = 1000
        instance.handler = mock_handler

        result = instance.is_frequency_settled_down()
        self.assertTrue(result)

    @patch("cpufreq_governors.time")
    def test_is_frequency_settled_down_failure(self, mock_time):
        # Mocking the current time and the get_current_frequency method
        # This simulates time-based checks
        mock_time.time.side_effect = [0, 0.5, 11]
        instance = CPUScalingTest(policy=0)

        # Mocking the get_current_frequency method to return a value
        # greater than or equal to max_freq
        mock_handler = Mock()
        mock_handler.get_current_frequency.return_value = 1100
        mock_handler.max_freq = 1000
        instance.handler = mock_handler

        result = instance.is_frequency_settled_down()
        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_settled_down")
    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.context_stress_cpus")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_ondemand_success(
        self,
        mock_context_set_governor,
        mock_context_stress_cpus,
        mock_is_frequency_equal_to_target,
        mock_is_frequency_settled_down,
    ):
        mock_is_frequency_equal_to_target.return_value = True
        mock_is_frequency_settled_down.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(governor="ondemand")

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_settled_down")
    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.context_stress_cpus")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_ondemand_frequency_not_equal(
        self,
        mock_context_set_governor,
        mock_context_stress_cpus,
        mock_is_frequency_equal_to_target,
        mock_is_frequency_settled_down,
    ):
        mock_is_frequency_equal_to_target.return_value = False
        mock_is_frequency_settled_down.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(governor="ondemand")

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_settled_down")
    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.context_stress_cpus")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_ondemand_settled_down_failure(
        self,
        mock_context_set_governor,
        mock_context_stress_cpus,
        mock_is_frequency_equal_to_target,
        mock_is_frequency_settled_down,
    ):
        mock_is_frequency_equal_to_target.return_value = True
        mock_is_frequency_settled_down.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(governor="ondemand")

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_frequency")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_userspace_success(
        self,
        mock_context_set_governor,
        mock_context_set_frequency,
        mock_is_frequency_equal_to_target,
    ):
        mock_is_frequency_equal_to_target.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(
            governor="userspace", target_freq=1000
        )

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_frequency")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_userspace_failure(
        self,
        mock_context_set_governor,
        mock_context_set_frequency,
        mock_is_frequency_equal_to_target,
    ):
        mock_is_frequency_equal_to_target.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(
            governor="userspace", target_freq=1000
        )

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_performance_success(
        self,
        mock_context_set_governor,
        mock_is_frequency_equal_to_target,
    ):
        mock_is_frequency_equal_to_target.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(
            governor="performance", target_freq=1000
        )

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.is_frequency_equal_to_target")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_performance_failure(
        self,
        mock_context_set_governor,
        mock_is_frequency_equal_to_target,
    ):
        mock_is_frequency_equal_to_target.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_frequency_influence(
            governor="performance", target_freq=1000
        )

        self.assertFalse(result)

    @patch("sys.exit")
    @patch("cpufreq_governors.CPUScalingHandler.context_set_governor")
    def test_frequency_influence_invalid_governor(
        self,
        mock_context_set_governor,
        mock_exit,
    ):
        instance = CPUScalingTest(policy=0)
        instance.test_frequency_influence(governor="no_governor")

        mock_exit.assert_called_with("Governor 'no_governor' not supported")

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_userspace_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.side_effect = [True, True]

        instance = CPUScalingTest(policy=0)
        result = instance.test_userspace()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_userspace_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.side_effect = [False, True]

        instance = CPUScalingTest(policy=0)
        result = instance.test_userspace()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_performance_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_performance()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_performance_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_performance()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_powersave_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_powersave()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_powersave_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_powersave()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_ondemand_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_ondemand()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_ondemand_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_ondemand()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_conservative_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_conservative()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_conservative_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_conservative()

        self.assertFalse(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_schedutil_success(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = True

        instance = CPUScalingTest(policy=0)
        result = instance.test_schedutil()

        self.assertTrue(result)

    @patch("cpufreq_governors.CPUScalingTest.test_frequency_influence")
    def test_test_schedutil_failure(self, mock_test_frequency_influence):
        mock_test_frequency_influence.return_value = False

        instance = CPUScalingTest(policy=0)
        result = instance.test_schedutil()

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
