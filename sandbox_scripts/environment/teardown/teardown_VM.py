from cloudshell.core.logger import qs_logger
from sandbox_scripts.helpers.Networking.save_restore_mgr import SaveRestoreManager
from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase


class EnvironmentTeardownVM:
    REMOVE_DEPLOYED_RESOURCE_ERROR = 153

    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = qs_logger.get_qs_logger(log_file_prefix="CloudShell Sandbox Teardown",
                                              log_group=self.reservation_id,
                                              log_category='Teardown')
        self.sandbox = SandboxBase(self.reservation_id, self.logger)

    # ---------------------------
    # ---------------------------
    def execute(self):
        self.sandbox.report_info("Beginning VMs cleanup")
        saveNRestoreTool = SaveRestoreManager(self.sandbox)

        filename = "Snapshot_"+self.reservation_id+".txt"
        is_snapshot = False

        # if the current reservation was saved as snapshot we look it by reservation_id
        if saveNRestoreTool.get_storage_manager():
            if saveNRestoreTool.is_snapshot(filename):
                is_snapshot = True
                saveNRestoreTool.delete_src_file(filename)
            else: #if this is a snapshot we look it by blueprint name
                if saveNRestoreTool.is_snapshot():
                    is_snapshot = True

        if is_snapshot:
            self.delete_VM_or_Power_off(to_delete=False)
        else:
            self.delete_VM_or_Power_off(to_delete=True)

    # ---------------------------
    # ---------------------------
    def delete_VM_or_Power_off(self, to_delete=False):
        """
        :param bool to_delete:
        :return:
        """
        # filter out resources not created in this reservation
        resources = self.sandbox.get_root_vm_resources()

        pool = ThreadPool()
        async_results = []
        lock = Lock()
        message_status = {
            "power_off": False,
            "delete": False
        }

        for resource in resources:
            result_obj = pool.apply_async(self._power_off_or_delete_deployed_app,
                                (resource, lock, message_status,to_delete))
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


    # ---------------------------
    # ---------------------------
    def _power_off_or_delete_deployed_app(self, resource, lock, message_status, to_delete):
        """
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ResourceBase resource:
        :return:
        """
        if resource.model.lower() =="vcenter static vm":
            to_delete = False

        try:
            if to_delete:
                with lock:
                    if not message_status['delete']:
                        message_status['delete'] = True
                        self.sandbox.report_info("Apps are being powered off and deleted...",
                                                 write_to_output_window=True)

                self.sandbox.report_info("Executing 'Delete' on deployed app {0}".format(resource.name))
                return resource.name

            else:
                with lock:
                    if not message_status['power_off']:
                        message_status['power_off'] = True
                        self.sandbox.report_info('Apps are being powering off... ',
                                                 write_to_output_window=True)

                with lock:
                    self.sandbox.report_info("Executing 'Power Off' on deployed app {0}"
                                     .format(resource.name))
                    resource.execute_connected_command(self.sandbox.id,"PowerOff", "power")

                return None

        except Exception as exc:
            err_msg = "Error deleting or powering off deployed app {0}. Error: {1}".format(
                resource.name, str(exc))
            self.sandbox.report_error(err_msg,raise_error=False)
            return None

