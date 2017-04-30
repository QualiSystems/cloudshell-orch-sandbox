import sys
from multiprocessing.pool import ThreadPool

from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

from cloudshell.sandbox.environment.setup.setup_common import SetupCommon
from cloudshell.sandbox.orchestration.workflow import Workflow
from cloudshell.sandbox.profiler.env_profiler import profileit
from cloudshell.sandbox.orchestration.apps_configuration import AppsConfiguration
from cloudshell.sandbox.orchestration.components import Components


class SandboxManager(object):
    def __init__(self):
        self._resource_details_cache = {}
        self.api = helpers.get_api_session()
        self.workflow = Workflow()

        self.ConnectivityContextDetails = helpers.get_connectivity_context_details()
        self.ReservationContextDetails = helpers.get_reservation_context_details()
        self.Globals = self.ReservationContextDetails.parameters.global_inputs
        self.reservation_id = self.ReservationContextDetails.id

        self.apps_configuration = AppsConfiguration(reservation_id=self.reservation_id,
                                                    api=self.api)

        reservation_description = self.api.GetReservationDetails(self.reservation_id).ReservationDescription
        self.Components = Components(reservation_description.Resources,
                                     reservation_description.Services,
                                     reservation_description.Apps)

        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                    log_group=self.reservation_id,
                                    log_category='Setup')

    def _execute_step(self, func, resources, steps):
        self.logger.info("Executing: {0}. ".format(func.__name__))
        execution_failed = 0
        try:
            func(self, resources, steps)
            # if (step not ended --> end all steps)
        except Exception as exc:
            execution_failed = 1
            print exc
            self.logger.error("Error executing function {0}. detaild error: {1}".format(func.__name__, str(exc)))
        return execution_failed

    def get_api(self):
        return self.api

    @profileit(scriptName='Setup')
    def execute(self):
        api = self.api

        api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                            message='Beginning sandbox setup')

        ## prepare sandbox stage
        SetupCommon.prepare_connectivity(api, self.reservation_id, self.logger)

        ## provisioning sandbox stage
        pool = ThreadPool(len(self.workflow._provisioning_functions))

        async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                               workflow_object.components,
                                                               workflow_object.steps)) for workflow_object in
                         self.workflow._provisioning_functions]

        pool.close()
        pool.join()

        ## validate parallel results
        for async_result in async_results:
            result = async_result.get()
            if result == 1:  # failed to execute step
                self.api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                         message='<font color="red">Error occurred during sandbox provisioning, see full activity feed for more information.</font>')
                sys.exit(-1)

        for function in self.workflow._after_provisioning:
            self._execute_step(function)
        # API.StageEnded(provisioning)


        # connectivity sandbox stage
        pool = ThreadPool(len(self.workflow._connectivity_functions))

        async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                               workflow_object.components,
                                                               workflow_object.steps)) for workflow_object in
                         self.workflow._connectivity_functions]

        pool.close()
        pool.join()

        ## validate parallel results
        for async_result in async_results:
            result = async_result.get()
            if result == 1:  # failed to execute step
                self.api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                         message='<font color="red">Error occurred during sandbox connectivity, see full activity feed for more information.</font>')
                sys.exit(-1)

        for function in self.workflow._after_connectivity:
            self._execute_step(function)

        # API.StageEnded(provisioning)


        # configuration sandbox stage
        pool = ThreadPool(len(self.workflow._configuration_functions))

        async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                               workflow_object.components,
                                                               workflow_object.steps)) for workflow_object in
                         self.workflow._configuration_functions]

        pool.close()
        pool.join()

        ## validate parallel results
        for async_result in async_results:
            result = async_result.get()
            if result == 1:  # failed to execute step
                self.api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                         message='<font color="red">Error occurred during sandbox configuration, see full activity feed for more information.</font>')
                sys.exit(-1)

        for function in self.workflow._after_configuration:
            self._execute_step(function)

        # API.StageEnded(provisioning)

        self.logger.info("Setup for sandbox {0} completed".format(self.reservation_id))

        api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                            message='Sandbox setup finished successfully')
