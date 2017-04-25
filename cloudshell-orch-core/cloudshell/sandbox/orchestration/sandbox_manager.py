from multiprocessing.pool import ThreadPool

import sys
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.core.logger.qs_logger import get_qs_logger

from cloudshell.sandbox.environment.setup.setup_common import SetupCommon
from cloudshell.sandbox.profiler.env_profiler import profileit


class SandboxManager(object):

    def __init__(self, default_provisioning=True, default_connectivity=True, default_configuration=True):
        self._resource_details_cache = {}
        self.api = helpers.get_api_session()

        self._enable_default_provisioning = default_provisioning
        self._enable_default_connectivity = default_connectivity
        self._enable_default_configuration = default_configuration

        self._provisioning_functions = []  # provisioning steps, function step name, resources
        self._connectivity_functions = []
        self._configuration_functions = []

        self._after_provisioning = []
        self._after_connectivity = []
        self._after_configuration = []

        self.reservation_id = helpers.get_reservation_context_details().id
        self._logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                     log_group=self.reservation_id,
                                     log_category='Setup')

        self._add_default_orchestration()

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

    def _add_default_orchestration(self):
        self._logger.info("Adding defualt orchestration")

        if self._enable_default_provisioning:
            self.add_provisioning_process(self._default_provisioning, None, None)
        if self._enable_default_connectivity:
            self.add_connectivity_process(self._default_connectivity, None, None)
        if self._enable_default_configuration:
            self.add_configuration_process(self._default_configuration, None, None)

    def _default_provisioning(self):
        api = self.api

        self._logger.info("Executing default provisioning")

        reservation_details = api.GetReservationDetails(self.reservation_id)
        self.deploy_result = SetupCommon.deploy_apps_in_reservation(api=api,
                                                                  reservation_details=reservation_details,
                                                                  reservation_id=self.reservation_id,
                                                                  logger=self._logger)

        SetupCommon._validate_all_apps_deployed(deploy_results=self.deploy_result,
                                                logger=self._logger)

        SetupCommon.try_exeucte_autoload(api=api,
                                       deploy_result=self.deploy_result,
                                       resource_details_cache=self._resource_details_cache,
                                       reservation_id=self.reservation_id,
                                       logger=self._logger)

    def _default_connectivity(self):
        api = self.api

        self._logger.info("Executing default connectivity")

        reservation_details = api.GetReservationDetails(self.reservation_id)

        SetupCommon.connect_all_routes_in_reservation(api=api,
                                                    reservation_details=reservation_details,
                                                    reservation_id=self.reservation_id,
                                                    resource_details_cache=self._resource_details_cache,
                                                    logger=self._logger)

        SetupCommon.run_async_power_on_refresh_ip(api=api,
                                                reservation_details=reservation_details,
                                                deploy_results=self.deploy_result,
                                                resource_details_cache=self._resource_details_cache,
                                                reservation_id=self.reservation_id,
                                                logger=self._logger)

    def _default_configuration(self):
        self._logger.info("Executing default configuration")
        SetupCommon.configure_apps(api=self.api,
                                   reservation_id=self.reservation_id,
                                   logger=self._logger)

    def _execute_step(self, func):
        self._logger.info("Executing: {0}. ".format(func.__name__))
        execution_failed = 0
        try:
            func()
            # if (step not ended --> end all steps)
        except Exception as exc:
            execution_failed = 1
            print exc
            self._logger.error("Error executing function {0}. detaild error: {1}".format(func.__name__, str(exc)))
        return execution_failed

    def get_api(self):
        return self.api

    @profileit(scriptName='Setup')
    def execute(self):
        api = self.api

        api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                            message='Beginning sandbox setup')

        ## prepare sandbox stage
        SetupCommon.prepare_connectivity(api, self.reservation_id, self._logger)

        ## provisioning sandbox stage
        pool = ThreadPool(len(self._provisioning_functions))

        async_results = [pool.apply_async(self._execute_step, (function,)) for function in self._provisioning_functions]

        pool.close()
        pool.join()

        ## validate parallel results
        for async_result in async_results:
            result = async_result.get()
            if result == 1: #failed to execute step
                self.api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                         message='<font color="red">Error occurred during sandbox provisioning, see full activity feed for more information.</font>')
                sys.exit(-1)


        for function in self._after_provisioning:
            self._execute_step(function)
        # API.StageEnded(provisioning)


        # connectivity sandbox stage
        pool = ThreadPool(len(self._connectivity_functions))

        [pool.apply_async(self._execute_step, (function, ))
                         for function in self._connectivity_functions]

        pool.close()
        pool.join()

        ## validate parallel results

        for function in self._after_connectivity:
            self._execute_step(function)

        # API.StageEnded(provisioning)


        # configuration sandbox stage
        pool = ThreadPool(len(self._configuration_functions))

        [pool.apply_async(self._execute_step, (function, ))
                         for function in self._configuration_functions]

        pool.close()
        pool.join()

        ## validate parallel results

        for function in self._after_configuration:
            self._execute_step(function)

            #  API.StageEnded(provisioning)

        self._logger.info("Setup for sandbox {0} completed".format(self.reservation_id))

        api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                            message='Sandbox setup finished successfully')
