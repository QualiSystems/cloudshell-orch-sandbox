class WorkflowObject(object):
    def __init__(self, function, components, steps):
        self.function = function
        self.components = components
        self.steps = steps


class Workflow(object):
    def __init__(self):
        self._provisioning_functions = []  # provisioning steps, function step name, resources
        """:type : list[WorkflowObject]"""
        self._connectivity_functions = []
        """:type : list[WorkflowObject]"""
        self._configuration_functions = []
        """:type : list[WorkflowObject]"""

        self._after_provisioning = []
        """:type : list[WorkflowObject]"""
        self._after_connectivity = []
        """:type : list[WorkflowObject]"""
        self._after_configuration = []
        """:type : list[WorkflowObject]"""

    def add_provisioning_process(self, function, steps=None, resources=None):
        self._provisioning_functions.append(WorkflowObject(function, steps, resources))

    def on_provisioning_ended(self, function, steps=None, resources=None):
        self._after_provisioning.append(WorkflowObject(function, steps, resources))

    def add_connectivity_process(self, function, steps=None, resources=None):
        self._connectivity_functions.append(WorkflowObject(function, steps, resources))

    def on_connectivity_ended(self, function, steps=None, resources=None):
        self._after_connectivity.append(WorkflowObject(function, steps, resources))

    def add_configuration_process(self, function, steps=None, resources=None):
        self._configuration_functions.append(WorkflowObject(function, steps, resources))

    def on_configuration_ended(self, function, steps=None, resources=None):
        self._after_configuration.append(WorkflowObject(function, steps, resources))
