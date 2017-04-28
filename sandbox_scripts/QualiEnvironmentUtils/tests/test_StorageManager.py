import unittest
from mock import patch, Mock,call
from sandbox_scripts.QualiEnvironmentUtils.StorageManager import StorageManager
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


class StorageManagerTests(unittest.TestCase):
    @patch('cloudshell.helpers.scripts.cloudshell_scripts_helpers.get_api_session')
    def setUp(self, mock_api_session):
        pass

    def tearDown(self):
        pass

# TODO: implement tests

if __name__ == '__main__':
    unittest.main()
