# coding=utf-8
from multiprocessing.pool import ThreadPool
from threading import Lock

from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from cloudshell.workflow.helpers.resource_helpers import *


class DefaultTeardownLogic:
    REMOVE_DEPLOYED_RESOURCE_ERROR = 153

    @staticmethod
    def disconnect_all_routes_in_reservation(api, reservation_details, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :param Logger logger:
        :return:
        """
        connectors = reservation_details.ReservationDescription.Connectors
        endpoints = []
        for endpoint in connectors:
            if endpoint.State in ['Connected', 'PartiallyConnected'] \
                    and endpoint.Target and endpoint.Source:
                endpoints.append(endpoint.Target)
                endpoints.append(endpoint.Source)

        if not endpoints:
            logger.info("No routes to disconnect for reservation {0}".format(reservation_id))
            return

        try:
            logger.info("Executing disconnect routes for reservation {0}".format(reservation_id))
            api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                message="Disconnecting all apps...")
            api.DisconnectRoutesInReservation(reservation_id, endpoints)

        except CloudShellAPIError as cerr:
            if cerr.code != "123":  # ConnectionNotFound error code
                logger.error("Error disconnecting all routes in reservation {0}. Error: {1}"
                                  .format(reservation_id, str(cerr)))
                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                    message="Error disconnecting apps. Error: {0}".format(cerr.message))

        except Exception as exc:
            logger.error("Error disconnecting all routes in reservation {0}. Error: {1}"
                              .format(reservation_id, str(exc)))
            api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                message="Error disconnecting apps. Error: {0}".format(exc.message))

    @staticmethod
    def power_off_and_delete_all_vm_resources(api, reservation_details, reservation_id, logger, components):
        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :param Logger logger:
        :return:
        """
        # filter out resources not created in this reservation
        resources = get_resources_created_in_res(reservation_details=reservation_details,
                                                 reservation_id=reservation_id)

        pool = ThreadPool()
        async_results = []
        lock = Lock()
        message_status = {
            "power_off": False,
            "delete": False
        }

        for resource in resources:
            if resource.VmDetails:
                result_obj = pool.apply_async(DefaultTeardownLogic._power_off_or_delete_deployed_app,
                                              (api, resource, lock, message_status, reservation_id, logger, components))
                async_results.append(result_obj)

        pool.close()
        pool.join()

        resource_to_delete = []
        for async_result in async_results:
            result = async_result.get()
            if result is not None:
                resource_to_delete.append(result)

        # delete resource - bulk
        if resource_to_delete:
            try:
                api.RemoveResourcesFromReservation(reservation_id, resource_to_delete)
            except CloudShellAPIError as exc:
                if exc.code == DefaultTeardownLogic.REMOVE_DEPLOYED_RESOURCE_ERROR:
                    logger.error(
                        "Error executing RemoveResourcesFromReservation command. Error: {0}".format(exc.message))
                    api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                        message=exc.message)

    @staticmethod
    def cleanup_connectivity(api, reservation_id, logger):
        """
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param Logger logger:
        :return:
        """
        logger.info("Cleaning-up connectivity for reservation {0}".format(reservation_id))
        api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                            message='Cleaning-up connectivity')
        api.CleanupSandboxConnectivity(reservation_id)

    @staticmethod
    def _power_off_or_delete_deployed_app(api, resource_info, lock, message_status, reservation_id, logger, components):
        """
        :param CloudShellAPISession api:
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ResourceInfo resource_info:
        :param str reservation_id:
        :param Logger logger:
        :return:
        """
        resource_name = resource_info.Name
        try:
            delete = "true"
            paramsList = components.apps[resource_name].deployed_app.VmDetails.VmCustomParams
            autoDeleteParms = [i for i in paramsList if i.Name == "auto_delete"]
            if autoDeleteParms:
                delete = autoDeleteParms[0].Value

            if delete.lower() == "true":
                logger.info("Executing 'Delete' on deployed app {0} in reservation {1}"
                                 .format(resource_name, reservation_id))

                if not message_status['delete']:
                    with lock:
                        if not message_status['delete']:
                            message_status['delete'] = True
                            if not message_status['power_off']:
                                message_status['power_off'] = True
                                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                                    message='Apps are being powered off and deleted...')
                            else:
                                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                                    message='Apps are being deleted...')

                # removed call to destroy_vm_only from this place because it will be called from
                # the server in RemoveResourcesFromReservation

                return resource_name
            else:
                power_off = "true"
                paramsList = components.apps[resource_name].deployed_app.VmDetails.VmCustomParams
                autoPowerOffParms = [i for i in paramsList if i.Name == "auto_power_off"]
                if autoPowerOffParms:
                    power_off = autoPowerOffParms[0].Value

                if power_off.lower() == "true":
                    logger.info("Executing 'Power Off' on deployed app {0} in reservation {1}"
                                     .format(resource_name, reservation_id))

                    if not message_status['power_off']:
                        with lock:
                            if not message_status['power_off']:
                                message_status['power_off'] = True
                                api.WriteMessageToReservationOutput(reservationId=reservation_id,
                                                                    message='Apps are powering off...')

                    api.ExecuteResourceConnectedCommand(reservation_id, resource_name, "PowerOff", "power")
                else:
                    logger.info("Auto Power Off is disabled for deployed app {0} in reservation {1}"
                                     .format(resource_name, reservation_id))
            return None
        except Exception as exc:
            logger.error("Error deleting or powering off deployed app {0} in reservation {1}. Error: {2}"
                              .format(resource_name, reservation_id, str(exc)))
            return None
