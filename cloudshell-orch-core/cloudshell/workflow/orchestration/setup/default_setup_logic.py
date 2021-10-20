from multiprocessing.pool import ThreadPool
from threading import Lock

from cloudshell.api.cloudshell_api import *
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from cloudshell.workflow.helpers.resource_helpers import *


class DefaultSetupLogic(object):
    NO_DRIVER_ERR = "129"
    DRIVER_FUNCTION_ERROR = "151"

    @staticmethod
    def try_exeucte_autoload(api, deploy_result, resource_details_cache, reservation_id, logger, components):
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
        successfully_autoloaded_apps_names = []

        for deployed_app in deploy_result.ResultItems:
            if not deployed_app.Success:
                continue
            deployed_app_name = deployed_app.AppDeploymentyInfo.LogicalResourceName

            resource_details = api.GetResourceDetails(deployed_app_name)
            resource_details_cache[deployed_app_name] = resource_details

            deployment_attributes = DefaultSetupLogic._get_deployment_attributes(components.apps[deployed_app.AppName])

            attribute_key = "autoload"

            autoload_attribute = DefaultSetupLogic._get_attribute_from_deployed_app_gen_agnostic(attribute_key,
                                                                                                 deployment_attributes)

            autoload = "true"

            if autoload_attribute:
                autoload = autoload_attribute[0].Value

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
                successfully_autoloaded_apps_names.append(deployed_app_name)

            except CloudShellAPIError as exc:
                if exc.code not in (DefaultSetupLogic.NO_DRIVER_ERR,
                                    DefaultSetupLogic.DRIVER_FUNCTION_ERROR):
                    logger.error(
                        "Error executing Autoload command on deployed app {0}. Error: {1}".format(deployed_app_name,
                                                                                                  exc.rawxml))
                    api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                        message='Discovery failed on "{0}": {1}'
                                                        .format(deployed_app_name, exc.message))
                    api.SetResourceLiveStatus(deployed_app_name, "Error", "Discovery failed")

                    # Bug 161222 - we must re-raise the original exception to stop the setup
                    # if there is a discovery error
                    raise

            except Exception as exc:
                logger.error("Error executing Autoload command on deployed app {0}. Error: {1}"
                             .format(deployed_app_name, str(exc)))
                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                    message='Discovery failed on "{0}": {1}'
                                                    .format(deployed_app_name, str(exc)))
                api.SetResourceLiveStatus(deployed_app_name, "Error", "Discovery failed")

                # Bug 161222 - we must re-raise the original exception to stop the setup
                # if there is a discovery error
                raise

        # for devices that are autoloaded and have child resources attempt to call "Connect child resources"
        # which copies CVCs from app to deployed app ports.
        DefaultSetupLogic.remap_connections(api=api, reservation_id=reservation_id,
                                            apps_names=successfully_autoloaded_apps_names, logger=logger)

    @staticmethod
    def _get_attribute_from_deployed_app_gen_agnostic(attribute_key, deployment_attributes):
        attribute = [i for i in deployment_attributes
                     if i.Name.lower() == attribute_key.lower() or
                     i.Name.lower().endswith("." + attribute_key.lower())]
        return attribute

    @staticmethod
    def _get_deployment_attributes(app):
        deployment_path = app.app_request.app_resource.DeploymentPaths[0]
        deployment_attributes = deployment_path.DeploymentService.Attributes
        return deployment_attributes

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

        app_names = list(map(lambda x: x.Name, apps))
        app_inputs = list(map(lambda x: DeployAppInput(x.Name, "Name", x.Name), apps))

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
    def activate_routes(api, reservation_details, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :param logging.Logger logger:
        """
        routes = reservation_details.ReservationDescription.RequestedRoutesInfo
        bi_endpoints = []
        uni_endpoints = []
        for route_endpoint in routes:
            if route_endpoint.Target and route_endpoint.Source:
                if route_endpoint.RouteType == 'bi':
                    bi_endpoints.append(route_endpoint.Source)
                    bi_endpoints.append(route_endpoint.Target)
                elif route_endpoint.RouteType == 'uni':
                    uni_endpoints.append(route_endpoint.Source)
                    uni_endpoints.append(route_endpoint.Target)

        if not bi_endpoints and not uni_endpoints:
            logger.info("No routes to connect for sandbox {0}".format(reservation_id))
            return

        logger.info("Executing connect routes for sandbox {0}".format(reservation_id))

        api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                            message='Connecting all routes')

        logger.debug("Connecting bi_endpoints: {0}".format(",".join(bi_endpoints)))

        if bi_endpoints:
            api.ConnectRoutesInReservation(reservation_id, bi_endpoints, 'bi')

        logger.debug("Connecting uni_endpoints: {0}".format(",".join(uni_endpoints)))
        if uni_endpoints:
            api.ConnectRoutesInReservation(reservation_id, uni_endpoints, 'uni')

    @staticmethod
    def run_async_power_on_refresh_ip(api, reservation_details, deploy_results, resource_details_cache,
                                      reservation_id, logger, components):
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
            DefaultSetupLogic.validate_all_apps_deployed(deploy_results=deploy_results,
                                                         logger=logger)
            return

        pool = ThreadPool(len(resources))
        lock = Lock()
        message_status = {
            "power_on": False,
            "wait_for_ip": False
        }

        async_results = [pool.apply_async(DefaultSetupLogic._power_on_refresh_ip,
                                          (api, lock, message_status, resource, deploy_results, resource_details_cache,
                                           reservation_id, logger, components))
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
    def refresh_vm_details(api, reservation_details, connect_results, resource_details_cache, logger, components):
        """
        :param list components: list of components: App, ReservedResourceInfo or ServiceInstance
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param list connectivity_data:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param logging.Logger logger:
        :return:
        """
        deployed_apps_to_refresh_names = []
        reservation_id = reservation_details.ReservationDescription.Id
        deployed_app_names = \
            DefaultSetupLogic.get_resource_names_deployed_in_reservation(reservation_details, reservation_id)

        for deployed_app_name in deployed_app_names:
            resource_details = get_resource_details_from_cache_or_server(api, deployed_app_name, resource_details_cache)

            if not DefaultSetupLogic._is_deployed_app(resource_details):
                continue

            if DefaultSetupLogic._has_wait_for_ip_attribute(components, resource_details, logger):
                deployed_apps_to_refresh_names.append(deployed_app_name)
                continue

            elif DefaultSetupLogic._was_connected_during_setup(connect_results, deployed_app_name):
                deployed_apps_to_refresh_names.append(deployed_app_name)
                continue

        try:
            if len(deployed_apps_to_refresh_names) > 0:
                logger.info('Refreshing VM Details for {0}'.format(', '.join(deployed_apps_to_refresh_names)))
                api.RefreshVMDetails(reservation_id, deployed_apps_to_refresh_names)
        except Exception as e:
            logger.error("Failed to refresh VM details:\ndeployed apps: {0}\nmessage: {1}"
                         .format(', '.join(deployed_apps_to_refresh_names), str(e)))
            raise Exception("Failed to refresh VM Details")

    @staticmethod
    def _has_wait_for_ip_attribute(components, resource_details, logger):
        """
        Check if wait for ip is set to True
        wait for ip is a parameter that can be on app (but doesnt have to be)

        :param Components components: list of components: App, ReservedResourceInfo or ServiceInstance
        :param resource_details:
        :param logging.Logger logger:
        :return:
        """
        attribute_key = "Wait for IP"

        reserved_resource = components.resources.get(resource_details.Name)
        app = components.apps.get(reserved_resource.AppDetails.AppName)
        if not app:
            # App object is not in cache. It means that this app wasnt deployed during the setup run. Returning false.
            return False

        deployment_attributes = DefaultSetupLogic._get_deployment_attributes(app)
        wait_for_ip_attr = DefaultSetupLogic._get_attribute_from_deployed_app_gen_agnostic(attribute_key,
                                                                                           deployment_attributes)
        wait_for_ip = False
        if wait_for_ip_attr:
            # logical resource attribute can overwrite default wait for ip
            wait_for_ip = wait_for_ip_attr[0].Value

        return wait_for_ip

    @staticmethod
    def _was_connected_during_setup(connect_results, deployed_app_name):
        # get first or default route in which deployed_app_name is in source or target
        # thus, we check if the deployed app was part of a route that was connected during setup
        name = deployed_app_name.lower()
        return hasattr(connect_results, 'Routes') \
               and next((True for result in connect_results.Routes
                         if result.Source.lower() == name or result.Target.lower() == name), False)

    @staticmethod
    def _is_deployed_app(resource_details):
        # all deployed apps have vm details and uid
        vm_details = get_vm_details(resource_details)
        is_deployed_app = True if hasattr(vm_details, "UID") else False
        return is_deployed_app

    @staticmethod
    def get_resource_names_deployed_in_reservation(reservation_details, reservation_id):
        deployed_resource_names = [res.Name for res in
                                   get_resources_created_in_res(reservation_details=reservation_details,
                                                                reservation_id=reservation_id) if
                                   not '\\' in res.Name and not '/' in res.Name]
        return deployed_resource_names

    @staticmethod
    def remap_connections(api, reservation_id, apps_names, logger):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param list[str] apps_names:
        :param logging.Logger logger:
        :return:
        """
        logger.info('Remap connections started ...')

        try:

            remap_result = api.RemapConnections(reservationId=reservation_id, resourcesFullPath=apps_names,
                                                printOutput=True)

            if not remap_result.ResultItems:
                logger.info('No resources connections remapped')
                return

            failed_apps = []
            for remap_result_item in remap_result.ResultItems:
                if remap_result_item.Success:
                    message = "Resource '{0}' connections remapped successfully".format(remap_result_item.ResourceName)
                    logger.info(message)
                else:
                    message = "Resource '{0}' remapping operation failed due to {1}".format(
                        remap_result_item.ResourceName, remap_result_item.Error)
                    logger.error(message)
                    failed_apps.append(remap_result_item.ResourceName)

            if not failed_apps:
                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                    message='Resource connections remapped successfully.')
            else:
                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                    message='Failed to remap connections for resources: {0}. See logs for more details'.format(
                                                        ",".join(failed_apps)))
                raise Exception("Sandbox is Active with Errors - Remap connections operation failed.")

        except Exception as ex:
            logger.error("Error in remap connections. Error: {0}".format(str(ex)))
            raise

    @staticmethod
    def configure_apps(api, reservation_id, logger, appConfigurations=[]):
        """
        :param appConfigurations:
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param logging.Logger logger:
        :return:
        """
        logger.info('App configuration started ...')
        try:
            configuration_result = api.ConfigureApps(reservationId=reservation_id, printOutput=True,
                                                     appConfigurations=appConfigurations)

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
    def _power_on_refresh_ip(api, lock, message_status, resource, deploy_result, resource_details_cache, reservation_id,
                             logger, components):
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
            logger.debug("Getting resource details for resource {0} in sandbox {1}".format(deployed_app_name,
                                                                                           reservation_id))

            resource_details = get_resource_details_from_cache_or_server(api, deployed_app_name, resource_details_cache)
            # check if deployed app
            vm_details = get_vm_details(resource_details)
            if not hasattr(vm_details, "UID"):
                logger.debug("Resource {0} is not a deployed app, nothing to do with it".format(deployed_app_name))
                return True, ""

            for k, v in components.apps.items():
                if v.deployed_app.Name == resource.Name:
                    app = v
                    break
                if v.deployed_app.Name == deployed_app_name:
                    app = v
                    break
            
            # name could be either original app request name, or renamed after deploy; below expression captures that
            if not app:
                app = components.apps.get(resource.AppDetails.AppName)
            if app.app_request.app_resource:
                deployment_attributes = DefaultSetupLogic._get_deployment_attributes(app)
            else:
                logger.info('App has already been deployed - deployment settings defaulting to auto power on and wait for ip')
                deployment_attributes = [AttributeNameValue("Auto Power On","True"), 
                                         AttributeNameValue("Wait for IP","True")]
            attribute_key = "Auto Power On"
            power_on_attribute = DefaultSetupLogic._get_attribute_from_deployed_app_gen_agnostic(attribute_key,
                                                                                                 deployment_attributes)

            if power_on_attribute:
                # logical resource attribute can overwrite default power on behavior
                power_on = power_on_attribute[0].Value

            attribute_key = "Wait for IP"
            wait_for_ip_attr = DefaultSetupLogic._get_attribute_from_deployed_app_gen_agnostic(attribute_key,
                                                                                               deployment_attributes)

            if wait_for_ip_attr:
                # logical resource attribute can overwrite default wait for ip
                wait_for_ip = wait_for_ip_attr[0].Value

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
            api.SetResourceLiveStatus(deployed_app_name, "Error", "Getting deployed app details has failed")

        try:
            DefaultSetupLogic._power_on(api, deployed_app_name, power_on, lock, message_status, reservation_id, logger)
        except Exception as exc:
            logger.error("Error powering on deployed app {0} in sandbox {1}. Error: {2}"
                         .format(deployed_app_name, reservation_id, str(exc)))
            api.SetResourceLiveStatus(deployed_app_name, "Error", "Powering on has failed")
            return False, "Error powering on deployed app {0}".format(deployed_app_name)

        try:
            DefaultSetupLogic._wait_for_ip(api, deployed_app_name, wait_for_ip, lock, message_status, reservation_id,
                                           logger)
        except Exception as exc:
            logger.error("Error refreshing IP on deployed app {0} in sandbox {1}. Error: {2}"
                         .format(deployed_app_name, reservation_id, str(exc)))
            api.SetResourceLiveStatus(deployed_app_name, "Error", "Obtaining IP has failed")
            return False, "Error refreshing IP deployed app {0}. Error: {1}".format(deployed_app_name, str(exc))

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
