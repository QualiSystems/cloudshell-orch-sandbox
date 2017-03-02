# coding=utf-8
from cloudshell.core.logger import qs_logger

from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *


class EnvironmentTeardownResources:
    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = qs_logger.get_qs_logger(log_file_prefix="CloudShell Sandbox Teardown Resources",
                                              log_group=self.reservation_id,
                                              log_category='Teardown')

    #@profileit(scriptName="Teardown")
    def execute(self):
        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = NetworkingSaveRestore(sandbox)

        sandbox.report_info("Beginning resources config load")
        sandbox.clear_all_resources_live_status()
        try:
            if saveNRestoreTool.get_storage_client():
                ignore_models = ['Generic TFTP server', 'Config Set Pool', 'Generic FTP server', 'netscout switch 3912',
                             'OnPATH Switch 3903', 'Ixia Traffic generator']
                saveNRestoreTool.load_config(config_stage='Base', config_type='Running',
                                         ignore_models=ignore_models, remove_temp_files=True, in_teardown_mode=True)
            else:
                sandbox.report_info("Skipping load configuration. No storage resource associated with the blueprint ",
                                    write_to_output_window=True)

        except QualiError as qe:
            self.logger.error("Teardown failed. " + str(qe))
        except:
            self.logger.error("Teardown failed. Unexpected error:" + str(sys.exc_info()[0]))
