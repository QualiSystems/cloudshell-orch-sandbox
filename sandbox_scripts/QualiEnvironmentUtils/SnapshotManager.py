#TODO: implement this file/move code from NetworkSaveNResource
from sandbox_scripts.QualiEnvironmentUtils.StorageManager import StorageManager
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
'''
class SnapshotManager(object):
    def __init__(self, storage_mgr):
        self.storage_mgr = storage_mgr
        self.config_files_root = self.storage_mgr.get_configs_root()
    # ----------------------------------
    # Is this Sandbox originates from a snapshot Blueprint?
    # ----------------------------------
    def is_snapshot(self,fileName = " "):
        # check if there is a directory with the Blueprint's name under the snapshots dir
        if fileName != " ":
            env_dir = self.config_files_root + '/Snapshots/' + fileName
        else:
            env_dir = self.config_files_root + '/Snapshots/' + self.sandbox.Blueprint_name

        env_dir = env_dir.replace(' ', '_')
        return self.storage_mgr.dir_exist(env_dir)

    # ----------------------------------
    # delete file name on storage
    # ----------------------------------
    def delete_src_file(self,fileName):

        env_dir = self.config_files_root + '/Snapshots/' + fileName
        env_dir = env_dir.replace(' ', '_')
        self.storage_mgr.delete(env_dir)

    # ----------------------------------
    def create_snapshot_dir(self,snapshot_name):
        env_dir = self.config_files_root + '/Snapshots/' + snapshot_name.strip()
        if not self.storage_mgr.dir_exist(env_dir):
            self.storage_mgr.create_dir(env_dir, write_to_output=True)
'''