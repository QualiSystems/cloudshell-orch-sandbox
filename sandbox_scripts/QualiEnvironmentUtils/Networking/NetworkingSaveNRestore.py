# coding=utf-8
import csv
import tempfile

import tftpy

from sandbox_scripts.QualiEnvironmentUtils.ConfigFileManager import *
from sandbox_scripts.QualiEnvironmentUtils.ConfigPoolManager import *


class NetworkingSaveRestore(object):
    def __init__(self, sandbox):
        """
        Get the root directory for the config files on the tftp server
        :param SandboxBase sandbox:  The sandbox save & restore will be done in
        """
        self.sandbox = sandbox
        tftp_resource = self.sandbox.get_tftp_resource()
        if tftp_resource is not None:
            self.tftp_address = tftp_resource.address
            self.tftp_port = int(tftp_resource.get_attribute('TFTP Port'))
            self.tftp_server_destination_path = tftp_resource.get_attribute("TFTP Network configs")
            #self.tftp_map_drive = tftp_resource.get_attribute("TFTP Drive")
            if self.tftp_server_destination_path != "":
                self.config_files_root = 'tftp://' + tftp_resource.address + "/" + self.tftp_server_destination_path
            else:
                self.sandbox.report_error("Failed to find the network's tftp path", raise_error=True,
                                          write_to_output_window=False)
        else:
            self.sandbox.report_error("Failed to find a tftp resource in the sandbox", raise_error=True,
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
            root_path = self.config_files_root + '/' + config_stage + '/' + self.sandbox.Blueprint_name + '/'
        elif config_stage.lower() == 'base':
            root_path = self.config_files_root + '/' + config_stage + '/'
        if config_set_name != '':
            root_path = root_path + config_set_name + '/'

        #root_path = root_path + 'configs/'
        images_path_dict = self._get_images_path_dict(root_path,write_to_output=True)

        root_resources = self.sandbox.get_root_resources()
        """:type : list[ResourceBase]"""
        for resource in root_resources:
            # Check if needs to load the config to the device
            load_config_to_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
            if load_config_to_device:
                health_check_result = resource.is_healthy()
                if health_check_result == "":
                    try:
                        if len(images_path_dict)>0:
                            image_key = resource.alias + '_' + resource.model
                            resource_image_path = images_path_dict[image_key]
                            if resource_image_path != '':
                                self.sandbox.report_info(
                                    'Loading firmware for device: ' + resource.name + ' from:' + resource_image_path, write_to_output)
                                resource.load_firmware(resource_image_path)
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
                    self.sandbox.report_info(resource.name +
                                             ' did not pass health check. Configuration will not be loaded to the device.',
                                             write_to_output_window=True)
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
        tftp_client = tftpy.TftpClient(self.tftp_address, self.tftp_port)
        # Check if there is a file pointing to firmware images files in the config directory
        try:
            firmware_data_file = root_path + 'FirmwareData.csv'
            tmp_firmware_file = tempfile.NamedTemporaryFile(delete=True)
            tftp_client.download(firmware_data_file, tmp_firmware_file.name)

            # Create a dictionary for each resource its image file location
            with open(tmp_firmware_file.name) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    images_path_dict(row['Device'], row['Path'])
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
        tftp_client = tftpy.TftpClient(self.tftp_address, self.tftp_port)
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
        tftp_template_config_path = tftp_template_config_path.replace('tftp://' + self.tftp_address + "/", '')
        tftp_template_config_path = str(unicode(tftp_template_config_path.replace(' ', '_')))
        try:
            tftp_client.download(tftp_template_config_path, tmp_template_config_file.name)
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
            tmp_template_config_file.delete()
            short_Reservation_id = self.sandbox.id[len(self.sandbox.id)-4:len(self.sandbox.id)]
            concrete_file_path = root_path + 'temp/' + short_Reservation_id + '_' + resource.alias + \
                                 '_' + resource.model + '.cfg'
            concrete_file_path = concrete_file_path.replace('tftp://' + self.tftp_address + "/",'')
            concrete_file_path = concrete_file_path.replace(' ', '_')
            # TODO - clean the temp dir on the tftp server
            tftp_client.upload(str(unicode(concrete_file_path)), str(tmp_concrete_config_file.name))
            tmp_concrete_config_file.close()
            tmp_concrete_config_file.delete()
            # Set the path to the new concrete file
            config_path = concrete_file_path
        # If we got exception - template file does not exist. Close the temp file and try to load
        # configuration from a concrete config file
        except :#tftpy.TftpException:
            if os.path.isfile(tftp_template_config_path):
                tmp_template_config_file.close()
                tmp_template_config_file.delete()

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
        root_resources = self.sandbox.get_root_resources()

     #   new_config_path = self.tftp_map_drive + '/Snapshots/' + snapshot_name

     #   windows_server_path = self.tftp_server_destination_path.replace("/","\\")
     #   new_config_path =  "\\\\" + self.tftp_address + "\\" + windows_server_path + "\Snapshots\\" + snapshot_name
        #config_path = 'Z:/Configs/snapshots/Snap12'

        #config_path = self.config_files_root + '/snapshots/' + self.sandbox.Blueprint_name

        #if not os.path.exists(new_config_path):
        #    os.makedirs(new_config_path)

        config_path = self.config_files_root + '/Snapshots/' + snapshot_name

        # TODO: check - do I need to create the snapshot folder on the tfp server if it doesn't exist?
        for resource in root_resources:
            save_config_from_device = True
            if ignore_models:
                for ignore_model in ignore_models:
                    if resource.model.lower() == ignore_model.lower():
                        save_config_from_device = False
                        break
            if save_config_from_device:
                try:
                    self.sandbox.report_info(
                        'Saving configuration for device: ' + resource.name + ' to: ' + config_path, write_to_output)
                    resource.save_network_config(self.sandbox.id, config_path, config_type)

                except QualiError as qe:
                    err = "Failed to save configuration for device " + resource.name + ". " + str(qe)
                    self.sandbox.report_error(err, write_to_output_window=write_to_output)
                except:
                    err = "Failed to save configuration for device " + resource.name + \
                          ". Unexpected error: " + str(sys.exc_info()[0])
                    self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # Is this Sandbox originates from a snapshot Blueprint?
    # ----------------------------------
    def is_snapshot(self):
        # check if there is a directory with the Blueprint's name under the snapshots dir
        envDir = self.config_files_root + '/Snapshots/' + self.sandbox.Blueprint_name
        return os.path.isdir(envDir)

    # ----------------------------------
    # Check if need to load configuration to the given device
    # A device should not be in the ignored models list,
    # or should not have a "Disable Load Config" attribute set to True
    # in order to load configuration on it
    # ----------------------------------
    def _is_load_config_to_device(self, resource, ignore_models=None):
        # check if the device is marked for not loading config during
        try:
            disable_load_config = resource.get_attribute("Disable Load Config")
            if disable_load_config:
                return False
        except QualiError:  # if attribute not found then assume load config in enabled
            pass

        if ignore_models:
            for ignore_model in ignore_models:
                if resource.model.lower() == ignore_model.lower():
                    return False

        return True

