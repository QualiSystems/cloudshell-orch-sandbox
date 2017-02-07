# coding=utf-8
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *


class EnvironmentSaveSnapshot:
    def __init__(self):
        self.reservation_id = helpers.get_reservation_context_details().id
        self.logger = get_qs_logger(log_file_prefix="SaveSnapshot",
                                    log_group=self.reservation_id,
                                    log_category='EnvironmentCommands')


   # @profileit(scriptName='SaveSnapshot')
    def execute(self):
        sandbox = SandboxBase(self.reservation_id, self.logger)
        saveNRestoreTool = NetworkingSaveRestore(sandbox)


        sandbox.clear_all_resources_live_status()
        try:

            username = helpers.get_reservation_context_details().owner_user

            snapshot_name = sandbox.Blueprint_name+"_"+username+"_"+ os.environ['name']

            sandbox.save_sandbox_as_blueprint(snapshot_name)


            # replace spaces with _ in the snapshot's name
            snapshot_name = snapshot_name.replace(' ', '_')

            saveNRestoreTool.save_config(snapshot_name=snapshot_name, config_type='running',
                                         ignore_models=['Generic TFTP server', 'Config Set Pool','Generic FTP server',
                                                        'netscout switch 3912'])

        except QualiError as qe:
            self.logger.error("Save snapshot failed. " + str(qe))

        except:
            self.logger.error("Save snapshot. Unexpected error:" + str(sys.exc_info()))

