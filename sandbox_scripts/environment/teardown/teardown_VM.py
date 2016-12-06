from sandbox_scripts.QualiEnvironmentUtils.Networking.NetworkingSaveNRestore import *
from cloudshell.core.logger import qs_logger
from sandbox_scripts.profiler.env_profiler import profileit
from sandbox_scripts.helpers.resource_helpers import get_vm_custom_param, get_resources_created_in_res


from multiprocessing.pool import ThreadPool
from threading import Lock

class EnvironmentTeardownVM:
    REMOVE_DEPLOYED_RESOURCE_ERROR = 153

    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = qs_logger.get_qs_logger(log_file_prefix="CloudShell Sandbox Teardown",
                                              log_group=self.reservation_id,
                                              log_category='Teardown')

    #@profileit(scriptName="Teardown")
    def execute(self):

        api = helpers.get_api_session()

        reservation_details = api.GetReservationDetails(self.reservation_id)

        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = NetworkingSaveRestore(sandbox)

        filename = "Snapshot_"+self.reservation_id+".txt"

        if saveNRestoreTool.is_snapshot(filename):
            self.delete_VM_and_Power_off(api,reservation_details,to_delete = False)

        else:
            self.delete_VM_and_Power_off(api,reservation_details,to_delete =True)


    def delete_VM_and_Power_off(self,api,reservation_details,to_delete = False):

        """
        :param CloudShellAPISession api:
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :return:
        """
        # filter out resources not created in this reservation
        resources = get_resources_created_in_res(reservation_details=reservation_details,
                                                 reservation_id=self.reservation_id)
        pool = ThreadPool()
        async_results = []
        lock = Lock()
        message_status = {
            "power_off": False,
            "delete": False
        }

        for resource in resources:
            resource_details = api.GetResourceDetails(resource.Name)
            if resource_details.VmDetails:
                result_obj = pool.apply_async(self._power_off_or_delete_deployed_app,
                                              (api, resource_details, lock, message_status,to_delete))
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
                api.RemoveResourcesFromReservation(self.reservation_id, resource_to_delete)
            except CloudShellAPIError as exc:
                if exc.code == EnvironmentTeardownVM.REMOVE_DEPLOYED_RESOURCE_ERROR:
                    self.logger.error(
                            "Error executing RemoveResourcesFromReservation command. Error: {0}".format(exc.message))
                    api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                        message=exc.message)


    def _power_off_or_delete_deployed_app(self, api, resource_info, lock, message_status,to_delete):
        """
        :param CloudShellAPISession api:
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ResourceInfo resource_info:
        :return:
        """
        resource_name = resource_info.Name

        try:

            self.logger.info("Executing 'Delete' on deployed app {0} in reservation {1}"
                               .format(resource_name, self.reservation_id))
            if to_delete:
                with lock:
                    if not message_status['delete']:
                        message_status['delete'] = True
                        if not message_status['power_off']:
                            message_status['power_off'] = True
                            api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                                message='Apps are being powered off and deleted...Inga')
                        else:
                            api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                                message='Apps are being deleted...Inga')

                return resource_name

            else:

                api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                   message="Executing 'Power Off' on deployed app {0} in reservation {1}"
                                                    .format(resource_name, self.reservation_id))


                self.logger.info("Executing 'Power Off' on deployed app {0} in reservation {1}"
                                 .format(resource_name, self.reservation_id))

                if not message_status['power_off']:
                    with lock:
                        if not message_status['power_off']:
                            message_status['power_off'] = True
                            api.WriteMessageToReservationOutput(reservationId=self.reservation_id,
                                                                    message='Apps are powering off...')

                    api.ExecuteResourceConnectedCommand(self.reservation_id, resource_name, "PowerOff", "power")
                else:
                    self.logger.info("Auto Power Off is disabled for deployed app {0} in reservation {1}"
                                     .format(resource_name, self.reservation_id))
                return None

        except Exception as exc:
            self.logger.error("Error deleting or powering off deployed app {0} in reservation {1}. Error: {2}"
                              .format(resource_name, self.reservation_id, str(exc)))
            return None

