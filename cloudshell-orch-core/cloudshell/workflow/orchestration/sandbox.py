import sys
from multiprocessing.pool import ThreadPool

from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

from cloudshell.workflow.environment.setup.setup_common import SetupCommon
from cloudshell.workflow.orchestration.workflow import Workflow
from cloudshell.workflow.profiler.env_profiler import profileit
from cloudshell.workflow.orchestration.apps_configuration import AppsConfiguration
from cloudshell.workflow.orchestration.components import Components


class Sandbox(object):
    def __init__(self):
        self.automation_api = helpers.get_api_session()
        self.workflow = Workflow()

        self.connectivityContextDetails = helpers.get_connectivity_context_details()
        self.reservationContextDetails = helpers.get_reservation_context_details()
        self.globals = self.reservationContextDetails.parameters.global_inputs
        self.id = self.reservationContextDetails.id

        reservation_description = self.automation_api.GetReservationDetails(self.id).ReservationDescription
        self.components = Components(reservation_description.Resources,
                                     reservation_description.Services,
                                     reservation_description.Apps)

        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                    log_group=self.id,
                                    log_category='Setup')

        self.apps_configuration = AppsConfiguration(sandbox=self)

    def _execute_step(self, func, components):
        self.logger.info("Executing method: {0}. ".format(func.__name__))
        execution_failed = 0
        try:
            func(self, components)
        except Exception as exc:
            execution_failed = 1
            print exc
            self.logger.error("Error executing function {0}. detaild error: {1}, {2}".format(func.__name__, str(exc), str(exc.message)))
        return execution_failed

    @profileit(scriptName='Setup')
    def execute(self):
        api = self.automation_api
        self.logger.info("Setup execution started")

        api.WriteMessageToReservationOutput(reservationId=self.id,
                                            message='Beginning sandbox setup')

        ## prepare sandbox stage
        self.logger.info("Preparing connectivity for sandbox. ")
        SetupCommon.prepare_connectivity(api, self.id, self.logger)

        ## provisioning workflow stage
        number_of_provisioning_processes = len(self.workflow._provisioning_functions)
        self.logger.info("Executing {0} workflow provisioning processes. ".format(number_of_provisioning_processes))

        if number_of_provisioning_processes > 0:
            pool = ThreadPool(number_of_provisioning_processes)

            async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                                   workflow_object.components)) for workflow_object in
                             self.workflow._provisioning_functions]

            pool.close()
            pool.join()

            ## validate parallel results
            for async_result in async_results:
                result = async_result.get()
                if result == 1:  # failed to execute step
                    self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                        message='<font color="red">Error occurred during sandbox provisioning, see full activity feed for more information.</font>')
                    sys.exit(-1)

        else:
            self.logger.info("No provisioning process was configured.")

        self.logger.info(
            "Executing {0} sandbox after provisioning ended steps. ".format(len(self.workflow._after_provisioning)))
        for workflow_object in self.workflow._after_provisioning:
            self._execute_step(workflow_object.function,
                               workflow_object.components)
        # API.StageEnded(provisioning)


        # connectivity workflow stage
        number_of_connectivity_processes = len(self.workflow._connectivity_functions)
        self.logger.info("Executing {0} sandbox connectivity processes. ".format(number_of_connectivity_processes))
        if number_of_connectivity_processes >= 1:
            pool = ThreadPool(number_of_connectivity_processes)

            async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                                   workflow_object.components)) for workflow_object in
                             self.workflow._connectivity_functions]

            pool.close()
            pool.join()

            ## validate parallel results
            for async_result in async_results:
                result = async_result.get()
                if result == 1:  # failed to execute step
                    self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                        message='<font color="red">Error occurred during sandbox connectivity, see full activity feed for more information.</font>')
                    sys.exit(-1)
        else:
            self.logger.info("No connectivity process was configured.")

        self.logger.info(
            "Executing {0} sandbox after connectivity ended steps. ".format(len(self.workflow._after_connectivity)))
        for workflow_object in self.workflow._after_connectivity:
            self._execute_step(workflow_object.function,
                               workflow_object.components)

        # API.StageEnded(provisioning)


        # configuration workflow stage
        number_of_configuration_processes = len(self.workflow._configuration_functions)
        self.logger.info("Executing {0} sandbox configuration processes. ".format(number_of_configuration_processes))
        if number_of_configuration_processes>= 1:
            pool = ThreadPool(number_of_configuration_processes)

            async_results = [pool.apply_async(self._execute_step, (workflow_object.function,
                                                                   workflow_object.components)) for workflow_object in
                             self.workflow._configuration_functions]

            pool.close()
            pool.join()

            ## validate parallel results
            for async_result in async_results:
                result = async_result.get()
                if result == 1:  # failed to execute step
                    self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                        message='<font color="red">Error occurred during sandbox configuration, see full activity feed for more information.</font>')
                    sys.exit(-1)
        else:
            self.logger.info("No configuration process was configured.")

        self.logger.info(
            "Executing {0} sandbox after configuration ended steps. ".format(len(self.workflow._after_configuration)))

        for workflow_object in self.workflow._after_configuration:
            self._execute_step(workflow_object.function,
                               workflow_object.components)

        # API.StageEnded(provisioning)

        self.logger.info("Setup for sandbox {0} completed".format(self.id))

        api.WriteMessageToReservationOutput(reservationId=self.id,
                                            message='Sandbox setup finished successfully')
