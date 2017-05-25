import unittest
from unittest import TestCase

import logging
from cloudshell.api.cloudshell_api import GetReservationDescriptionResponseInfo, ReservationDescriptionInfo
from mock import patch, Mock

from cloudshell.workflow.orchestration.sandbox import Sandbox
from workflow.orchestration.workflow import Workflow


class test_helpers(object):
    @staticmethod
    def some_function(sandbox, components):
        pass


# class TestSandbox(TestCase):
#     def setUp(self):
#         # from cloudshell.workflow.profiler import env_profiler
#         self.helpers_patcher = patch('cloudshell.workflow.orchestration.sandbox.helpers')
#         self.qs_logger_patcher = patch('cloudshell.workflow.orchestration.sandbox.get_qs_logger')
#         # env_profiler.profileit = Mock()
#
#         self.helpers = self.helpers_patcher.start()
#         self.logger = self.qs_logger_patcher.start()
#
#         self.get_api_session = Mock()
#         self.helpers.get_api_session.return_value = self.get_api_session
#
#         reservation_description = Mock(spec=ReservationDescriptionInfo)
#         reservation_description.Resources = []
#         reservation_description.Services = []
#         reservation_description.Apps = []
#         reservation_details = Mock(spec=GetReservationDescriptionResponseInfo)
#         reservation_details.ReservationDescription = reservation_description
#
#         self.get_api_session.GetReservationDetails.return_value = reservation_details
#
#
#         self.sandbox = Sandbox()
#
#     def test_sandbox_register_workflow_events(self):
#         resources = self.sandbox.components.get_resources_by_model('model_name')
#
#         self.sandbox.workflow.add_to_provisioning(test_helpers.some_function,resources)
#         self.assertEqual(len(self.sandbox.workflow._provisioning_functions), 1)
#
#         self.sandbox.workflow.add_to_connectivity(test_helpers.some_function, resources)
#         self.assertEqual(len(self.sandbox.workflow._connectivity_functions), 1)
#
#         self.sandbox.workflow.add_to_configuration(test_helpers.some_function, resources)
#         self.assertEqual(len(self.sandbox.workflow._configuration_functions), 1)
#
#         self.sandbox.workflow.on_provisioning_ended(test_helpers.some_function, resources)
#         self.assertEqual(len(self.sandbox.workflow._after_provisioning), 1)
#
#         self.sandbox.workflow.on_connectivity_ended(test_helpers.some_function, resources)
#         self.assertEqual(len(self.sandbox.workflow._after_connectivity), 1)
#
#         self.sandbox.workflow.on_configuration_ended(test_helpers.some_function, resources)
#         self.assertEqual(len(self.sandbox.workflow._after_configuration), 1)
#
#     def test_setup_calles_workflow_events(self):
#         resources = self.sandbox.components.get_resources_by_model('model_name')
#         self.sandbox.workflow.add_to_provisioning(test_helpers.some_function, resources)
#
#         self.sandbox.execute_setup()
#
#         assert self.get_api_session.PrepareSandboxConnectivity.called
#         # assert self.helpers.get_api_session.called
#
#         self.logger.info.assert_called_with('Setup execution started')
#         pass
#
#     def tearDown(self):
#         self.helpers_patcher.stop()
#         self.qs_logger_patcher.stop()


class TestSomething(TestCase):
    def test_something(self):
        sandbox = Mock(Sandbox)
        sandbox.logger = Mock(logging.Logger)
        sandbox.workflow = Workflow(sandbox)
        a = test_helpers.some_function
        sandbox.workflow.add_to_provisioning(a, [])
        sandbox.execute_setup()

        sandbox._execute_stage.assert_called_with([a], Workflow.PROVISIONING_STAGE_NAME)


if __name__ == '__main__':
    unittest.main()
