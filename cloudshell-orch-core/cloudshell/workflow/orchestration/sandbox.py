import sys
from multiprocessing.pool import ThreadPool
import traceback

from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as api_helpers

from cloudshell.workflow.orchestration.apps_configuration import AppsConfiguration
from cloudshell.workflow.orchestration.components import Components
from cloudshell.workflow.orchestration.workflow import Workflow
from cloudshell.workflow.profiler.env_profiler import profileit
from cloudshell.workflow.helpers import sandbox_helpers as helpers

class Sandbox(object):
    def __init__(self):
        self.automation_api = api_helpers.get_api_session()
        self.workflow = Workflow(self)

        self.connectivityContextDetails = helpers.get_connectivity_context_details()
        self.reservationContextDetails = helpers.get_reservation_context_details()
        self.global_inputs = helpers.get_global_inputs()
        self.additional_info_inputs = helpers.get_resource_additional_info_inputs()
        self.requirement_inputs = helpers.get_resource_requirement_inputs()
        self.id = self.reservationContextDetails.id

        reservation_description = self.automation_api.GetReservationDetails(self.id).ReservationDescription

        self.components = Components(reservation_description.Resources,
                                     reservation_description.Services,
                                     reservation_description.Apps)

        self.logger = get_qs_logger(log_file_prefix='CloudShell Sandbox Orchestration',
                                    log_group=self.id,
                                    log_category='Orchestration')

        self.apps_configuration = AppsConfiguration(sandbox=self)

    def get_user_param(self, param_name):
        api_helpers.get_user_param(param_name)

    @profileit(scriptName='Setup')
    def execute_setup(self):
        api = self.automation_api

        self.logger.info('Setup execution started')

        api.WriteMessageToReservationOutput(reservationId=self.id,
                                            message='Beginning sandbox setup')

        ## prepare sandbox stage
        self.logger.info('Preparing sandbox. ')
        api.WriteMessageToReservationOutput(reservationId=self.id, message='Preparing connectivity')
        api.PrepareSandboxConnectivity(self.id)

        self.automation_api.SetSetupStage('Provisioning', self.id)

        self._execute_stage(self.workflow._provisioning_functions, Workflow.PROVISIONING_STAGE_NAME)

        self._after_stage_ended(self.workflow._after_provisioning, Workflow.ON_PROVISIONING_ENDED_STAGE_NAME)

        self.automation_api.SetSetupStage('Connectivity', self.id)

        self._execute_stage(self.workflow._connectivity_functions, Workflow.CONNECTIVITY_STAGE_NAME)

        self._after_stage_ended(self.workflow._after_connectivity, Workflow.ON_CONNECTIVITY_ENDED_STAGE_NAME)

        self.automation_api.SetSetupStage('Configuration', self.id)

        self.components.refresh_components(self)

        self._execute_stage(self.workflow._configuration_functions, Workflow.CONFIGURATION_STAGE_NAME)

        self._after_stage_ended(self.workflow._after_configuration, Workflow.ON_CONFIGURATION_ENDED_STAGE_NAME)

        self.automation_api.SetSetupStage('Ended', self.id)

        self.logger.info('Setup for sandbox {0} completed'.format(self.id))

        api.WriteMessageToReservationOutput(reservationId=self.id,
                                            message='Sandbox setup finished successfully')

    @profileit(scriptName='Teardown')
    def execute_teardown(self):
        if self.workflow._teardown is None:
            self.logger.info('No teardown process was configured for the sandbox')

        else:
            self.logger.info('Teardown execution started')

            self._execute_workflow_process(self.workflow._teardown.function, self.workflow._teardown.components)

            self.logger.info('Teardown for sandbox {0} completed'.format(self.id))

            self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                message='Sandbox teardown finished successfully')

    def _execute_workflow_process(self, func, components):
        self.logger.info("Executing method: {0}. ".format(func.__name__))
        execution_failed = 0
        try:
            func(self, components)

        except Exception as exc:
            execution_failed = 1
            error = exc.message
            if not error or not isinstance(exc.message, str):
                try:
                    error = str(exc)
                except Exception:
                    pass

            print error
            self.logger.error("Error executing function '{0}'. detailed error: {1}, {2}".format(func.__name__, str(error), str(traceback.format_exc())))

        return execution_failed

    def _execute_stage(self, workflow_objects, stage_name):
        """
         :param list[WorkflowObject] workflow_objects:
         :param str stage_name:
         :return:
         """
        number_of_workflow_objects = len(workflow_objects)
        self.logger.info('Executing "{0}" stage, {1} workflow processes found. '.format(stage_name, number_of_workflow_objects))

        if number_of_workflow_objects > 0:
            pool = ThreadPool(number_of_workflow_objects)

            async_results = [pool.apply_async(self._execute_workflow_process, (workflow_object.function,
                                                                               workflow_object.components)) for workflow_object in workflow_objects]

            pool.close()
            pool.join()

            for async_result in async_results:
                result = async_result.get()
                self._validate_workflow_process_result(result, stage_name)

        else:
            self.logger.info('Stage: {0}, No workflow process were found.'.format(stage_name))

    def _validate_workflow_process_result(self, result, stage_name):
        if result == 1:  # failed to execute step
            self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                message='<font color="red">Error occurred during "{0}" stage, see full activity feed for more information.</font>'.format(
                                                                    stage_name))
            sys.exit(-1)

    def _after_stage_ended(self, workflow_objects, stage_name):
        self.logger.info(
            'Executing "{0}" stage ,{1} workflow processes found. '.format(stage_name, len(workflow_objects)))
        for workflow_object in workflow_objects:
            workflow_result = self._execute_workflow_process(workflow_object.function, workflow_object.components)
            self._validate_workflow_process_result(workflow_result,stage_name)
