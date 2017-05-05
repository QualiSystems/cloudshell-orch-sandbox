
from sandbox_scripts.QualiEnvironmentUtils.StorageManager import StorageManager


class BaseSaveRestore(object):
    def __init__(self, sandbox):
        """
        Get the root directory for the config files on the storage server
        :param SandboxBase sandbox:  The sandbox save & restore will be done in
        """
        self.sandbox = sandbox
        storage_server_resource = self.sandbox.get_storage_server_resource()
        self.storage_mgr = None
        if storage_server_resource is not None:
            self.storage_mgr = StorageManager(sandbox)
            self.config_files_root = self.storage_mgr.get_configs_root()
        else:
            if self.is_resources_in_reservation_to_restore(ignore_models=None):
                self.sandbox.report_info("Failed to find a storage server resource (e.g. tftp) in the sandbox. ",
                                         write_to_output_window=False)

    # ----------------------------------
    # ----------------------------------
    def get_storage_manager(self):
        return self.storage_mgr

    # ----------------------------------
    # Is this Sandbox originates from a snapshot Blueprint?
    # ----------------------------------
    def is_snapshot(self, fileName=" "):
        # check if there is a directory with the Blueprint's name under the snapshots dir

        if fileName != " ":
            env_dir = self.config_files_root + '/Snapshots/' + fileName
        else:
            env_dir = self.config_files_root + '/Snapshots/' + self.sandbox.Blueprint_name

        env_dir = env_dir.replace(' ', '_')
        return self.storage_mgr.dir_exist(env_dir)

    # ----------------------------------
    # Check if need to load configuration to the given device
    # A device should not be in the ignored models list,
    # or should not have a "Disable Load Config" attribute set to True
    # in order to load configuration on it
    # ----------------------------------
    def _is_load_config_to_device(self, resource, ignore_models=None):
        # check if the device is marked for not loading config during

        if resource.attribute_exist("Disable Load Config"):
            disable_load_config = resource.get_attribute("Disable Load Config")
            if disable_load_config:
                return False

        if ignore_models:
            for ignore_model in ignore_models:
                if resource.model.lower() == ignore_model.lower():
                    return False

        apps = self.sandbox.get_Apps_resources()
        for app in apps:
            if app.Name == resource.name:
                return False

        return True


class image_struct:
    def __init__(self, path, version):
        self.path = path
        self.version = version

class load_result_struct:
    def __init__(self, resource_name):
        self.run_result = True
        self.resource_name = resource_name
        self.message = ""

