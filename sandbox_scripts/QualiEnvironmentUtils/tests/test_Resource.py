import unittest
from mock import patch, Mock,call
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
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
        command1 = Mock()
        command1.Name = 'Location'
        self.resource.connected_commands = [command1]
        ret = self.resource.has_command('LocationXYZ')

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


    # TODO: much more
        # health_check
        # load_network_config
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
