# coding=utf-8
import csv
import tempfile
import subprocess


from sandbox_scripts.QualiEnvironmentUtils.ConfigFileManager import *
from sandbox_scripts.QualiEnvironmentUtils.ConfigPoolManager import *
from sandbox_scripts.QualiEnvironmentUtils.StorageManager import StorageManager


class NetworkingSaveRestore(object):
    def __init__(self, sandbox):
        """
        Get the root directory for the config files on the storage server
        :param SandboxBase sandbox:  The sandbox save & restore will be done in
        """
        self.sandbox = sandbox
        storage_server_resource = self.sandbox.get_storage_server_resource()
        if storage_server_resource is not None:
            self.storage_client = StorageManager(sandbox,storage_server_resource).get_client()
            self.config_files_root = self.storage_client.get_configs_root()
        else:
            self.sandbox.report_error("Failed to find a storage server resource (e.g. tftp) in the sandbox. ", raise_error=True,
                                      write_to_output_window=False)

    # ----------------------------------
    # load_network_config(ResourceName,config_type, RestoreMethod=Override)
    # ResourceName - The name of the resource we would like to load the config onto
    # ConfigPath – the path to the configuration file, including the configuration file name.
    # The path should include the protocol type. This input is mandatory.
    # the configuration file name doesnt include “StartUp” or “Running”
    # Restore Method – optional, if empty the default value will be taken.
    # Possible values – Append or Override
    # Default value – Override
    # The command should fail if the configuration file name doesnt include “StartUp” or “Running”
    # config_stage - Gold, Base, Snapshot...
    # A path to a config file will look like ROOT_DIR/CONFIG_STAGE/BlueprintX/resourceY_ModelZ.cfg
    # e.g. tftp://configs/Gold/Large_Office/svl290-gg07-sw1_c3850.cfg
    # Base config is an exception. The blueprint's name is not in the path
    # e.g. tftp://configs/Base/svl290-gg07-sw1_c3850.cfg
    # ----------------------------------
    def load_config(self, config_stage, config_type, restore_method="Override", config_set_name='', ignore_models=None,
                    write_to_output=True):
        """
        Load the configuration from config files on the Blueprint's devices
        :param str config_stage:  The stage of the config e.g Gold, Base
        :param str config_type:  Possible values - StartUp or Running
        :param str restore_method: Optional. Restore method. Can be Append or Override
        :param str config_set_name: Optional. If we have multiple configuration sets for the same blueprint.
        the nam of the set selected by the user
        :param list[str] ignore_models: Optional. Models that should be ignored and not load config on the device
        :param bool write_to_output: Optional. should messages be sent to the command output.
        """
        root_path = ''
        if config_stage.lower() == 'gold' or config_stage.lower() == 'snapshot':
            root_path = self.config_files_root + '/' + config_stage + '/' + self.sandbox.Blueprint_name.strip() + '/'
        elif config_stage.lower() == 'base':
            root_path = self.config_files_root + '/' + config_stage + '/'
        if config_set_name != '':
            root_path = root_path + config_set_name.strip() + '/'

        root_path = root_path.replace(' ', '_')


        #root_path = root_path + 'configs/'
        images_path_dict = self._get_images_path_dict(root_path,write_to_output=True)

        root_resources = self.sandbox.get_root_resources()
        """:type : list[ResourceBase]"""
        for resource in root_resources:
            # Check if needs to load the config to the device
            load_config_to_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
            if load_config_to_device:
                health_check_result = resource.health_check(self.sandbox.id)
                if health_check_result == "":
                    try:
                        #TBD: check what the FW version is and only load firmware if it's different from what
                        # currently is there
                        if len(images_path_dict)>0:
                            image_key = (resource.alias + '_' + resource.model).replace(' ', '_')
                            resource_image_path = images_path_dict[image_key]
                            if resource_image_path != '':
                                self.sandbox.report_info(
                                    'Loading firmware for device: ' + resource.name + ' from:' + resource_image_path, write_to_output)
                                resource.load_firmware(self.sandbox.id,resource_image_path)
                        config_path = self._get_concrete_config_file_path(root_path, resource, write_to_output=True)
                        self.sandbox.report_info(
                            'Loading configuration for device: ' + resource.name + ' from:' + config_path, write_to_output)

                        resource.load_network_config(self.sandbox.id, config_path, config_type, restore_method)
                        self.sandbox.api_session.SetResourceLiveStatus(resource.name, 'Online')
                    except QualiError as qe:
                        err = "Failed to load configuration for device " + resource.name + ". " + str(qe)
                        self.sandbox.report_error(err, write_to_output_window=write_to_output, raise_error=False)
                        self.sandbox.api_session.SetResourceLiveStatus(resource.name, 'Error')
                    except :
                        err = "Failed to load configuration for device " + resource.name + \
                              ". Unexpected error: " + traceback.format_exc()
                        self.sandbox.report_error(err, write_to_output_window=write_to_output, raise_error=False)
                        self.sandbox.api_session.SetResourceLiveStatus(resource.name, 'Error')
                else:
                    #self.sandbox.api_session.SetResourceLiveStatus(resource.name, 'Error')
                    self.sandbox.report_error(resource.name +
                                             ' did not pass health check. Configuration will not be loaded to the device.',
                                             raise_error=False, write_to_output_window=True)
                    self.sandbox.report_info(resource.name +
                                             ' health check error is: ' + health_check_result,
                                             write_to_output_window=False)

    # ----------------------------------
    # ----------------------------------
    def _get_images_path_dict(self, root_path, write_to_output=True):
        """
        Check if there is a need to load firmware on the devices
        If a file named FirmwareData.csv is located under the configs directory -
        Read it to get the data on the firmware files location and create a dictionary: resource-its image file location
        :param str root_path:  The root dir on the tftp where the config files reside
        :rtype: dict
        """
        images_path_dict = dict()
        tmp_firmware_file = tempfile.NamedTemporaryFile(delete=False)

        # Check if there is a file pointing to firmware images files in the config directory
        try:
            firmware_data_file = root_path + 'FirmwareData.csv'
            self.storage_client.download(firmware_data_file, tmp_firmware_file.name)
            # Create a dictionary for each resource its image file location
            with open(tmp_firmware_file.name) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    images_path_dict[row['Device']] = row['Path']
        except:
            if os.path.isfile(tmp_firmware_file.name):
                tmp_firmware_file.close()
        return images_path_dict

    # ----------------------------------
    # ----------------------------------
    def _get_concrete_config_file_path(self, root_path, resource, write_to_output=True):
        """
        Get the path to a concrete config file. If there is only a template for the config file,
        create a temp concrete config file, and send its path
        :param str root_path:  The root dir on the tftp where the config files reside
        :param ResourceBase resource:  The resource the file will be created for
        :rtype: str
        """
        config_file_mgr = ConfigFileManager(self.sandbox)
        config_set_pool_data = dict()
        # If there is a pool resource, get the pool data
        config_set_pool_resource = self.sandbox.get_config_set_pool_resource()
        if config_set_pool_resource is not None:
            config_set_pool_manager = ConfigPoolManager(sandbox=self.sandbox, pool_resource=config_set_pool_resource)
            config_set_pool_data = config_set_pool_manager.pool_data_to_dict()

        config_path = root_path + resource.alias + '_' + resource.model + '.cfg'

        # Look for a template config file
        tmp_template_config_file = tempfile.NamedTemporaryFile(delete=False)
        tftp_template_config_path = root_path + resource.alias + '_' + resource.model + '.tm'
        try:
            self.storage_client.download(tftp_template_config_path,tmp_template_config_file.name)
            with open(tmp_template_config_file.name, 'r') as content_file:
                tmp_template_config_file_data = content_file.read()
            concrete_config_data = config_file_mgr.create_concrete_config_from_template(
                tmp_template_config_file_data, config_set_pool_data, resource)
            tmp_concrete_config_file = tempfile.NamedTemporaryFile(delete=False)
            tf = file(tmp_concrete_config_file.name, 'wb+')
            tf.write(concrete_config_data)
            tf.flush()
            tf.close()
            tmp_template_config_file.close()
            os.unlink(tmp_template_config_file.name)
            short_Reservation_id = self.sandbox.id[len(self.sandbox.id)-4:len(self.sandbox.id)]
            concrete_file_path = root_path + 'temp/' + short_Reservation_id + '_' + resource.alias + \
                                 '_' + resource.model + '.cfg'
            # TODO - clean the temp dir on the tftp server
            self.storage_client.upload(concrete_file_path, tmp_concrete_config_file.name)
            tmp_concrete_config_file.close()
            os.unlink(tmp_concrete_config_file.name)
            # Set the path to the new concrete file
            config_path = concrete_file_path
        # If we got exception - template file does not exist. Close the temp file and try to load
        # configuration from a concrete config file
        except :
            if os.path.isfile(tftp_template_config_path):
                tmp_template_config_file.close()
                os.unlink(tmp_template_config_file.name)

        config_path = config_path.replace(' ','_')

        return config_path

    # ----------------------------------
    # ----------------------------------
    def save_config(self, snapshot_name, config_type, ignore_models=None, write_to_output=True):
        """
        Load the configuration from the devices to the tftp
        :param str snapshot_name:  The name of the snapshot
        :param str config_type:  StartUp or Running
        :param list[str] ignore_models: Optional. Models that should be ignored and not load config on the device
        :param bool write_to_output: Optional. should messages be sent to the command output.
        """
        env_dir = self.config_files_root + '/Snapshots/' + snapshot_name
        self.storage_client.save_config(config_type,env_dir, ignore_models=None, write_to_output=True)


    # ----------------------------------
    # Is this Sandbox originates from a snapshot Blueprint?
    # ----------------------------------
    def is_snapshot(self):
        # check if there is a directory with the Blueprint's name under the snapshots dir
        env_dir = self.config_files_root + '/Snapshots/' + self.sandbox.Blueprint_name
        env_dir = env_dir.replace(' ', '_')
        return self.storage_client.dir_exist(env_dir)

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

        return True

