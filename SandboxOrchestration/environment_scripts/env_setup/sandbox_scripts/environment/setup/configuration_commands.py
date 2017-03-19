from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from remap_child_resources_constants import MISSING_COMMAND_ERROR
import cPickle
import traceback

TARGET_TYPE_RESOURCE = 'Resource'
PRE_AUTOLOAD_CONFIGURATION_STEPS = 'pre_autoload_configuration_command'
PYTHON_DRIVER_CONFIGURE = 'configure_device_command'
RESOURCE_COMMAND_CONFIGURE_FAMILIES = ['Virtual Traffic Generator Chassis']
NO_DRIVER_ERR = "129"
DRIVER_FUNCTION_ERROR = "151"


def pre_autoload_configuration_step(api, deployed_app, sandbox_id):
        # for devices that have a pre-autoload configuration step run it
        # example: add vnics to a vm before running autoload
        _run_configuration_step(api, deployed_app, sandbox_id, PRE_AUTOLOAD_CONFIGURATION_STEPS)


def driver_command_configure_step(api, deployed_app, sandbox_id, param_args):
    # for devices that need to run configuration after all other steps have finished
    _run_configuration_step(api, deployed_app, sandbox_id, PYTHON_DRIVER_CONFIGURE, param_args)


def _run_configuration_step(api, deployed_app, sandbox_id, configuration_step_command_name, param_args=[]):
        deployed_app_name = deployed_app.AppDeploymentyInfo.LogicalResourceName
        api.ExecuteCommand(sandbox_id, deployed_app_name,
                           TARGET_TYPE_RESOURCE,
                           configuration_step_command_name, param_args)


def call_resource_command_configure(api, deploy_result, resource_details_cache, logger, sandbox_id):
        message_written = False

        resource_cache_pickle_string = cPickle.dumps(resource_details_cache)
        # api.WriteMessageToReservationOutput(sandbox_id, resource_cache_pickle_string)
        configure_params = [InputNameValue('resource_cache', resource_cache_pickle_string)]

        for deployed_app in deploy_result.ResultItems:
            if not deployed_app.Success:
                continue
            deployed_app_name = deployed_app.AppDeploymentyInfo.LogicalResourceName
            app_resource_details = resource_details_cache[deployed_app_name]

            if app_resource_details.ResourceFamilyName not in RESOURCE_COMMAND_CONFIGURE_FAMILIES:
                continue

            try:
                logger.info("Called configure resource command on deployed app {0}".format(deployed_app_name))
                if not message_written:
                    api.WriteMessageToReservationOutput(sandbox_id, 'Calling configure command on device...')
                    message_written = True

                driver_command_configure_step(api, deployed_app, sandbox_id, configure_params)

            except CloudShellAPIError as exc:
                if exc.code not in (NO_DRIVER_ERR,
                                    DRIVER_FUNCTION_ERROR,
                                    MISSING_COMMAND_ERROR):
                    logger.error(
                        "Error executing Configure Resource command on deployed app {0}. Error: {1}".format(
                            deployed_app_name,
                            exc.rawxml))
                    api.WriteMessageToReservationOutput(sandbox_id, 'Configuration failed on "{0}": {1}'
                                                        .format(deployed_app_name, exc.message))

            except Exception as exc:
                logger.error("Error executing Configure Resource command on deployed app {0}. Error: {1}"
                             .format(deployed_app_name, str(exc)))
                api.WriteMessageToReservationOutput(sandbox_id, 'Discovery failed on "{0}": {1}\n{2}'
                                                    .format(deployed_app_name, exc.message, traceback.print_exc()))