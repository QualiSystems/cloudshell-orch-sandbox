import sys
import unittest
from cloudshell.workflow.orchestration.workflow import Workflow
from cloudshell.workflow.orchestration.sandbox import Sandbox

if sys.version_info >= (3, 0):
    from unittest.mock import MagicMock
else:
    from mock import MagicMock


def classic_workflow_func(sandbox, components=None):
    """
    :param sandbox:
    :param components:
    :return:
    """
    pass


def py3_workflow_func(sandbox: Sandbox, components=None):
    pass


class TestTypeHintsWorkflow(unittest.TestCase):
    def setUp(self):
        sandbox = MagicMock()
        self.workflow = Workflow(sandbox)

    def tearDown(self):
        pass

    def test_no_type_hints(self):
        self.workflow._validate_function(classic_workflow_func)

    def test_py3_type_hint_func(self):
        self.workflow._validate_function(py3_workflow_func)
