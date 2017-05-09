class WorkflowObject(object):
    def __init__(self, function, components):
        self.function = function
        self.components = components


class Workflow(object):
    def __init__(self):
        self._provisioning_functions = []
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

    def add_to_provisioning(self, function, components=None):
        self._provisioning_functions.append(WorkflowObject(function=function, components=components))

    def on_provisioning_ended(self, function, components=None):
        self._after_provisioning.append(WorkflowObject(function=function, components=components))

    def add_to_connectivity(self, function, components=None):
        self._connectivity_functions.append(WorkflowObject(function=function, components=components))

    def on_connectivity_ended(self, function, components=None):
        self._after_connectivity.append(WorkflowObject(function=function, components=components))

    def add_to_configuration(self, function, components=None):
        self._configuration_functions.append(WorkflowObject(function=function, components=components))

    def on_configuration_ended(self, function, components=None):
        self._after_configuration.append(WorkflowObject(function=function, components=components))
