from multiprocessing.pool import ThreadPool
from threading import Lock

from cloudshell.core.logger import qs_logger

from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *


class EnvironmentTeardownVM:
    REMOVE_DEPLOYED_RESOURCE_ERROR = 153

    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = qs_logger.get_qs_logger(log_file_prefix="CloudShell Sandbox Teardown",
                                              log_group=self.reservation_id,
                                              log_category='Teardown')
        self.sandbox = None

    def execute(self):

        self.sandbox = SandboxBase(self.reservation_id, self.logger)

        self.sandbox.report_info("Beginning VMs cleanup")

        reservation_details = self.sandbox.api_session.GetReservationDetails(self.reservation_id)


        saveNRestoreTool = NetworkingSaveRestore(self.sandbox)

        filename = "Snapshot_"+self.reservation_id+".txt"

        is_snapshot = False

        #if the current reservation was saved as snapshot we look it by reservation_id
        if saveNRestoreTool.get_storage_manager():
            if saveNRestoreTool.is_snapshot(filename):
                is_snapshot = True
                saveNRestoreTool.delete_src_file(filename)
            else: #if this is a snapshot we look it by blueprint name
                if saveNRestoreTool.is_snapshot():
                    is_snapshot = True

        if is_snapshot:
            self.delete_VM_or_Power_off(reservation_details, to_delete = False)

        else:
            self.delete_VM_or_Power_off(reservation_details, to_delete =True)

    def delete_VM_or_Power_off(self, reservation_details, to_delete = False):

        """
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param str reservation_id:
        :return:
        """
        # filter out resources not created in this reservation
        resources = reservation_details.ReservationDescription.Resources

        pool = ThreadPool()
        async_results = []
        lock = Lock()
        message_status = {
            "power_off": False,
            "delete": False
        }

        for resource in resources:
            resource_details = self.sandbox.api_session.GetResourceDetails(resource.Name)
            vm_details = resource_details.VmDetails
            if hasattr(vm_details, "UID"):
                result_obj = pool.apply_async(self._power_off_or_delete_deployed_app,
                                    (resource_details, lock, message_status,to_delete))
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
                self.sandbox.api_session.RemoveResourcesFromReservation(self.reservation_id, resource_to_delete)
            except CloudShellAPIError as exc:
                if exc.code == EnvironmentTeardownVM.REMOVE_DEPLOYED_RESOURCE_ERROR:
                    self.sandbox.report_error(error_message=exc.message,
                              log_message="Error executing RemoveResourcesFromReservation command. "
                                          "Error: {0}".format(exc.message),
                              raise_error=True, write_to_output_window=True)


    def _power_off_or_delete_deployed_app(self, resource_info, lock, message_status, to_delete):
        """
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ResourceInfo resource_info:
        :return:
        """
        resource_name = resource_info.Name

        if resource_info.ResourceModelName.lower() =="vcenter static vm":
            to_delete = False

        try:

            if to_delete:
                with lock:
                    if not message_status['delete']:
                        message_status['delete'] = True
                        self.sandbox.report_info("Apps are being powered off and deleted...",
                                                 write_to_output_window=True)

                self.logger.info("Executing 'Delete' on deployed app {0} in reservation {1}"
                                 .format(resource_name, self.reservation_id))

                return resource_name

            else:
                with lock:
                    if not message_status['power_off']:
                        message_status['power_off'] = True
                        self.sandbox.report_info('Apps are being powering off... ',
                                                 write_to_output_window=True)

                with lock:
                    self.logger.info("Executing 'Power Off' on deployed app {0}"
                                     .format(resource_name, self.reservation_id))
                    self.sandbox.api_session.ExecuteResourceConnectedCommand(self.reservation_id, resource_name,
                                                                        "PowerOff", "power")

                return None

        except Exception as exc:
            self.logger.error("Error deleting or powering off deployed app {0} in reservation {1}. Error: {2}"
                              .format(resource_name, self.reservation_id, str(exc)))
            return None

