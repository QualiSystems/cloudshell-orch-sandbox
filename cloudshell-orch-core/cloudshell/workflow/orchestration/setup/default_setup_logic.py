from multiprocessing.pool import ThreadPool
from threading import Lock

from cloudshell.api.cloudshell_api import *
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from cloudshell.workflow.helpers.resource_helpers import *
from remap_child_resources_constants import *


class DefaultSetupLogic(object):
    NO_DRIVER_ERR = "129"
    DRIVER_FUNCTION_ERROR = "151"

    @staticmethod
    def prepare_connectivity(api, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param logging.Logger logger:
        """
        logger.info("Preparing connectivity for sandbox {0}".format(reservation_id))
        api.WriteMessageToReservationOutput(reservationId=reservation_id, message='Preparing connectivity')
        api.PrepareSandboxConnectivity(reservation_id)

    @staticmethod
    def try_exeucte_autoload(api, deploy_result, resource_details_cache, reservation_id, logger):
        """
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param CloudShellAPISession api:
        :param BulkAppDeploymentyInfo deploy_result:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param str reservation_id:
        :param logging.Logger logger:
        :return:
        """

        if deploy_result is None:
            logger.info("No apps to discover")
            api.WriteMessageToReservationOutput(reservationId=reservation_id, message='No apps to discover')
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
                logger.info("Apps discovery is disabled on deployed app {0}".format(deployed_app_name))
                continue

            try:
                logger.info("Executing Autoload command on deployed app {0}".format(deployed_app_name))
                if not message_written:
                    api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                        message='Apps are being discovered...')
                    message_written = True

                api.AutoLoad(deployed_app_name)

                # for devices that are autoloaded and have child resources attempt to call "Connect child resources"
                # which copies CVCs from app to deployed app ports.
                api.ExecuteCommand(reservation_id, deployed_app_name,
                                   TARGET_TYPE_RESOURCE,
                                   REMAP_CHILD_RESOURCES, [])

            except CloudShellAPIError as exc:
                if exc.code not in (DefaultSetupLogic.NO_DRIVER_ERR,
                                    DefaultSetupLogic.DRIVER_FUNCTION_ERROR,
                                    MISSING_COMMAND_ERROR):
                    logger.error(
                        "Error executing Autoload command on deployed app {0}. Error: {1}".format(deployed_app_name,
                                                                                                  exc.rawxml))
                    api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                        message='Discovery failed on "{0}": {1}'
                                                        .format(deployed_app_name, exc.message))

            except Exception as exc:
                logger.error("Error executing Autoload command on deployed app {0}. Error: {1}"
                                  .format(deployed_app_name, str(exc)))
                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                    message='Discovery failed on "{0}": {1}'
                                                    .format(deployed_app_name, exc.message))

    @staticmethod
    def deploy_apps_in_reservation(api, reservation_details, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :param logging.Logger logger:
        :return:
        """
        apps = reservation_details.ReservationDescription.Apps
        if not apps or (len(apps) == 1 and not apps[0].Name):
            logger.info("No apps found in sandbox {0}".format(reservation_id))
            api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                message='No apps to deploy')
            return None

        app_names = map(lambda x: x.Name, apps)
        app_inputs = map(lambda x: DeployAppInput(x.Name, "Name", x.Name), apps)

        api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                            message='Apps deployment started')
        logger.info(
            "Deploying apps for sandbox {0}. App names: {1}".format(reservation_id, ", ".join(app_names)))

        res = api.DeployAppToCloudProviderBulk(reservation_id, app_names, app_inputs)

        return res

    @staticmethod
    def connect_all_routes_in_reservation(api, reservation_details, reservation_id, resource_details_cache, logger):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param logging.Logger logger:
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
            logger.info("No routes to connect for sandbox {0}".format(reservation_id))
            return

        logger.info("Executing connect routes for sandbox {0}".format(reservation_id))
        logger.debug("Connecting: {0}".format(",".join(endpoints)))
        api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                            message='Connecting all apps')
        res = api.ConnectRoutesInReservation(reservation_id, endpoints, 'bi')
        return res

    @staticmethod
    def run_async_power_on_refresh_ip(api, reservation_details, deploy_results, resource_details_cache,
                                       reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param BulkAppDeploymentyInfo deploy_results:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param str reservation_id:
        :param logging.Logger logger:
        :return:
        """
        # filter out resources not created in this reservation

        resources = get_resources_created_in_res(reservation_details=reservation_details, reservation_id=reservation_id)
        if len(resources) == 0:
            api.WriteMessageToReservationOutput(
                reservationId=reservation_id,
                message='No resources to power on')
            DefaultSetupLogic.validate_all_apps_deployed(deploy_results)
            return

        pool = ThreadPool(len(resources))
        lock = Lock()
        message_status = {
            "power_on": False,
            "wait_for_ip": False
        }

        async_results = [pool.apply_async(DefaultSetupLogic._power_on_refresh_ip,
                                          (api, lock, message_status, resource, deploy_results, resource_details_cache, reservation_id, logger))
                         for resource in resources]

        pool.close()
        pool.join()

        for async_result in async_results:
            res = async_result.get()
            if not res[0]:
                raise Exception("Sandbox is Active with Errors - " + res[1])

        DefaultSetupLogic.validate_all_apps_deployed(deploy_results=deploy_results,
                                                     logger=logger)

    @staticmethod
    def configure_apps(api, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param logging.Logger logger:
        :return:
        """
        logger.info('App configuration started ...')
        try:
            configuration_result = api.ConfigureApps(reservationId=reservation_id)

            if not configuration_result.ResultItems:
                api.WriteMessageToReservationOutput(reservationId=reservation_id, message='No apps to configure')
                return

            failed_apps = []
            for conf_res in configuration_result.ResultItems:
                if conf_res.Success:
                    message = "App '{0}' configured successfully".format(conf_res.AppName)
                    logger.info(message)
                else:
                    message = "App '{0}' configuration failed due to {1}".format(conf_res.AppName,
                                                                                 conf_res.Error)
                    logger.error(message)
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
            logger.error("Error configuring apps. Error: {0}".format(str(ex)))
            raise

    @staticmethod
    def validate_all_apps_deployed(deploy_results, logger):
        logger.info("validating apps deployment results")
        if deploy_results is not None:
            for deploy_res in deploy_results.ResultItems:
                if not deploy_res.Success:
                    logger.info("app " + deploy_res.AppName + " ended with error")
                    raise Exception("Sandbox is Active with Errors - " + deploy_res.Error)

    @staticmethod
    def _power_on_refresh_ip(api, lock, message_status, resource, deploy_result, resource_details_cache, reservation_id, logger):
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
            logger.debug("Getting resource details for resource {0} in sandbox {1}"
                              .format(deployed_app_name, reservation_id))

            resource_details = get_resource_details_from_cache_or_server(api, deployed_app_name, resource_details_cache)
            # check if deployed app
            vm_details = get_vm_details(resource_details)
            if not hasattr(vm_details, "UID"):
                logger.debug("Resource {0} is not a deployed app, nothing to do with it".format(deployed_app_name))
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
            logger.error("Error getting resource details for deployed app {0} in sandbox {1}. "
                              "Will use default settings. Error: {2}".format(deployed_app_name,
                                                                             reservation_id,
                                                                             str(exc)))

        try:
            DefaultSetupLogic._power_on(api, deployed_app_name, power_on, lock, message_status, reservation_id, logger)
        except Exception as exc:
            logger.error("Error powering on deployed app {0} in sandbox {1}. Error: {2}"
                              .format(deployed_app_name, reservation_id, str(exc)))
            return False, "Error powering on deployed app {0}".format(deployed_app_name)

        try:
            DefaultSetupLogic._wait_for_ip(api, deployed_app_name, wait_for_ip, lock, message_status, reservation_id, logger)
        except Exception as exc:
            logger.error("Error refreshing IP on deployed app {0} in sandbox {1}. Error: {2}"
                              .format(deployed_app_name, reservation_id, str(exc)))
            return False, "Error refreshing IP deployed app {0}. Error: {1}".format(deployed_app_name, exc.message)

        return True, ""

    @staticmethod
    def _wait_for_ip(api, deployed_app_name, wait_for_ip, lock, message_status, reservation_id, logger):
        if wait_for_ip.lower() == "true":
            if not message_status['wait_for_ip']:
                with lock:
                    if not message_status['wait_for_ip']:
                        message_status['wait_for_ip'] = True
                        api.WriteMessageToReservationOutput(
                            reservationId=reservation_id,
                            message='Waiting for apps IP addresses, this may take a while...')

            logger.info("Executing 'Refresh IP' on deployed app {0} in sandbox {1}"
                             .format(deployed_app_name, reservation_id))

            api.ExecuteResourceConnectedCommand(reservation_id, deployed_app_name,
                                                "remote_refresh_ip",
                                                "remote_connectivity")
        else:
            logger.info("Wait For IP is off for deployed app {0} in sandbox {1}"
                             .format(deployed_app_name, reservation_id))

    @staticmethod
    def _power_on(api, deployed_app_name, power_on, lock, message_status, reservation_id, logger):
        if power_on.lower() == "true":
            logger.info("Executing 'Power On' on deployed app {0} in sandbox {1}"
                             .format(deployed_app_name, reservation_id))

            if not message_status['power_on']:
                with lock:
                    if not message_status['power_on']:
                        message_status['power_on'] = True
                        api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                            message='Apps are powering on...')

            api.ExecuteResourceConnectedCommand(reservation_id, deployed_app_name, "PowerOn", "power")
        else:
            logger.info("Auto Power On is off for deployed app {0} in sandbox {1}"
                             .format(deployed_app_name, reservation_id))
