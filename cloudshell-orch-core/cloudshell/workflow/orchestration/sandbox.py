import sys
from multiprocessing.pool import ThreadPool
import traceback

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as api_helpers

from cloudshell.workflow.orchestration.apps_configuration import AppsConfiguration
from cloudshell.workflow.orchestration.components import Components
from cloudshell.workflow.orchestration.workflow import Workflow
from cloudshell.workflow.profiler.env_profiler import profileit
from cloudshell.workflow.helpers import sandbox_helpers as helpers
from cloudshell.workflow.orchestration.workflow import WorkFlowException


class Sandbox(object):
    def __init__(self):
        self.automation_api = api_helpers.get_api_session()
        self.workflow = Workflow(self)
        self.suppress_exceptions = True
        self._exception = None

        self.connectivityContextDetails = helpers.get_connectivity_context_details()
        self.reservationContextDetails = helpers.get_reservation_context_details()
        self.reservationLifecycleDetails = helpers.get_lifecycle_context_details()
        self.global_inputs = helpers.get_global_inputs()
        self.additional_info_inputs = helpers.get_resource_additional_info_inputs()
        self.requirement_inputs = helpers.get_resource_requirement_inputs()
        self.id = self.reservationContextDetails.id

        reservation_description = self.automation_api.GetReservationDetails(reservationId=self.id, disableCache=True).ReservationDescription

        self.name = reservation_description.Name

        self.components = Components(reservation_description.Resources,
                                     reservation_description.Services,
                                     reservation_description.Apps)

        self.logger = get_qs_logger(log_file_prefix='CloudShell Sandbox Orchestration',
                                    log_group=self.id,
                                    log_category='Orchestration')

        self.apps_configuration = AppsConfiguration(sandbox=self)

    def get_user_param(self, param_name):
        return api_helpers.get_user_param(param_name)

    @profileit(scriptName='Setup')
    def execute_setup(self):
        self.logger.info('Setup execution started')
        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Beginning sandbox setup')
        self.execute_stages()
        self.logger.info('Setup for sandbox {0} completed'.format(self.id))
        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Sandbox setup finished successfully')

    def execute_stages(self):
        api = self.automation_api
        self.automation_api.SetSetupStage('Preparation', self.id)
        self.logger.info('Preparing sandbox. ')
        api.WriteMessageToReservationOutput(reservationId=self.id, message='Preparing connectivity')
        api.PrepareSandboxConnectivity(self.id)
        self._execute_stage(self.workflow._preparation_functions, Workflow.PREPARATION_STAGE_NAME)
        self._executes_stage_sequentially(self.workflow._after_preparation, Workflow.ON_PREPARATION_ENDED_STAGE_NAME)
        self.automation_api.SetSetupStage('Provisioning', self.id)
        self._execute_stage(self.workflow._provisioning_functions, Workflow.PROVISIONING_STAGE_NAME)
        self._executes_stage_sequentially(self.workflow._after_provisioning, Workflow.ON_PROVISIONING_ENDED_STAGE_NAME)
        self.automation_api.SetSetupStage('Connectivity', self.id)
        self._execute_stage(self.workflow._connectivity_functions, Workflow.CONNECTIVITY_STAGE_NAME)
        self._executes_stage_sequentially(self.workflow._after_connectivity, Workflow.ON_CONNECTIVITY_ENDED_STAGE_NAME)
        self.automation_api.SetSetupStage('Configuration', self.id)
        self.components.refresh_components(self)
        self._execute_stage(self.workflow._configuration_functions, Workflow.CONFIGURATION_STAGE_NAME)
        self._executes_stage_sequentially(self.workflow._after_configuration,
                                          Workflow.ON_CONFIGURATION_ENDED_STAGE_NAME)
        self.automation_api.SetSetupStage('Ended', self.id)

    @profileit(scriptName='Teardown')
    def execute_teardown(self):
        if self.workflow._teardown_functions is None:
            self.logger.info('No teardown process was configured for the sandbox')

        else:
            self.logger.info('Before Teardown execution started')

            self._executes_stage_sequentially(self.workflow._before_teardown, Workflow.BEFORE_TEARDOWN_STAGE_NAME)

            self.logger.info('Teardown execution started')

            self._execute_stage(self.workflow._teardown_functions, Workflow.TEARDOWN_STAGE_NAME)

            self.logger.info('Teardown for sandbox {0} completed'.format(self.id))

            self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                message='Sandbox teardown finished successfully')

    def _execute_workflow_process(self, func, components):
        self.logger.info("Executing method: {0}. ".format(func.__name__))
        execution_failed = 0
        try:
            func(self, components)

        except Exception as exc:
            self.logger.info("except Exception as exc")
            execution_failed = 1
            error = exc.message
            self._exception = exc
            if not error or not isinstance(error, str):
                try:
                    error = str(exc)
                except Exception:
                    pass

            if self.suppress_exceptions:
                print (error)
            self.logger.exception("Error was thrown during orchestration execution: ")

        return execution_failed

    def _execute_stage(self, workflow_objects, stage_name):
        """
         :param list[WorkflowObject] workflow_objects:
         :param str stage_name:
         :return:
         """
        number_of_workflow_objects = len(workflow_objects)
        self.logger.info(
            'Executing "{0}" stage, {1} workflow processes found. '.format(stage_name, number_of_workflow_objects))

        if number_of_workflow_objects > 0:
            pool = ThreadPool(number_of_workflow_objects)

            async_results = [pool.apply_async(self._execute_workflow_process, (workflow_object.function,
                                                                               workflow_object.components)) for
                             workflow_object in workflow_objects]

            pool.close()
            pool.join()

            for async_result in async_results:
                result = async_result.get()
                self._validate_workflow_process_result(result, stage_name)

        else:
            self.logger.info('Stage: {0}, No workflow process were found.'.format(stage_name))

    def _validate_workflow_process_result(self, result, stage_name):
        if result == 1:  # failed to execute step
            self.logger.info("error: " + str(self._exception))
            if self.suppress_exceptions:
                msg = 'Error occurred during "{0}" stage, See additional entries in the Activity Feed for more information.'.format(
                    stage_name)
                self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                    message='<font color="red">{0}</font>'.format(msg))
                sys.exit(-1)
            msg = 'Error of type "{0}" occurred during "{1}" stage, with message "{2}". '.format(
                type(self._exception).__name__, stage_name, self._exception.message)
            raise WorkFlowException(msg)

    def _executes_stage_sequentially(self, workflow_objects, stage_name):
        self.logger.info(
            'Executing "{0}" stage ,{1} workflow processes found. '.format(stage_name, len(workflow_objects)))
        for workflow_object in workflow_objects:
            workflow_result = self._execute_workflow_process(workflow_object.function, workflow_object.components)
            self._validate_workflow_process_result(workflow_result, stage_name)

    def _execute_save_internally(self, save_sandbox_name, save_sandbox_description):
        """
        Save sandbox as the current user
        :rtype: SaveSandboxResponseInfo
        """
        try:
            result = self.automation_api.SaveSandbox(self.id, save_sandbox_name, save_sandbox_description, self.reservationLifecycleDetails.currentUserName)
        except Exception as e:
            self.logger.error(e.message)
            self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                                message='<font color="red">{0}</font>'.format(e.message))
            sys.exit(e.message)
        return result

    def execute_save(self):
        self.logger.info('Save execution started')
        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Beginning sandbox save')

        new_saved_sandbox_name = self.reservationLifecycleDetails.saved_sandbox_name
        new_saved_sandbox_description = self.reservationLifecycleDetails.saved_sandbox_description

        self.logger.info('Saving sandbox {0} with as {1}'.format(self.id, new_saved_sandbox_name))

        save_sandbox = self._execute_save_internally(new_saved_sandbox_name,
                                                     new_saved_sandbox_description).SavedSandboxId

        self.logger.info('Save for sandbox {0} completed with saved sandbox id: {1}'.format(self.id, save_sandbox))
        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Sandbox was saved successfully')

    def execute_restore(self):
        self.logger.info('Restore execution started')

        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Beginning sandbox restore')
        self.execute_stages()

        self.logger.info('Restore for sandbox {0} completed'.format(self.id))

        self.automation_api.WriteMessageToReservationOutput(reservationId=self.id,
                                                            message='Sandbox restored successfully')
