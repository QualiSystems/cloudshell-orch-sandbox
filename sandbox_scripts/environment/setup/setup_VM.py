from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *


class EnvironmentSetupVM(object):

    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup",
                                    log_group=self.reservation_id,
                                    log_category='Setup')
        self.is_snapshot = False
        self.sandbox = None

    def execute(self):
        self.sandbox = SandboxBase(self.reservation_id, self.logger)

        self.sandbox.report_info('Beginning VMs power on')

        reservation_details = self.sandbox.api_session.GetReservationDetails(self.reservation_id)

        #TODO: don't use networking save and restore to figure if it's a snapshot setup
        saveNRestoreTool = NetworkingSaveRestore(self.sandbox)
        if saveNRestoreTool.get_storage_manager():
            if saveNRestoreTool.is_snapshot():
                self.is_snapshot = True

        self._run_async_power_on_refresh_ip(reservation_details)


    def _run_async_power_on_refresh_ip(self, reservation_details):

        """
        :param GetReservationDescriptionResponseInfo reservation_details:
        :param BulkAppDeploymentyInfo deploy_results:
        :param (dict of str: ResourceInfo) resource_details_cache:
        :param str reservation_id:
        :return:
        """
        # filter out resources not created in this reservation

        resources = reservation_details.ReservationDescription.Resources

        if len(resources) == 0:
            self.sandbox.report_info(message='No resources to power on ', write_to_output_window=True)
            return

        pool = ThreadPool(len(resources))
        lock = Lock()
        message_status = {
            "power_on": False,
            "wait_for_ip": False
            }
        async_results = [pool.apply_async(self._power_on_refresh_ip,
                                          (lock, message_status, resource))
                         for resource in resources]

        pool.close()
        pool.join()

        for async_result in async_results:
            res = async_result.get()
            if not res[0]:
                raise Exception("Reservation is Active with Errors - " + res[1])

    def _power_on_refresh_ip(self, lock, message_status, resource):
        """
        :param Lock lock:
        :param (dict of str: Boolean) message_status:
        :param ReservedResourceInfo resource:

        :return:
        """

        deployed_app_name = resource.Name

        resource_details = self.sandbox.api_session.GetResourceDetails(deployed_app_name)
        vm_details = resource_details.VmDetails

        if not(vm_details and hasattr(vm_details, "UID") and vm_details.UID):
            #self.logger.debug("Resource {0} is not a app, nothing to do with it".format(deployed_app_name))
            return True, ""

        power_on = "true"
        wait_for_ip = "true"

        if resource.ResourceModelName.lower() =="vcenter static vm":
            self.logger.debug("Resource {0} is a static app".format(deployed_app_name))
            wait_for_ip = "false"

        elif not self.is_snapshot:
            return True, ""


        try:
            self._power_on(deployed_app_name, power_on, lock, message_status)
        except Exception as exc:
            self.logger.error("Error powering on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.reservation_id, str(exc)))
            return False, "Error powering on deployed app {0}".format(deployed_app_name)

        try:
            if resource.ResourceModelName.lower() !="vCenter Static VM":
                self._wait_for_ip(deployed_app_name, wait_for_ip, lock, message_status)
        except Exception as exc:
            self.logger.error("Error refreshing IP on deployed app {0} in reservation {1}. Error: {2}"
                              .format(deployed_app_name, self.reservation_id, str(exc)))
            return False, "Error refreshing IP deployed app {0}. Error: {1}".format(deployed_app_name, exc.message)

        return True,""


    def _wait_for_ip(self, deployed_app_name, wait_for_ip, lock, message_status):

        if wait_for_ip.lower() == "true":

            if not message_status['wait_for_ip']:
                with lock:
                    if not message_status['wait_for_ip']:
                        message_status['wait_for_ip'] = True
                        self.sandbox.report_info(message='Waiting for apps IP addresses, this may take a while...',
                                                 write_to_output_window=True)

            self.logger.info("Executing 'Refresh IP' on deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

            with lock:
                self.sandbox.api_session.ExecuteResourceConnectedCommand(self.reservation_id, deployed_app_name,
                                                "remote_refresh_ip",
                                                "remote_connectivity")
        else:
            self.logger.info("Wait For IP is off for deployed app {0} in reservation {1}"
                             .format(deployed_app_name, self.reservation_id))

    def _power_on(self, deployed_app_name, power_on, lock, message_status):

        if power_on.lower() == "true":
            with lock:
                if not message_status['power_on']:
                    message_status['power_on'] = True
                    self.sandbox.report_info('Apps are powering on... ')

                self.sandbox.report_info(message="Executing 'Power On' on deployed app {0} "
                                         .format(deployed_app_name),
                                         log_message="Executing 'Power On' on deployed app {0} in reservation {1}"
                                         .format(deployed_app_name, self.reservation_id),
                                         write_to_output_window=True)

                self.sandbox.api_session.ExecuteResourceConnectedCommand(self.reservation_id, deployed_app_name,
                                                                         "PowerOn", "power")


        else:
            self.logger.info("Auto Power On is off for deployed app {0} in reservation {1}"
                                    .format(deployed_app_name, self.reservation_id))

