import unittest
from mock import patch
from cloudshell.workflow.orchestration.sandbox import Sandbox


class TestSandbox(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict('os.environ', {
            'QUALICONNECTIVITYCONTEXT': '{"tsAPIPort": "8028","adminPass": "admin", "adminUser": "admin", "serverAddress":"localhost"}',
            'RESERVATIONLIFECYCLECONTEXT': '{"reservationId":"be015364-9640-4ac5-b6ca-f26e1c6d44c8", "savedSandboxName":"empty", "savedSandboxDescription":"","currentUserName":"admin"}',
            'RESERVATIONCONTEXT': '{"environmentName":"","environmentPath":"Global Topologies/empty","domain":"Global", "description":"","parameters":{"resourceRequirements":[],"globalInputs":[{"parameterName": "in1", "value": "222"},{"parameterName": "in2", "value": "0"}],"resourceAdditionalInfo":[]},"ownerUser":"admin","ownerPass":"admin","id":"be015364-9640-4ac5-b6ca-f26e1c6d44c8","permittedUsers":[{"userName":"admin", "email":"None"}]}',
            'MY_PARAM': 'PARAM-VALUE'})
        patcher.start()

    def tearDown(self):
        patch.stopall()

    def test_sandbox_inputs(self):
        sandbox = Sandbox()
        param = sandbox.get_user_param('MY_PARAM')
        self.assertEqual(param, "PARAM-VALUE")