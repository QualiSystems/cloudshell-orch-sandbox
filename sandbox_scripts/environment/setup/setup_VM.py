from multiprocessing.pool import ThreadPool
from threading import Lock
from sandbox_scripts.profiler.env_profiler import profileit
from sandbox_scripts.QualiEnvironmentUtils.Networking.NetworkingSaveNRestore import *
from cloudshell.core.logger import qs_logger
from sandbox_scripts.helpers.resource_helpers import *

class EnvironmentSetupVM(object):

    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                    log_group=self.reservation_id,
                                    log_category='Setup')

    #@profileit(scriptName='Setup')
    def execute(self):
        api = helpers.get_api_session()

        api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                            message='Beginning resources power On Inga!!')

        reservation_details = api.GetReservationDetails(self.reservation_id)

        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = NetworkingSaveRestore(sandbox)

        if saveNRestoreTool.is_snapshot():
            self._run_async_power_on_refresh_ip_install(api,reservation_details)

       # self._run_async_power_on_refresh_ip_install(api,reservation_details)

    def _run_async_power_on_refresh_ip_install(self, api, reservation_details):

        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param BulkAppDeploymentyInfo deploy_results:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param str reservation_id:
        :return:
        """
        # filter out resources not created in this reservation

        api.WriteMessageToReservationOutput(
                reservationId=self.reservation_id,
                message='Start power on!! Inga!')

        resources = reservation_details.ReservationDescription.Resources

        if len(resources) == 0:
            api.WriteMessageToReservationOutput(
                reservationId=self.reservation_id,
                message='No resources to power on or install Inga')
            return

        pool = ThreadPool(len(resources))
        lock = Lock()
        message_status = {
            "power_on": False,
            "wait_for_ip": False,
            "install": False
            }

        async_results = [pool.apply_async(self._power_on_refresh_ip,
                                          (api,lock, message_status, resource))
                         for resource in resources]

        pool.close()
        pool.join()

        for async_result in async_results:
            res = async_result.get()
            if not res[0]:
                raise Exception("Reservation is Active with Errors - " + res[1])



    def _power_on_refresh_ip(self, api, lock, message_status, resource):
        """
        :param CloudShellAPISession api:
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ReservedResourceInfo resource:

        :return:
        """

        deployed_app_name = resource.Name

        resource_details = api.GetResourceDetails(deployed_app_name)
        vm_details = resource_details.VmDetails

        if not hasattr(vm_details, "UID"):
            self.logger.debug("Resource {0} is not a deployed app, nothing to do with it".format(deployed_app_name))
            return True, ""

        power_on = "true"
        wait_for_ip = "true"
        install = "true"

        try:
            self._power_on(api, deployed_app_name, power_on, lock, message_status)
        except Exception as exc:
            self.logger.error("Error powering on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.reservation_id, str(exc)))
            return False, "Error powering on deployed app {0}".format(deployed_app_name)

        try:
            self._wait_for_ip(api, deployed_app_name, wait_for_ip, lock, message_status)
        except Exception as exc:
            self.logger.error("Error refreshing IP on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.reservation_id, str(exc)))
            return False, "Error refreshing IP deployed app {0}. Error: {1}".format(deployed_app_name, exc.message)

        return True,""


    def _wait_for_ip(self, api, deployed_app_name, wait_for_ip, lock, message_status):
        if wait_for_ip.lower() == "true":

            if not message_status['wait_for_ip']:
                with lock:
                    if not message_status['wait_for_ip']:
                        message_status['wait_for_ip'] = True
                        api.WriteMessageToReservationOutput(
                            reservationId=self.reservation_id,
                            message='Waiting for apps IP addresses, this may take a while...Inga')

            self.logger.info("Executing 'Refresh IP' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

            api.ExecuteResourceConnectedCommand(self.reservation_id, deployed_app_name,
                                                "remote_refresh_ip",
                                                "remote_connectivity")
        else:
            self.logger.info("Wait For IP is off for deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

    def _power_on(self, api, deployed_app_name, power_on, lock, message_status):

        api.WriteMessageToReservationOutput(
                            reservationId=self.reservation_id,
                            message="Executing 111 'Power On' on deployed app {0} in reservation {1} Inga"
                                .format(deployed_app_name, self.reservation_id))
        self.logger.info("Executing 111 'Power On' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

        if power_on.lower() == "true":

            api.WriteMessageToReservationOutput(
                            reservationId=self.reservation_id,
                            message="Executing 222 'Power On' on deployed app {0} in reservation {1} Inga"
                                .format(deployed_app_name, self.reservation_id))

            self.logger.info("Executing 222 'Power On' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))
            with lock:
                if not message_status['power_on']:
                    message_status['power_on'] = True
                    api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                            message='Apps are powering on... Inga')

            api.ExecuteResourceConnectedCommand(self.reservation_id, deployed_app_name, "PowerOn", "power")


        else:
            self.logger.info("Auto Power On is off for deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

