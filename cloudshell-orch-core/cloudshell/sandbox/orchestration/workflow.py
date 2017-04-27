class Workflow(object):
    def __init__(self):
        self._provisioning_functions = []  # provisioning steps, function step name, resources
        self._connectivity_functions = []
        self._configuration_functions = []

        self._after_provisioning = []
        self._after_connectivity = []
        self._after_configuration = []

    def add_provisioning_process(self, function, steps, resources):
        self._provisioning_functions.append(function)

    def on_provisioning_ended(self, function, steps, resources):
        self._after_provisioning.append(function)

    def add_connectivity_process(self, function, steps, resources):
        self._connectivity_functions.append(function)

    def on_connectivity_ended(self, function, steps, resources):
        self._after_connectivity.append(function)

    def add_configuration_process(self, function, steps, resources):
        self._configuration_functions.append(function)

    def on_configuration_ended(self, function, steps, resources):
        self._after_configuration.append(function)

