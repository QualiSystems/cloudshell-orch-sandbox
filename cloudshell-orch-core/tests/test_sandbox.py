import logging
import unittest

from cloudshell.api import cloudshell_api
from cloudshell.core.logger import qs_logger, interprocess_logger
from cloudshell.core.logger.qs_logger import get_qs_logger
import multiprocessing
from cloudshell.workflow.orchestration.sandbox import Sandbox

import sys

if (sys.version_info >= (3,0)):
    from unittest.mock import MagicMock, patch
    from unittest import TestCase, mock
else:
    from mock import MagicMock, patch
    import mock
    from unittest import TestCase


class TestSandbox(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict('os.environ', {
            'qualiConnectivityContext': '{"tsAPIPort": "8028","adminPass": "admin", "adminUser": "admin", "serverAddress":"localhost"}',
            'reservationLifecycleContext': '{"reservationId":"be015364-9640-4ac5-b6ca-f26e1c6d44c8", "savedSandboxName":"empty", "savedSandboxDescription":"","currentUserName":"admin"}',
            'reservationContext': '{"environmentName":"","runningUser":"admin", "environmentPath":"Global Topologies/empty","domain":"Global", "description":"","parameters":{"resourceRequirements":[],"globalInputs":[{"parameterName": "in1", "value": "222"},{"parameterName": "in2", "value": "0"}],"resourceAdditionalInfo":[]},"ownerUser":"admin","ownerPass":"admin","id":"be015364-9640-4ac5-b6ca-f26e1c6d44c8","permittedUsers":[{"userName":"admin", "email":"None"}]}',
            'MY_PARAM': 'PARAM-VALUE'})
        patcher.start()

    def tearDown(self):
        patch.stopall()

    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    @patch.object(interprocess_logger, 'MultiProcessingLog') #without it getting errors like: Error in atexit._run_exitfuncs
    @patch.object(cloudshell_api, 'GetReservationDescriptionResponseInfo')
    def test_sandbox_inputs(self, automation_api, logger, details):
        # automation_api.return_value = 'test-val-1'
        # details.ReservationDescription.Id = 'be015364-9640-4ac5-b6ca-f26e1c6d44c8'
        # automation_api.GetReservationDetails.return_value = details
        sandbox = Sandbox()
        param = sandbox.get_user_param('MY_PARAM')
        self.assertEqual(param, "PARAM-VALUE")