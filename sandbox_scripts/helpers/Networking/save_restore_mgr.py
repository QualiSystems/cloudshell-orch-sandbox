from sandbox_scripts.helpers.Networking.vm_save_restore import *
from sandbox_scripts.helpers.Networking.NetworkingSaveNRestore import *

class SaveRestoreManager(object):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox):
        self.networking_save_restore = NetworkingSaveRestore(sandbox)
        self.vm_save_restore = VMsSaveRestore(sandbox)

    # ----------------------------------
    # ----------------------------------
    def load_config(self, config_stage, config_type, restore_method="Override", config_set_name='', ignore_models=None,
                    write_to_output=True, remove_temp_files = False, in_teardown_mode = False,use_Config_file_path_attr = False):
        #TODO:parallel both vms and resources
        self.networking_save_restore.load_config(config_type=config_type,restore_method=restore_method,
                                                 config_set_name=config_set_name,ignore_models=ignore_models,
                                                 write_to_output=write_to_output,remove_temp_files=remove_temp_files,
                                                 use_Config_file_path_attr=use_Config_file_path_attr)

        self.vm_save_restore.load_config(config_stage=config_stage, config_set_name=config_set_name,
                                         ignore_models=ignore_models,write_to_output=write_to_output,
                                         in_teardown_mode=in_teardown_mode)

    # ----------------------------------
    # ----------------------------------
    def save_config(self, snapshot_name, config_type, ignore_models=None, write_to_output=True):
        #TODO:parallel both vms and resources
        self.networking_save_restore.save_config(snapshot_name=snapshot_name,config_type=config_type,
                                                 ignore_models=ignore_models,write_to_output=write_to_output)

        self.vm_save_restore.save_config(snapshot_name=snapshot_name , config_type=config_type,
                                         ignore_models=ignore_models, write_to_output=write_to_output)

    # ----------------------------------
    # ----------------------------------
    def get_storage_manager(self):
        return self.vm_save_restore.get_storage_manager()

    # ----------------------------------
    # Is this Sandbox originates from a snapshot Blueprint?
    # ----------------------------------
    def is_snapshot(self,fileName = " "):
        return self.vm_save_restore.is_snapshot(fileName)