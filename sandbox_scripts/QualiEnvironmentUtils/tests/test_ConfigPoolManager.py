import unittest
import json
import os
from mock import patch, Mock, call
from sandbox_scripts.QualiEnvironmentUtils.ConfigPoolManager import ConfigPoolManager
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
from cloudshell.api.cloudshell_api import ResourceAttribute
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


class ConfigPoolManagerTests(unittest.TestCase):
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

    def tearDown(self):
        pass

    # ================================================================
    # test push_data_from_pool_to_sandbox function
    def test_no_config_manager(self):
        with self.assertRaises(QualiError) as e:
            self.config_pool_mgr = ConfigPoolManager(sandbox=self.sandbox, pool_resource=None)

        the_exception = e.exception
        self.assertEqual(str(the_exception),
                         'CloudShell error at ConfigPoolManager. '
                         'Error is: Trying to use the ConfigPoolManager without a pool resource')

    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    def test_config_manager_without_attributes(self, mock_api_session):
        rd = Mock()
        rd.Name = 'pool manager'
        rd.Address = ''
        rd.ChildResources = []
        rd.ResourceAttributes = []
        mock_api_session.return_value.GetResourceDetails = Mock(return_value=rd)
        resource = ResourceBase(resource_name='pool manager')

        config_pool_mgr = ConfigPoolManager(sandbox=self.sandbox, pool_resource=resource)
        self.assertTrue(len(config_pool_mgr.pool_data) == 0)

    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    def test_config_manager_without_child_resources(self, mock_api_session):
        rd = Mock()
        rd.Name = 'pool manager'
        rd.Address = ''
        attr1 = Mock()
        attr1.Name = 'Pool1'
        attr1.Value = 'Pool1Val'
        attr2 = Mock()
        attr2.Name = 'Pool2'
        attr2.Value = 'Pool2Val'
        rd.ChildResources = []
        rd.ResourceAttributes = [attr1, attr2]
        mock_api_session.return_value.GetResourceDetails = Mock(return_value=rd)
        resource = ResourceBase(resource_name='pool manager')

        config_pool_mgr = ConfigPoolManager(sandbox=self.sandbox, pool_resource=resource)
        self.assertTrue(len(config_pool_mgr.pool_data) == 2)
        self.assertTrue('{configpool:pool1}' in config_pool_mgr.pool_data)
        self.assertTrue('{configpool:pool2}' in config_pool_mgr.pool_data)


    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    def test_config_manager_with_child_resources(self, mock_api_session):
        rd = Mock()
        rd.Name = 'pool manager'
        rd.Address = ''
        attr1 = Mock()
        attr1.Name = 'Pool1'
        attr1.Value = 'Pool1Val'
        attr2 = Mock()
        attr2.Name = 'Pool2'
        attr2.Value = 'Pool2Val'
        cr = Mock()
        cr.Name = 'pool view'
        cr.Address = ''
        attr3 = Mock()
        attr3.Name = 'Pool3'
        attr3.Value = 'Pool3Val'
        cr.ResourceAttributes = [attr3]
        rd.ChildResources = [cr]
        rd.ResourceAttributes = [attr1, attr2]
        mock_api_session.return_value.GetResourceDetails = Mock(return_value=rd)
        resource = ResourceBase(resource_name='pool manager')

        config_pool_mgr = ConfigPoolManager(sandbox=self.sandbox, pool_resource=resource)
        self.assertTrue(len(config_pool_mgr.pool_data) == 3)
        self.assertTrue('{configpool:pool1}' in config_pool_mgr.pool_data, "pool1 not found")
        self.assertTrue('{configpool:pool2}' in config_pool_mgr.pool_data, "pool2 not found")
        self.assertTrue('{configpool:pool view:pool3}' in config_pool_mgr.pool_data, "pool3 not found")


if __name__ == '__main__':
    unittest.main()

