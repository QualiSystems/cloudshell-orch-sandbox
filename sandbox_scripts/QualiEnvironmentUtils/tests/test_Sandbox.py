import unittest
from mock import patch, Mock
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
from cloudshell.api.cloudshell_api import ReservationDescriptionInfo
import json
import os

resContext = '''{"id":"5487c6ce-d0b3-43e9-8ee7-e27af8406905",
 "ownerUser":"bob",
 "ownerPass":"nIqm+BG6ZGJjby5hUittVFFJASc=",
 "domain":"Global",
 "environmentName":"My environment",
 "description":"New demo environment",
 "parameters":
   { "globalInputs": [],
     "resourceRequirements":[],
     "resourceAdditionalInfo":[]}}'''

conContext = '''{"serverAddress": "localhost",
"adminAuthToken": "anAdminToken"}'''


class SandboxTests(unittest.TestCase):
    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    def setUp(self, mock_api_session):
        os.environ['reservationContext'] = resContext
        os.environ['qualiConnectivityContext'] = conContext
        tli = Mock()
        tli.Topologies = ["My environment"]
        mock_api_session.return_value.GetActiveTopologyNames = Mock(return_value=tli)

        abstractinfo = Mock()
        abstractinfo.Alias = "alias"
        topoinfo = Mock()

        topoinfo.Name = "My environment"
        topoinfo.AbstractResources = [abstractinfo]
        mock_api_session.return_value.GetTopologyDetails = Mock(return_value=topoinfo)
        mock_logger = Mock()
        self.sandbox = SandboxBase(reservation_id="5487c6ce-d0b3-43e9-8ee7-e27af8406905", logger=mock_logger)

        self.mock_api_session = mock_api_session
        self.mock_logger = mock_logger

    def tearDown(self):
        pass


    #test report_error function
    def test_report_error_without_raising_error_and_without_output(self):
        try:
            self.sandbox.report_error(error_message="error message",
                                      raise_error=False,
                                      write_to_output_window=False)
        except Exception as e:
            self.fail("Got an exception while not expecting to: " + e.message)

        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()

    def test_report_error_with_raising_error_and_without_output(self):
        with self.assertRaises(QualiError) as e:
            self.sandbox.report_error(error_message="error message",
                                      raise_error=True,
                                      write_to_output_window=False)

        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         "CloudShell error at 5487c6ce-d0b3-43e9-8ee7-e27af8406905. Error is: error message")
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()

    def test_report_error_without_raising_error_and_with_output(self):
        self.sandbox.report_error(error_message="error message",
                                  raise_error=False,
                                  write_to_output_window=True)

        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_called_with(
            '5487c6ce-d0b3-43e9-8ee7-e27af8406905', '<font color="red">error message</font>')

    def test_report_error_with_just_to_log(self):
        self.sandbox.report_error(error_message="error message",
                                  raise_error=False,
                                  write_to_output_window=False)

        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()
        self.mock_logger.error.assert_called_with('error message')

    #test report_info function


    #test get_root_resources
    def test_no_resources_in_sandbox(self):
        rdi = Mock()
        rdi.ReservationDescription = Mock()
        rdi.ReservationDescription.Resources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        self.assertEqual(resources, [], "got resources, excepted none")

    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_get_root_resources_without_sub_resources(self, mock_resourcebase):
        rdi = Mock()
        resource1 = Mock()
        resource1.Name = "r1"
        resource1a = Mock()
        resource1a.Name = "r1/r2"
        resource2 = Mock()
        resource2.Name = "r2"
        rdi.ReservationDescription.Resources = [resource1, resource1a, resource2]
        rdi.ReservationDescription.TopologiesReservedResources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        self.assertEqual(len(resources), 2, "didn't get resources, excepted two")

    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_get_root_resources_without_sub_resources_and_with_alias(self, mock_resourcebase):
        rdi = Mock()
        resource1 = Mock()
        resource1.Name = "r1"
        trr = Mock()
        trr.Name = "r1"
        trr.Alias = "my r1"
        trr.TopologyName = "My environment"
        rdi.ReservationDescription.Resources = [resource1]
        rdi.ReservationDescription.TopologiesReservedResources = [trr]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        mock_resourcebase.assert_called_with('r1', 'my r1')
        self.assertEqual(len(resources), 1, "didn't get resources, excepted one")




if __name__ == '__main__':
    unittest.main()
