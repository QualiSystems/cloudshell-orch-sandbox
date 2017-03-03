import unittest
from mock import patch, Mock, call
from sandbox_scripts.environment.setup.setup_resources import EnvironmentSetupResources
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

class SetupResourcesTests(unittest.TestCase):

    @patch('sandbox_scripts.environment.setup.setup_resources.get_qs_logger')
    def setUp(self, mock_logger):
        os.environ['reservationContext'] = resContext
        os.environ['qualiConnectivityContext'] = conContext
        self.setup_script = EnvironmentSetupResources()

    def tearDown(self):
        pass

    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    @patch('sandbox_scripts.environment.setup.setup_resources.SandboxBase')
    @patch('sandbox_scripts.environment.setup.setup_resources.NetworkingSaveRestore')
    def test_flow_ok_with_snapshots(self, mock_save, mock_sandboxbase, mock_api_session):

        mock_save.return_value.is_snapshot.return_value = True
        self.setup_script.execute()
        mock_sandboxbase.return_value.clear_all_resources_live_status.assert_called_with()
        mock_save.return_value.load_config.assert_called_with(config_stage='Snapshots', config_type='Running', ignore_models=['Generic TFTP server', 'Config Set Pool', 'Generic FTP server', 'netscout switch 3912'])
        mock_sandboxbase.return_value.power_on_vms.assert_called_with()
        mock_sandboxbase.return_value.activate_all_routes_and_connectors.assert_called_with()
        report_info_calls = [call('Beginning load configuration for resources'),
                             call('Sandbox setup finished successfully')]
        mock_sandboxbase.return_value.report_info.assert_has_calls(report_info_calls)


    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    @patch('sandbox_scripts.environment.setup.setup_resources.SandboxBase')
    @patch('sandbox_scripts.environment.setup.setup_resources.NetworkingSaveRestore')
    def test_flow_ok_with_gold(self, mock_save, mock_sandboxbase, mock_api_session):

        mock_save.return_value.is_snapshot.return_value = False
        self.setup_script.execute()
        mock_sandboxbase.return_value.clear_all_resources_live_status.assert_called_with()
        mock_save.return_value.load_config.assert_called_with(config_set_name='', config_stage='Gold', config_type='Running', ignore_models=['Generic TFTP server', 'Config Set Pool', 'Generic FTP server', 'netscout switch 3912'])
        mock_sandboxbase.return_value.power_on_vms.assert_called_with()
        mock_sandboxbase.return_value.activate_all_routes_and_connectors.assert_called_with()
        report_info_calls = [call('Beginning load configuration for resources'),
                             call('Sandbox setup finished successfully')]
        mock_sandboxbase.return_value.report_info.assert_has_calls(report_info_calls)



if __name__ == '__main__':
    unittest.main()
