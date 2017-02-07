import unittest
from mock import patch, Mock,call
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
from cloudshell.api.cloudshell_api import ReservationDescriptionInfo
import json
import os
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

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

    #================================================================
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

    #================================================================
    #test report_info function
    def test_report_info_to_log_without_output(self):
        self.sandbox.report_info(message="error message",write_to_output_window=False)
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()
        self.mock_logger.info.assert_called_with('error message')

    def test_report_info_to_log_with_output(self):
        self.sandbox.report_info(message="error message",write_to_output_window=True)
        self.mock_api_session.return_value.WriteMessageToReservationOutput.\
            assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'error message')
        self.mock_logger.info.assert_called_with('error message')


    #================================================================
    #test get_root_resources
    def test_no_resources_in_sandbox(self):
        rdi = Mock()
        rdi.ReservationDescription = Mock()
        rdi.ReservationDescription.Resources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        self.assertEqual(resources, [], "got resources, excepted none")

    #---------------------------
    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_get_root_resources_with_sub_resources(self, mock_resourcebase):
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

    #---------------------------
    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_get_root_resources_with_services_only(self, mock_resourcebase):
        rdi = Mock()
        Service1 = Mock()
        Service1.Name = "s1"
        Service2 = Mock()
        Service2.Name = "s2"
        rdi.ReservationDescription.Services = [Service1,Service2]
        rdi.ReservationDescription.Resources = []
        rdi.ReservationDescription.TopologiesReservedResources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        self.assertEqual(len(resources), 0, "No resources expected")

    #---------------------------
    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_get_root_resources_with_services_and_resource(self, mock_resourcebase):
        rdi = Mock()
        Service1 = Mock()
        Service1.Name = "s1"
        Service2 = Mock()
        Service2.Name = "s2"
        resource1 = Mock()
        resource1.Name = "r1"
        rdi.ReservationDescription.Services = [Service1,Service2]
        rdi.ReservationDescription.Resources = [resource1]
        rdi.ReservationDescription.TopologiesReservedResources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        resources = self.sandbox.get_root_resources()
        self.assertEqual(len(resources), 1, "No resources expected")

    #---------------------------
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

    #================================================================
    #test clear_all_resources_live_status
    def test_clear_all_resources_live_status_no_devices(self):
        rdi = Mock()
        rdi.ReservationDescription.Resources = []
        rdi.ReservationDescription.TopologiesReservedResources = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)

        self.sandbox.clear_all_resources_live_status()
        self.mock_api_session.return_value.SetResourceLiveStatus.assert_not_called()

    #---------------------------
    @patch('sandbox_scripts.QualiEnvironmentUtils.Sandbox.ResourceBase')
    def test_clear_all_resources_live_status_two_devices(self,mock_resourcebase):
        resource1 = Mock()
        resource1.name = "r1"
        resource2 = Mock()
        resource2.name = "r2"
        rr = Mock()
        rr = [resource1, resource2]
        self.sandbox.get_root_resources = Mock(return_value=rr)

        self.sandbox.clear_all_resources_live_status()
        #self.mock_api_session.return_value.SetResourceLiveStatus.assert_called()
        calls = [call('r1', ''),
                 call('r2', '')]
        self.mock_api_session.return_value.SetResourceLiveStatus.assert_has_calls(calls)

    #================================================================
    #test activate_connectors
    def test_activate_connectors_no_connectors_no_output(self):
        rdi = Mock()
        rdi.ReservationDescription.Connectors = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_connectors(False)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_not_called()
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()

    #---------------------------
    def test_activate_connectors_no_connectors_with_output(self):
        rdi = Mock()
        rdi.ReservationDescription.Connectors = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_connectors(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_not_called()
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting the connectors'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'No connectors to connect for reservation 5487c6ce-d0b3-43e9-8ee7-e27af8406905')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #---------------------------
    def test_activate_connectors_with_connectors_with_output(self):
        rdi = Mock()
        connector1 = Mock()
        connector1.State = 'Disconnected'
        connector1.Target = 'x'
        connector1.Source = 'y'
        rdi.ReservationDescription.Connectors = [connector1]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_connectors(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_called()
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting the connectors'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connectors connected')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #---------------------------
    def test_activate_connectors_with_connectors_already_connected_with_output(self):
        rdi = Mock()
        connector1 = Mock()
        connector1.State = 'Connected'
        connector1.Target = 'x'
        connector1.Source = 'y'
        rdi.ReservationDescription.Connectors = [connector1]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_connectors(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_not_called()
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting the connectors'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'No connectors to connect for reservation 5487c6ce-d0b3-43e9-8ee7-e27af8406905')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #---------------------------
    def test_activate_connectors_with_some_of_connectors_already_connected_with_output(self):
        rdi = Mock()
        connector1 = Mock()
        connector1.State = 'Connected'
        connector1.Target = 'x'
        connector1.Source = 'y'
        connector2 = Mock()
        connector2.State = 'ConnectionFailed'
        connector2.Target = 'a'
        connector2.Source = 'z'
        rdi.ReservationDescription.Connectors = [connector1,connector2]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_connectors(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905', ['a', 'z'], 'bi')
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting the connectors'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connectors connected')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #================================================================
    #test activate_routes
    def test_activate_routes_no_routes_no_output(self):
        rdi = Mock()
        rdi.ReservationDescription.RequestedRoutesInfo = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_routes(False)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_not_called()
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_not_called()

    #---------------------------
    def test_activate_routes_no_routes_with_output(self):
        rdi = Mock()
        rdi.ReservationDescription.RequestedRoutesInfo = []
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_routes(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_not_called()
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting routes'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'No routes to connect for reservation 5487c6ce-d0b3-43e9-8ee7-e27af8406905')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #---------------------------
    def test_activate_routes_with_bi_routes_with_output(self):
        rdi = Mock()
        route1 = Mock()
        route1.RouteType = 'bi'
        route1.Target = 'x'
        route1.Source = 'y'
        rdi.ReservationDescription.RequestedRoutesInfo = [route1]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_routes(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905', ['x', 'y'], 'bi')
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting routes'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Routes connected')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #---------------------------
    def test_activate_routes_with_uni_routes_with_output(self):
        rdi = Mock()
        route2 = Mock()
        route2.RouteType = 'uni'
        route2.Target = 'x'
        route2.Source = 'y'
        rdi.ReservationDescription.RequestedRoutesInfo = [route2]
        self.mock_api_session.return_value.GetReservationDetails = Mock(return_value=rdi)
        self.sandbox.activate_routes(True)
        self.mock_api_session.return_value.ConnectRoutesInReservation.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905', ['y', 'x'], 'uni')
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Connecting routes'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'Routes connected')]
        self.mock_api_session.return_value.WriteMessageToReservationOutput.assert_has_calls(calls)

    #================================================================
    #test save as blueprint
    def test_save_sandbox_as_blueprint(self):
        self.sandbox.save_sandbox_as_blueprint('aaa')
        self.mock_api_session.return_value.SaveReservationAsTopology.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905',
                                                                                        folderFullPath='Snapshots',
                                                                                        includeInactiveRoutes=True,
                                                                                        topologyName='aaa')
        self.mock_api_session.return_value.UpdateTopologyOwner.assert_called_with(ownerName='bob', topologyName='Snapshots/aaa')

    # ---------------------------
    def test_save_sandbox_as_blueprint_invalid_topo_name(self):
        self.mock_api_session.return_value.SaveReservationAsTopology.side_effect = CloudShellAPIError(100,"Invalid name","")
        with self.assertRaises(QualiError) as e:
            self.sandbox.save_sandbox_as_blueprint('a@aa')
        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         "CloudShell error at 5487c6ce-d0b3-43e9-8ee7-e27af8406905. Error is: Failed to save sandbox as blueprint. Invalid name")
        self.mock_api_session.return_value.SaveReservationAsTopology.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905',
                                                                                        folderFullPath='Snapshots',
                                                                                        includeInactiveRoutes=True,
                                                                                        topologyName='a@aa')
        self.mock_api_session.return_value.UpdateTopologyOwner.assert_not_called()

    #================================================================
    #test power_on_vms
    def test_power_on_vms_vm_and_resource(self):

        resource1 = Mock()
        resource1.name = "r1"
        resource1.is_app.return_value = True
        resource2 = Mock()
        resource2.name = "r2"
        resource2.is_app.return_value = False
        rr = Mock()
        rr = [resource1, resource2]
        self.sandbox.get_root_resources = Mock(return_value=rr)
        self.sandbox.power_on_vms()
        self.mock_api_session.return_value.ExecuteResourceConnectedCommand.assert_called_with('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'r1', 'PowerOn', 'power')

    # ---------------------------
    def test_power_on_vms_only_vms(self):

        resource1 = Mock()
        resource1.name = "r1"
        resource1.is_app.return_value = True
        resource2 = Mock()
        resource2.name = "r2"
        resource2.is_app.return_value = True
        rr = Mock()
        rr = [resource1, resource2]
        self.sandbox.get_root_resources = Mock(return_value=rr)
        self.sandbox.power_on_vms()
        calls = [call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'r1', 'PowerOn', 'power'),
                 call('5487c6ce-d0b3-43e9-8ee7-e27af8406905', 'r2', 'PowerOn', 'power')]

        self.mock_api_session.return_value.ExecuteResourceConnectedCommand.assert_has_calls(calls)

    # ---------------------------
    def test_power_on_vms_no_vms(self):

        resource1 = Mock()
        resource1.name = "r1"
        resource1.is_app.return_value = False
        resource2 = Mock()
        resource2.name = "r2"
        resource2.is_app.return_value = False
        rr = Mock()
        rr = [resource1, resource2]
        self.sandbox.get_root_resources = Mock(return_value=rr)
        self.sandbox.power_on_vms()
        self.mock_api_session.return_value.ExecuteResourceConnectedCommand.assert_not_called()

#get_Apps_resources
if __name__ == '__main__':
    unittest.main()
