# coding=utf-8
#from sandbox_scripts.helpers.Networking.NetworkingHealthCheck import *
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from sandbox_scripts.helpers.Networking.save_restore_mgr import SaveRestoreManager
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from cloudshell.core.logger.qs_logger import get_qs_logger
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
import os, sys


class EnvironmentSetupResources(object):
    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="CloudShell Sandbox Setup Resources",
                                    log_group=self.reservation_id,
                                    log_category='Setup')

    def execute(self):
        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = SaveRestoreManager(sandbox)
        sandbox.report_info('Beginning load configuration for resources')
        try:
            sandbox.clear_all_resources_live_status()
            if sandbox.get_storage_server_resource():
                # Get the config set name from the orchestration's params
                config_set_name = ''
                try:
                    config_set_name = os.environ['Set Name']
                except:
                    pass
                #Consider an ignore family capability? This list gets to be a maint issue...?
                ignore_models=['Generic TFTP server', 'Config Set Pool', 'Generic FTP server',
                               'netscout switch 3912', 'Subnet-28', 'Subnet-30', 'GitLab']

                if saveNRestoreTool.get_storage_manager():
                    if saveNRestoreTool.is_snapshot():
                        saveNRestoreTool.load_config(config_stage='Snapshots', config_type='Running',
                                                     ignore_models=ignore_models)
                    else:
                        saveNRestoreTool.load_config(config_stage='Gold', config_type='Running',
                                                 ignore_models=ignore_models,
                                                 config_set_name=config_set_name)
            else:
                sandbox.report_info("Skipping load configuration. No storage resource associated with the blueprint ",
                                    write_to_output_window=True)

            # power on Vms that might be powered off because of the snapshot configuration
            sandbox.power_on_vms()

            # call activate_all_routes_and_connectors
            sandbox.activate_all_routes_and_connectors()

            sandbox.report_info('Sandbox setup finished successfully')

            # Call routes_validation
            #   sandbox.routes_validation()
        except QualiError as qe:
            self.logger.error("Setup failed. " + str(qe))
        except Exception as ex:
            print str(ex.message)
            self.logger.error("Setup failed. Unexpected error:" + str(ex.message) + " : " + (sys.exc_info()[0]))



