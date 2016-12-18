# coding=utf-8
import csv
import tempfile
import json
import subprocess
from multiprocessing.pool import ThreadPool
from threading import Lock

from sandbox_scripts.QualiEnvironmentUtils.ConfigFileManager import *
from sandbox_scripts.QualiEnvironmentUtils.ConfigPoolManager import *
from sandbox_scripts.QualiEnvironmentUtils.StorageManager import StorageManager


class image_struct:
    def __init__(self, path, version):
        self.path = path
        self.version = version

class load_result_struct:
    def __init__(self, resource_name):
        self.run_result = True
        self.resource_name = resource_name
        self.message = ""

class NetworkingSaveRestore(object):
    def __init__(self, sandbox):
        """
        Get the root directory for the config files on the storage server
        :param SandboxBase sandbox:  The sandbox save & restore will be done in
        """
        self.sandbox = sandbox
        storage_server_resource = self.sandbox.get_storage_server_resource()
        self.storage_client = None
        if storage_server_resource is not None:
            self.storage_client = StorageManager(sandbox,storage_server_resource).get_client()
            self.config_files_root = self.storage_client.get_configs_root()
        else:
            if self.is_resources_in_reservation_to_restore(ignore_models = None):
                self.sandbox.report_error("Failed to find a storage server resource (e.g. tftp) in the sandbox. ", raise_error=True,
                                      write_to_output_window=True)

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
                    write_to_output=True, remove_temp_files = False):
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
        if config_stage.lower() == 'gold' or config_stage.lower() == 'snapshots':
            root_path = self.config_files_root + '/' + config_stage + '/' + self.sandbox.Blueprint_name.strip() + '/'
        elif config_stage.lower() == 'base':
            root_path = self.config_files_root + '/' + config_stage + '/'
        if config_set_name != '':
            root_path = root_path + config_set_name.strip() + '/'

        root_path = root_path.replace(' ', '_')


        #root_path = root_path + 'configs/'
        images_path_dict = self._get_images_path_dict(root_path,write_to_output=True)
        self.sandbox.report_info(
            "Loading image and configuration on the devices. This action may take some time",write_to_output_window=True)
        root_resources = self.sandbox.get_root_resources()
        """:type : list[ResourceBase]"""
        pool = ThreadPool(len(root_resources))
        lock = Lock()
        async_results = [pool.apply_async(self._run_asynch_load,
                                          (resource, images_path_dict, root_path, ignore_models,config_stage, lock))
                         for resource in root_resources]

        pool.close()
        pool.join()
        for async_result in async_results:
            res = async_result.get()
            """:type : load_result_struct"""
            if not res.run_result:
                err = "Failed to load configuration on device " + res.resource_name
                self.sandbox.report_error(err, write_to_output_window=write_to_output, raise_error=False)
                self.sandbox.report_error(res.message, raise_error=False)
                self.sandbox.api_session.SetResourceLiveStatus(res.resource_name, 'Error')
            elif res.message != '':
                self.sandbox.report_info(res.resource_name + "\n" + res.message)
        if remove_temp_files:
            self._remove_temp_config_files()


    # ----------------------------------
    # ----------------------------------
    def _remove_temp_config_files(self):
        root_resources = self.sandbox.get_root_resources()
        """:type : list[ResourceBase]"""
        for resource in root_resources:
            try:
                if resource.attribute_exist('Config file path'):
                    tmp_config_file_path = resource.get_attribute('Config file path')
                    if tmp_config_file_path != '':
                        self.storage_client.delete(tmp_config_file_path)
            except QualiError as qe:
                self.sandbox.report_info("Failed to delete temp config file " + tmp_config_file_path +
                                         "Error is: " + str(qe))
    # ----------------------------------
    # ----------------------------------
    def _run_asynch_load(self,resource, images_path_dict,root_path, ignore_models,config_stage, lock):
        message = ""
        #run_status = True
        saved_artifact_info = None
        load_result = load_result_struct(resource.name)
        # Check if needs to load the config to the device
        load_config_to_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
        if load_config_to_device:
            #if we are in teardown the vm is already down - no need to do anything
            if resource.is_app() and config_stage.lower() == 'base':
                return

            health_check_result = resource.health_check(self.sandbox.id)
            if health_check_result == "":
                try:
                    config_path = ''
                    with lock:
                        config_path = self._get_concrete_config_file_path(root_path, resource, config_stage, write_to_output=True)
                    resource.set_attribute_value('Config file path', config_path)
                    #TODO - Snapshots currently only restore configuration. We need to restore firmware as well
                    if config_stage.lower() == 'snapshots':
                        if resource.has_command('orchestration_restore'):
                            dest_name = resource.name + '_' + resource.model +'_artifact.txt'
                            dest_name = dest_name.replace(' ','-')
                            saved_artifact_info = self.storage_client.download_artifact_info(config_path,dest_name,write_to_output=True)
                            resource.orchestration_restore(self.sandbox.id,config_path,saved_artifact_info)
                        else:
                            resource.load_network_config(self.sandbox.id, config_path, 'running', 'override')
                    else:
                        if len(images_path_dict) > 0:
                            # check what the FW version is and only load firmware if it's different from what
                            # currently is on the device
                            image_key = (resource.alias + '_' + resource.model).replace(' ', '_')
                            version = resource.get_version(self.sandbox.id)
                            try:
                                dict_img_version = images_path_dict[image_key].version
                            except:
                                image_key = resource.model.replace(' ', '_')
                                dict_img_version = images_path_dict[image_key].version
                            # same image version - Only load config (running override)
                            if dict_img_version.lower() == version.lower():
                                message += "\nLoading configuration for device: " + resource.name + " from:" + config_path
                                resource.load_network_config(self.sandbox.id, config_path, 'running', 'override')
                            # Different image - Load config to the startup and load the image
                            else:
                                message += "\nLoading configuration for device: " + resource.name + " from:" + config_path
                                resource.load_network_config(self.sandbox.id, config_path, 'startup', 'override')

                                resource_image_path = images_path_dict[image_key].path
                                if resource_image_path != '':
                                    message += "\nLoading firmware for device: " + resource.name + " from:" + \
                                               resource_image_path
                                    resource.load_firmware(self.sandbox.id, resource_image_path)
                        else:
                            message += "\nLoading configuration for device: " + resource.name + " from:" + config_path
                            resource.load_network_config(self.sandbox.id, config_path, 'running', 'override')

                    health_check_result = resource.health_check(self.sandbox.id)
                    if health_check_result != '':
                        raise QualiError(self.sandbox.id, resource.name +
                                         " did not pass health check after loading configuration")

                except QualiError as qe:
                    load_result.run_result = False
                    err = "\nFailed to load configuration for device " + resource.name + ". " + str(qe)
                    message += err
                except Exception as ex:
                    load_result.run_result = False
                    err = "\nFailed to load configuration for device " + resource.name + \
                          ". Unexpected error: " + str(ex)
                    message += err
            else:
                load_result.run_result = False
                err = resource.name + " did not pass health check. Configuration will not be loaded to the device.\n" + \
                        "Health check error is: " + health_check_result
                message +=  err
        load_result.message = message
        return load_result

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
                    image_data = image_struct(row['Path'],row['Version'])
                    images_path_dict[row['Device']] = image_data
        except:
            if os.path.isfile(tmp_firmware_file.name):
                tmp_firmware_file.close()
        return images_path_dict

    # ----------------------------------
    # ----------------------------------
    def _get_concrete_config_file_path(self, root_path, resource, config_stage, write_to_output=False):
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
        if config_stage == 'snapshots':
            config_path = root_path + resource.name + '_' + resource.model + '.cfg'
        else:
            config_path = root_path + resource.alias + '_' + resource.model + '.cfg'
        # Look for a template config file
        tmp_template_config_file = tempfile.NamedTemporaryFile(delete=False)
        tftp_template_config_path = root_path + resource.alias + '_' + resource.model + '.tm'
        #try:
        #look for a concrete config file
        try:
            self.storage_client.download(config_path, tmp_template_config_file.name)
            tmp_template_config_file.close()
            os.unlink(tmp_template_config_file.name)
        #if no concrete file, look for a template file
        except:
            try:
                self.storage_client.download(tftp_template_config_path,tmp_template_config_file.name)
            except:
                #look for a generic config file for the model
                tftp_template_config_path = root_path + resource.model + '.tm'
                self.storage_client.download(tftp_template_config_path, tmp_template_config_file.name)
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
            concrete_file_path = concrete_file_path.replace(' ', '_')
            # TODO - clean the temp dir on the tftp server
            self.storage_client.upload(concrete_file_path, tmp_concrete_config_file.name)
            tmp_concrete_config_file.close()
            os.unlink(tmp_concrete_config_file.name)
            # Set the path to the new concrete file
            config_path = concrete_file_path

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

        try:
            env_dir = self.config_files_root + '/Snapshots/' + snapshot_name.strip()
            if not self.storage_client.dir_exist(env_dir):
                self.storage_client.create_dir(env_dir, write_to_output=True)
        except QualiError as e:
            self.sandbox.report_error("Save snapshot failed. " + str(e),
                                      write_to_output_window=write_to_output,raise_error=True)
        '''Call To Save command in resource'''
        root_resources = self.sandbox.get_root_resources()
        for resource in root_resources:
            save_config_for_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
            if save_config_for_device:
                    try:
                        self.sandbox.report_info(
                                'Saving configuration for device: ' + resource.name, write_to_output)
                        if resource.has_command('orchestration_save'):
                            config_path = env_dir.replace('\\','/')
                            saved_artifact_info= resource.orchestration_save(self.sandbox.id, config_path, config_type)
                            if saved_artifact_info != "":
                                dest_name = resource.name + '_' + resource.model +'_artifact.txt'
                                dest_name = dest_name.replace(' ','-')
                                self.storage_client.save_artifact_info(saved_artifact_info,config_path,dest_name,write_to_output=True)
                        else:
                            file_name = resource.save_network_config(self.sandbox.id, env_dir, config_type)
                            #rename file on the storage server
                            file_path = env_dir + '/' + file_name
                            to_name = resource.name + '_' + resource.model + '.cfg'
                            self.storage_client.rename_file(file_path, to_name)

                    except QualiError as qe:
                        err = "Failed to save configuration for device " + resource.name + ". " + str(qe)
                        self.sandbox.report_error(err, write_to_output_window=write_to_output,raise_error=False)
                    except Exception as e:
                        err = "Failed to save configuration for device " + resource.name + \
                              ". Unexpected error: " + str(e)
                        self.sandbox.report_error(err, write_to_output_window=write_to_output,raise_error=False)


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

        apps = self.sandbox.get_Apps_resources()
        for app in apps:
            if app.Name == resource.name:
                return False

        return True

    # ----------------------------------
    #Are there devices in the reservation that need to be restored
    # ----------------------------------
    def is_resources_in_reservation_to_restore(self,ignore_models):

        root_resources = self.sandbox.get_root_resources()

        if not root_resources or (len(root_resources) == 1 and not root_resources[0].name):
            self.sandbox.report_info(
                        'No resources found in reservation '+ self.sandbox.id , write_to_output_window=False)
            return False

        for resource in root_resources:
            # Check if needs to load configuration to the device
            if self._is_load_config_to_device(resource, ignore_models=ignore_models):
                return True

        return False

    # ----------------------------------
    # ----------------------------------
    def get_storage_client(self):
        return self.storage_client