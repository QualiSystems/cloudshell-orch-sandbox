import inspect


class WorkflowObject(object):
    def __init__(self, function, components):
        self.function = function
        self.components = components


class Workflow(object):
    PREPARATION_STAGE_NAME = 'Preparation'
    ON_PREPARATION_ENDED_STAGE_NAME = 'On preparation ended'
    PROVISIONING_STAGE_NAME = 'Provisioning'
    ON_PROVISIONING_ENDED_STAGE_NAME = 'On provisioning ended'
    CONNECTIVITY_STAGE_NAME = 'Connectivity'
    ON_CONNECTIVITY_ENDED_STAGE_NAME = 'On connectivity ended'
    CONFIGURATION_STAGE_NAME = 'Configuration'
    ON_CONFIGURATION_ENDED_STAGE_NAME = 'On configuration ended'
    TEARDOWN_STAGE_NAME = 'Teardown'
    BEFORE_TEARDOWN_STAGE_NAME = 'Before Teardown Started'

    def __init__(self, sandbox):
        self._preparation_functions = []
        """:type : list[WorkflowObject]"""
        self._provisioning_functions = []
        """:type : list[WorkflowObject]"""
        self._connectivity_functions = []
        """:type : list[WorkflowObject]"""
        self._configuration_functions = []
        """:type : list[WorkflowObject]"""

        self._after_preparation = []
        """:type : list[WorkflowObject]"""
        self._after_provisioning = []
        """:type : list[WorkflowObject]"""
        self._after_connectivity = []
        """:type : list[WorkflowObject]"""
        self._after_configuration = []
        """:type : list[WorkflowObject]"""

        self._teardown_functions = []
        """:type : list[WorkflowObject]"""
        self._before_teardown = []
        """:type : list[WorkflowObject]"""

        self.sandbox = sandbox

    def add_to_preparation(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._preparation_functions.append(WorkflowObject(function=function, components=components))

    def on_preparation_ended(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._after_preparation.append(WorkflowObject(function=function, components=components))

    def add_to_provisioning(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._provisioning_functions.append(WorkflowObject(function=function, components=components))

    def on_provisioning_ended(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._after_provisioning.append(WorkflowObject(function=function, components=components))

    def add_to_connectivity(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._connectivity_functions.append(WorkflowObject(function=function, components=components))

    def on_connectivity_ended(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._after_connectivity.append(WorkflowObject(function=function, components=components))

    def add_to_configuration(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._configuration_functions.append(WorkflowObject(function=function, components=components))

    def on_configuration_ended(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._after_configuration.append(WorkflowObject(function=function, components=components))

    def add_to_teardown(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._teardown_functions.append(WorkflowObject(function=function, components=components))

    def before_teardown_started(self, function, components=None):
        """
        :param function:
        :param components: list of components: App, ReservedResourceInfo or ServiceInstance
        """
        self._validate_function(function)
        self._before_teardown.append(WorkflowObject(function=function, components=components))

    def _validate_function(self, func):
        args = inspect.getargspec(func).args
        self.sandbox.logger.info(
            'Validating custom function "{0}": {1}. '.format(func.__name__, args))
        if len(args) < 2:
            self.sandbox.automation_api.WriteMessageToReservationOutput(reservationId=self.sandbox.id,
                                                                        message='Sandbox orchestration workflow processes "{0}" should have 2 parameters (sandbox and components), see documentation for more information.'.format(
                                                                            func.__name__))
            raise Exception("Sandbox is Active with Errors")
