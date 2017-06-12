import unittest
from mock import patch, Mock,call
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
from cloudshell.api.cloudshell_api import CommandParameter
from cloudshell.api.cloudshell_api import ReservationDescriptionInfo
from cloudshell.api.cloudshell_api import ResourceCommandInfo
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


class ResourceTests(unittest.TestCase):
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
        self.mock_api_session = mock_api_session
        self.mock_logger = mock_logger

        rd = Mock()
        rd.Name = 'r1'
        rd.Address = ''
        rd.ResourceAttributes = []
        self.mock_api_session.return_value.GetResourceDetails = Mock(return_value=rd)
        self.resource = ResourceBase(resource_name='r1')



    def tearDown(self):
        pass

    # ================================================================
    # test has command function
    def test_has_command_found(self):
        command1 = Mock()
        command1.Name = 'example_command'
        self.resource.commands = [command1]
        ret = self.resource.has_command('example_command')

        self.assertTrue(ret, "command was expected to be found but wasn't")

    def test_has_command_found_connected(self):
        command1 = Mock()
        command1.Name = 'example_command'
        self.resource.connected_commands = [command1]
        ret = self.resource.has_command('example_command')

        self.assertTrue(ret, "command was expected to be found but wasn't")

    def test_has_command_not_found(self):
        command1 = Mock()
        command1.Name = 'example_command'
        self.resource.connected_commands = [command1]
        ret = self.resource.has_command('example_command2')

        self.assertFalse(ret, "command was not expected to be found but was found")

    # ================================================================
    # test attribute exists
    def test_attribute_found(self):
        attr1 = Mock()
        attr1.Name = 'Location'
        self.resource.attributes = [attr1]
        ret = self.resource.attribute_exist('Location')

        self.assertTrue(ret, "attribute was expected to be found but wasn't")

    def test_attribute_found_case_insensitive(self):
        attr1 = Mock()
        attr1.Name = 'locatioN'
        self.resource.attributes = [attr1]
        ret = self.resource.attribute_exist('loCation')

        self.assertTrue(ret, "attribute was expected to be found but wasn't")

    def test_attribute_not_found(self):
        attr1 = Mock()
        attr1.Name = 'Location'
        self.resource.attributes = [attr1]
        ret = self.resource.attribute_exist('LocationXYZ')

        self.assertFalse(ret, "attribute was not expected to be found but was found")

    # ================================================================
    # test get attribute
    def test_get_attribute(self):
        attr1 = Mock()
        attr1.Name = 'Location'
        attr1.Type = 'String'
        attr1.Value = 'New York'
        self.resource.attributes = [attr1]
        ret = self.resource.get_attribute('Location')

        self.assertEqual(ret, "New York", "attribute value was not as expected")

    def test_get_password_attribute(self):
        attr1 = Mock()
        attr1.Name = 'MyPassword'
        attr1.Type = 'Password'
        attr1.Value = 'abcdefg'
        self.resource.attributes = [attr1]
        self.mock_api_session.return_value.DecryptPassword.return_value.Value = 'New York'
        ret = self.resource.get_attribute('MyPassword')
        self.assertEqual(ret, "New York", "attribute was expected to be found but wasn't")

    def test_get_attribute_not_found(self):
        attr1 = Mock()
        attr1.Name = 'Location'
        attr1.Type = 'String'
        attr1.Value = 'New York'
        self.resource.attributes = [attr1]
        with self.assertRaises(QualiError) as e:
            ret = self.resource.get_attribute('LocationXYZ')

        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         "CloudShell error at r1. Error is: Attribute: 'LocationXYZ' not found")

    # ================================================================
    # test health_check
    def test_health_check_passed(self):
        command1 = Mock()
        command1.Name = 'health_check'
        self.resource.commands = [command1]

        rd = Mock()
        rd.Output = "Health check passed"
        self.mock_api_session.return_value.ExecuteCommand = Mock(return_value=rd)
        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905")
        self.assertEqual('',ret, "command was expected to be pass but wasn't")

    def test_health_check_fail_w_exception(self):
        command1 = Mock()
        command1.Name = 'health_check'
        self.resource.commands = [command1]
        self.mock_api_session.return_value.ExecuteCommand.side_effect = CloudShellAPIError(100,"Invalid command","")

        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905")
        self.assertEqual('Health check did not pass for device r1. CloudShell error at r1. Error is: Invalid command',ret)

    def test_health_check_failed(self):
        command1 = Mock()
        command1.Name = 'health_check'
        self.resource.commands = [command1]

        rd = Mock()
        rd.Output = "Health check failed"
        self.mock_api_session.return_value.ExecuteCommand = Mock(return_value=rd)
        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905")
        self.assertEqual('Health check did not pass for device r1. Health check failed',ret)

    @patch('time.sleep')
    def test_health_check_failed_twice(self, mock_time):
        command1 = Mock()
        command1.Name = 'health_check'
        self.resource.commands = [command1]

        rd = Mock()
        rd.Output = "Health check failed"
        self.mock_api_session.return_value.ExecuteCommand = Mock(return_value=rd)
        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905", health_check_attempts=2)
        self.assertEqual('Health check did not pass for device r1. Health check failed',ret)
        self.assertEqual(mock_time.call_count,1)

    @patch('time.sleep')
    def test_health_check_failed_once_succeeds_on_second(self, mock_time):
        command1 = Mock()
        command1.Name = 'health_check'
        self.resource.commands = [command1]
        self.count = 0
        def execute_command_return_value(res_id, resource_name, resource_type, command_name, inputs, print_output):
            rd = Mock()
            if self.count == 0:
                rd.Output = "Health check failed"
                self.count += 1
            else:
                rd.Output = "Health check passed"
            return rd

        self.mock_api_session.return_value.ExecuteCommand.side_effect = execute_command_return_value
        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905", health_check_attempts=2)
        self.assertEqual('',ret, "command was expected to be pass but wasn't")
        self.assertEqual(mock_time.call_count,1)

    def test_health_check_not_found(self):
        ret = self.resource.health_check("5487c6ce-d0b3-43e9-8ee7-e27af8406905")
        self.assertEqual('',ret, "command was expected to be found but wasn't")

    # ================================================================
    # test load_network_config
    def test_load_network_config_restore_not_exist(self):
        try:
            self.resource.load_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')
            self.fail("Didn't get an exception while expecting to. load_network_config does not exist." )
        except QualiError as e:
            self.assertEqual('Failed building restore command input parm names.Restore command does not exist. Check driver installation.',
                             e.message)

    def test_load_network_config_wrong_param(self):
        command1 = Mock()
        command1.Name = 'restore'
        param1 = Mock()
        param1.Name = 'path123'
        param2 = Mock()
        param2.Name = 'configuration_type'
        param3 = Mock()
        param3.Name = 'restore_method'
        command1.Parameters = [param1, param2, param3]
        self.resource.commands = [command1]
        with self.assertRaises(Exception) as e:
            self.resource.load_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')

        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         'CloudShell error at r1. Error is: Failed building restore command input parm names.Failed to find viable restore command for r1 - config_path: undef, config_type: configuration_type, restore_method: restore_method')

    def test_load_network_config_passed(self):
        command1 = Mock()
        command1.Name = 'restore'
        param1 = Mock()
        param1.Name = 'path'
        param2 = Mock()
        param2.Name = 'configuration_type'
        param3 = Mock()
        param3.Name = 'restore_method'
        command1.Parameters = [param1, param2, param3]
        self.resource.commands = [command1]

        try:
            self.resource.load_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')
        except Exception as e:
            self.fail('Got an unexpected exception: ' + e.message)

    def test_load_network_config_failed(self):
        command1 = Mock()
        command1.Name = 'restore'
        param1 = Mock()
        param1.Name = 'path'
        param2 = Mock()
        param2.Name = 'configuration_type'
        param3 = Mock()
        param3.Name = 'restore_method'
        command1.Parameters = [param1, param2, param3]
        self.resource.commands = [command1]

        self.mock_api_session.return_value.ExecuteCommand.side_effect = CloudShellAPIError(100,"Device rejected connection","")
        with self.assertRaises(QualiError) as e:
            self.resource.load_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')

        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         'CloudShell error at r1. Error is: Failed to load configuration: Device rejected connection')

    def test_load_network_config_w_vrf(self):
        command1 = Mock()
        command1.Name = 'restore'
        param1 = Mock()
        param1.Name = 'path'
        param2 = Mock()
        param2.Name = 'configuration_type'
        param3 = Mock()
        param3.Name = 'restore_method'
        command1.Parameters = [param1, param2, param3]
        self.resource.commands = [command1]

        attr1 = Mock()
        attr1.Name = 'VRF Management Name'
        attr1.Value = '123'
        self.resource.attributes = [attr1]
        try:
            self.resource.load_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')
            #todo: check command_inputs size is 4
            call_args = self.mock_api_session.return_value.ExecuteCommand.call_args[0]
            self.assertEqual(call_args[0], '5487c6ce-d0b3-43e9-8ee7-e27af8406905')
            self.assertEqual(call_args[1], 'r1')
            self.assertEqual(call_args[2], 'Resource')
            self.assertEqual(call_args[3], 'restore')
            command_inputs = call_args[4]
            self.assertEqual(command_inputs[0].Name, 'path')
            self.assertEqual(command_inputs[0].Value, 'tftp://www.cfg')
            self.assertEqual(command_inputs[1].Name, 'configuration_type')
            self.assertEqual(command_inputs[1].Value, 'running')
            self.assertEqual(command_inputs[2].Name, 'restore_method')
            self.assertEqual(command_inputs[2].Value, 'Override')
            self.assertEqual(command_inputs[3].Name, 'vrf_management_name')
            self.assertEqual(command_inputs[3].Value, '123')
        except Exception as e:
            self.fail('Got an unexpected exception: ' + e.message)

    # ================================================================
    # test save_network_config
    '''
    def test_save_network_config_restore_not_exist(self):
        try:
            self.resource.save_network_config("5487c6ce-d0b3-43e9-8ee7-e27af8406905",'tftp://www.cfg','running')
            self.fail("Didn't get an exception while expecting to. save_network_config does not exist." )
        except QualiError as e:
            self.assertEqual('Failed to save configuration: No commands were found',
                             e.message)

    '''
    # TODO: much more
        # save_network_config
        # orchestration_restore
        # orchestration_save
        # execute_command
        # execute_connected_command
        # load_firmware
        # set_live_status
        # get_live_status



if __name__ == '__main__':
    unittest.main()
