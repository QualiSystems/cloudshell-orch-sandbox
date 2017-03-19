from multiprocessing.pool import ThreadPool
from threading import Lock

from cloudshell.api.cloudshell_api import *
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from sandbox_scripts.helpers.resource_helpers import *
from sandbox_scripts.profiler.env_profiler import profileit

from configuration_commands import pre_autoload_configuration_step, call_resource_command_configure
from remap_child_resources_constants import *
from utils import validate_all_apps_deployed


# In future we will refactor out the following to a separate setup package:
# pre_autoload_app_configuration
#

class EnvironmentSetup(object):
    NO_DRIVER_ERR = "129"
    DRIVER_FUNCTION_ERROR = "151"

    def __init__(self):
        self.sandbox_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                    log_group=self.sandbox_id,
                                    log_category='Setup')

    @profileit('Setup')
    def execute(self):
        api, resource_details_cache, sandbox_msg = self._prepare_execute()
        sandbox_msg('Beginning reservation setup')
        self._setup_sandbox(api, resource_details_cache)
        self.logger.info("Setup for reservation {0} completed".format(self.sandbox_id))
        sandbox_msg('Reservation setup finished successfully')

    def _setup_sandbox(self, api, resource_details_cache):
        self._prepare_connectivity(api)
        deploy_result, sandbox_details = self._deploy_and_autoload_apps(api, resource_details_cache)
        self._connect_all_routes_in_reservation(api, sandbox_details)
        self._run_async_power_on_refresh_ip(api, sandbox_details, deploy_result, resource_details_cache)
        self._configure_apps(api)
        call_resource_command_configure(api, deploy_result, resource_details_cache, self.logger, self.sandbox_id)

    def _deploy_and_autoload_apps(self, api, resource_details_cache):
        sandbox_details = self._get_reservation_details(api)
        deploy_result = self._deploy_apps_in_reservation(api, sandbox_details)
        self._autoload_apps(api, deploy_result, resource_details_cache)
        sandbox_details = self._refresh_sandbox_details_if_apps_deployed(api, deploy_result, sandbox_details)
        return deploy_result, sandbox_details

    def _get_reservation_details(self, api):
        return api.GetReservationDetails(self.sandbox_id)

    def _refresh_sandbox_details_if_apps_deployed(self, api, deploy_result, reservation_details):
        # refresh reservation_details after app deployment if any deployed apps
        if deploy_result and deploy_result.ResultItems:
            reservation_details = api.GetReservationDetails(self.sandbox_id)
        return reservation_details

    def _prepare_execute(self):
        api = helpers.get_api_session()
        resource_details_cache = {}
        def sandbox_msg(x): api.WriteMessageToReservationOutput(self.sandbox_id, x)
        return api, resource_details_cache, sandbox_msg

    def _prepare_connectivity(self, api):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        """
        reservation_id = self.sandbox_id
        self.logger.info("Preparing connectivity for reservation {0}".format(self.sandbox_id))
        api.WriteMessageToReservationOutput(reservationId=self.sandbox_id, message='Preparing connectivity')
        api.PrepareSandboxConnectivity(reservation_id)

    def _autoload_apps(self, api, deploy_result, resource_details_cache):
        """
        :param CloudShellAPISession api:
        :param BulkAppDeploymentyInfo deploy_result:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :return:
        """

        if deploy_result is None:
            self.logger.info("No apps to discover")
            api.WriteMessageToReservationOutput(self.sandbox_id, 'No apps to discover')
            return

        message_written = False

        for deployed_app in deploy_result.ResultItems:
            if not deployed_app.Success:
                continue
            deployed_app_name = deployed_app.AppDeploymentyInfo.LogicalResourceName

            resource_details = api.GetResourceDetails(deployed_app_name)
            resource_details_cache[deployed_app_name] = resource_details

            autoload = "true"
            autoload_param = get_vm_custom_param(resource_details, "autoload")
            if autoload_param:
                autoload = autoload_param.Value
            if autoload.lower() != "true":
                self.logger.info("Apps discovery is disabled on deployed app {0}".format(deployed_app_name))
                continue

            try:
                self.logger.info("Executing Autoload command on deployed app {0}".format(deployed_app_name))
                if not message_written:
                    api.WriteMessageToReservationOutput(self.sandbox_id, 'Apps are being discovered...')
                    message_written = True

                pre_autoload_configuration_step(api, deployed_app, self.sandbox_id)

                api.AutoLoad(deployed_app_name)

                remap_child_resources(api, deployed_app_name, self.sandbox_id)

            except CloudShellAPIError as exc:
                if exc.code not in (EnvironmentSetup.NO_DRIVER_ERR,
                                    EnvironmentSetup.DRIVER_FUNCTION_ERROR,
                                    MISSING_COMMAND_ERROR):
                    self.logger.error(
                        "Error executing Autoload command on deployed app {0}. Error: {1}".format(deployed_app_name,
                                                                                                  exc.rawxml))
                    api.WriteMessageToReservationOutput(self.sandbox_id, 'Discovery failed on "{0}": {1}'
                                                        .format(deployed_app_name, exc.message))

            except Exception as exc:
                self.logger.error("Error executing Autoload command on deployed app {0}. Error: {1}"
                                  .format(deployed_app_name, str(exc)))
                api.WriteMessageToReservationOutput(self.sandbox_id, 'Discovery failed on "{0}": {1}'
                                                    .format(deployed_app_name, exc.message))

    def _deploy_apps_in_reservation(self, api, reservation_details):
        apps = reservation_details.ReservationDescription.Apps
        if not apps or (len(apps) == 1 and not apps[0].Name):
            self.logger.info("No apps found in reservation {0}".format(self.sandbox_id))
            api.WriteMessageToReservationOutput(reservationId=self.sandbox_id,
                                                message='No apps to deploy')
            return None

        app_names = map(lambda x: x.Name, apps)
        app_inputs = map(lambda x: DeployAppInput(x.Name, "Name", x.Name), apps)

        api.WriteMessageToReservationOutput(reservationId=self.sandbox_id,
                                            message='Apps deployment started')
        self.logger.info(
            "Deploying apps for reservation {0}. App names: {1}".format(reservation_details, ", ".join(app_names)))

        res = api.DeployAppToCloudProviderBulk(self.sandbox_id, app_names, app_inputs)

        return res

    def _connect_all_routes_in_reservation(self, api, reservation_details):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :return:
        """
        connectors = reservation_details.ReservationDescription.Connectors
        endpoints = []
        for endpoint in connectors:
            if endpoint.State in ['Disconnected', 'PartiallyConnected', 'ConnectionFailed'] \
                    and endpoint.Target and endpoint.Source:
                endpoints.append(endpoint.Target)
                endpoints.append(endpoint.Source)

        if not endpoints:
            self.logger.info("No routes to connect for reservation {0}".format(self.sandbox_id))
            return

        self.logger.info("Executing connect routes for reservation {0}".format(self.sandbox_id))
        self.logger.debug("Connecting: {0}".format(",".join(endpoints)))
        api.WriteMessageToReservationOutput(reservationId=self.sandbox_id,
                                            message='Connecting all apps')
        res = api.ConnectRoutesInReservation(self.sandbox_id, endpoints, 'bi')
        return res

    def _run_async_power_on_refresh_ip(self, api, reservation_details, deploy_results, resource_details_cache):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param BulkAppDeploymentyInfo deploy_results:
        :return:
        """
        # filter out resources not created in this reservation
        resources = get_resources_created_in_res(reservation_details=reservation_details,
                                                 reservation_id=self.sandbox_id)
        if len(resources) == 0:
            api.WriteMessageToReservationOutput(
                reservationId=self.sandbox_id,
                message='No resources to power on')
            validate_all_apps_deployed(deploy_results)
            return

        pool = ThreadPool(len(resources))
        lock = Lock()
        message_status = {
            "power_on": False,
            "wait_for_ip": False
        }

        async_results = [pool.apply_async(self._power_on_refresh_ip,
                                          (api, lock, message_status, resource, deploy_results, resource_details_cache))
                         for resource in resources]

        pool.close()
        pool.join()

        for async_result in async_results:
            res = async_result.get()
            if not res[0]:
                raise Exception("Reservation is Active with Errors - " + res[1])

        validate_all_apps_deployed(deploy_results)

    def _configure_apps(self, api):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        :return:
        """
        reservation_id = self.sandbox_id
        self.logger.info('App configuration started ...')
        try:
            configuration_result = api.ConfigureApps(reservationId=reservation_id)

            if not configuration_result.ResultItems:
                api.WriteMessageToReservationOutput(reservationId=reservation_id, message='No apps to configure')
                return

            failed_apps = []
            for conf_res in configuration_result.ResultItems:
                if conf_res.Success:
                    message = "App '{0}' configured successfully".format(conf_res.AppName)
                    self.logger.info(message)
                else:
                    message = "App '{0}' configuration failed due to {1}".format(conf_res.AppName,
                                                                                 conf_res.Error)
                    self.logger.error(message)
                    failed_apps.append(conf_res.AppName)

            if not failed_apps:
                api.WriteMessageToReservationOutput(reservationId=reservation_id, message=
                'Apps were configured successfully.')
            else:
                api.WriteMessageToReservationOutput(reservationId=reservation_id, message=
                'Apps: {0} configuration failed. See logs for more details'.format(
                    ",".join(failed_apps)))
                raise Exception("Configuration of apps failed see logs.")
        except Exception as ex:
            self.logger.error("Error configuring apps. Error: {0}".format(str(ex)))
            raise

    def _power_on_refresh_ip(self, api, lock, message_status, resource, deploy_result, resource_details_cache):
        """
        :param CloudShellAPISession api:
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ReservedResourceInfo resource:
        :param BulkAppDeploymentyInfo deploy_result:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :return:
        """

        deployed_app_name = resource.Name
        deployed_app_data = None

        power_on = "true"
        wait_for_ip = "true"

        try:
            self.logger.debug("Getting resource details for resource {0} in reservation {1}"
                              .format(deployed_app_name, self.sandbox_id))

            resource_details = get_resource_details_from_cache_or_server(api, deployed_app_name, resource_details_cache)
            # check if deployed app
            vm_details = get_vm_details(resource_details)
            if not hasattr(vm_details, "UID"):
                self.logger.debug("Resource {0} is not a deployed app, nothing to do with it".format(deployed_app_name))
                return True, ""

            auto_power_on_param = get_vm_custom_param(resource_details, "auto_power_on")
            if auto_power_on_param:
                power_on = auto_power_on_param.Value

            wait_for_ip_param = get_vm_custom_param(resource_details, "wait_for_ip")
            if wait_for_ip_param:
                wait_for_ip = wait_for_ip_param.Value

            # check if we have deployment data
            if deploy_result is not None:
                for data in deploy_result.ResultItems:
                    if data.Success and data.AppDeploymentyInfo.LogicalResourceName == deployed_app_name:
                        deployed_app_data = data
        except Exception as exc:
            self.logger.error("Error getting resource details for deployed app {0} in reservation {1}. "
                              "Will use default settings. Error: {2}".format(deployed_app_name,
                                                                             self.sandbox_id,
                                                                             str(exc)))

        try:
            self._power_on(api, deployed_app_name, power_on, lock, message_status)
        except Exception as exc:
            self.logger.error("Error powering on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.sandbox_id, str(exc)))
            return False, "Error powering on deployed app {0}".format(deployed_app_name)

        try:
            self._wait_for_ip(api, deployed_app_name, wait_for_ip, lock, message_status)
        except Exception as exc:
            self.logger.error("Error refreshing IP on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.sandbox_id, str(exc)))
            return False, "Error refreshing IP deployed app {0}. Error: {1}".format(deployed_app_name, exc.message)

        return True, ""

    def _wait_for_ip(self, api, deployed_app_name, wait_for_ip, lock, message_status):
        if wait_for_ip.lower() == "true":

            if not message_status['wait_for_ip']:
                with lock:
                    if not message_status['wait_for_ip']:
                        message_status['wait_for_ip'] = True
                        api.WriteMessageToReservationOutput(
                            reservationId=self.sandbox_id,
                            message='Waiting for apps IP addresses, this may take a while...')

            self.logger.info("Executing 'Refresh IP' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.sandbox_id))

            api.ExecuteResourceConnectedCommand(self.sandbox_id, deployed_app_name,
                                                "remote_refresh_ip",
                                                "remote_connectivity")
        else:
            self.logger.info("Wait For IP is off for deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.sandbox_id))

    def _power_on(self, api, deployed_app_name, power_on, lock, message_status):
        if power_on.lower() == "true":
            self.logger.info("Executing 'Power On' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.sandbox_id))

            if not message_status['power_on']:
                with lock:
                    if not message_status['power_on']:
                        message_status['power_on'] = True
                        api.WriteMessageToReservationOutput(reservationId=self.sandbox_id,
                                                            message='Apps are powering on...')

            api.ExecuteResourceConnectedCommand(self.sandbox_id, deployed_app_name, "PowerOn", "power")
        else:
            self.logger.info("Auto Power On is off for deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.sandbox_id))


