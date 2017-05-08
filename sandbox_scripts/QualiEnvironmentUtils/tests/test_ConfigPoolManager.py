import unittest
from mock import patch, Mock
from sandbox_scripts.QualiEnvironmentUtils.ConfigPoolManager import ConfigPoolManager
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError


class ConfigPoolManagerTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = None

    def tearDown(self):
        pass

    # ================================================================
    # test ConfigPoolManager/pool_data function
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

