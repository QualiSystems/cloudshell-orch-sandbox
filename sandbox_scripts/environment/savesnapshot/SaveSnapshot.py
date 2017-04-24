# coding=utf-8
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from sandbox_scripts.helpers.Networking.save_restore_mgr import SaveRestoreManager
from cloudshell.core.logger.qs_logger import get_qs_logger
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError


class EnvironmentSaveSnapshot:
    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="SaveSnapshot",
                                    log_group=self.reservation_id,
                                    log_category='EnvironmentCommands')


    def execute(self):
        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = SaveRestoreManager(sandbox)


        sandbox.clear_all_resources_live_status()
        try:

            username = helpers.get_reservation_context_details().owner_user
            if sandbox.get_storage_server_resource():
                snapshot_name = sandbox.Blueprint_name+"_"+username+"_"+ os.environ['name']
                sandbox.save_sandbox_as_blueprint(snapshot_name)

                # replace spaces with _ in the snapshot's name
                snapshot_name = snapshot_name.replace(' ', '_')

                saveNRestoreTool.save_config(snapshot_name=snapshot_name, config_type='running',
                                         ignore_models=['Generic TFTP server', 'Config Set Pool','Generic FTP server',
                                                        'netscout switch 3912'])
            else:
                 sandbox.report_error("There is no storage resource (e.g. FTP) available in the reservation",True,True)

        except QualiError as qe:
            self.logger.error("Save snapshot failed. " + str(qe))

        except:
            self.logger.error("Save snapshot. Unexpected error:" + str(sys.exc_info()))

