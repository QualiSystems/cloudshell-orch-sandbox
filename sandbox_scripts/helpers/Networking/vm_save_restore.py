from sandbox_scripts.helpers.Networking.base_save_restore import *
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
from multiprocessing.pool import ThreadPool
from threading import Lock


class VMsSaveRestore(BaseSaveRestore):
    def __init__(self, sandbox):
        super(VMsSaveRestore,self).__init__(sandbox)


    # ----------------------------------
    # ----------------------------------
    def load_config(self, config_stage, config_set_name='', ignore_models=None,
                    write_to_output=True, in_teardown_mode = False):
        """
        Load the configuration from config files on the Blueprint's devices
        :param str config_stage:  The stage of the config e.g Gold, Base
        :param str config_set_name: Optional. If we have multiple configuration sets for the same blueprint.
        the nam of the set selected by the user
        :param list[str] ignore_models: Optional. Models that should be ignored and not load config on the device
        :param bool write_to_output: Optional. should messages be sent to the command output.
        :param bool in_teardown_mode: Optional. is in teardown mode.
        """

        root_path = ''
        if config_stage.lower() == 'gold' or config_stage.lower() == 'snapshots':
            root_path = self.config_files_root + '/' + config_stage + '/' + self.sandbox.Blueprint_name.strip() + '/'
        elif config_stage.lower() == 'base':
            root_path = self.config_files_root + '/' + config_stage + '/'
        if config_set_name != '':
            root_path = root_path + config_set_name.strip() + '/'

        root_path = root_path.replace(' ', '_')

        self.sandbox.report_info(
            "Loading image on the devices. This action may take some time",write_to_output_window=True)
        root_resources = self.sandbox.get_root_vm_resources()
        """:type : list[ResourceBase]"""
        pool = ThreadPool(len(root_resources))
        async_results = [pool.apply_async(self._run_asynch_load,
                                          (resource, root_path, ignore_models, in_teardown_mode))
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

    # ----------------------------------
    # ----------------------------------
    def _run_asynch_load(self, resource, root_path, ignore_models, in_teardown_mode):

        #if we are in teardown the vm is either going to be deleted or will be restored to default
        # snapshot in the setup - no need to do anything
        #TODO: restore to base config in teardown if there wasn't a snapshot in this reservation, only for static vms
        #(to prevent any issues later in setup)
        if in_teardown_mode:
            return
        message = ""

        saved_artifact_info = None
        load_result = load_result_struct(resource.name)
        # Check if needs to load the config to the device
        load_config_to_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
        if load_config_to_device:
            health_check_result = resource.health_check(self.sandbox.id)
            if health_check_result == "":
                try:
                    if resource.has_command('orchestration_restore'):
                        dest_name = resource.name + '_' + resource.model +'_artifact.txt'
                        dest_name = dest_name.replace(' ','-')
                        saved_artifact_info = self.storage_mgr.download_artifact_info(root_path, dest_name)
                        resource.orchestration_restore(self.sandbox.id,None,saved_artifact_info)

                    health_check_result = resource.health_check(self.sandbox.id)
                    if health_check_result != '':
                        raise QualiError(self.sandbox.id, resource.name +
                                         " did not pass health check after restoring snapshot")

                except QualiError as qe:
                    load_result.run_result = False
                    err = "\nFailed to restore snapshot on " + resource.name + ". " + str(qe)
                    message += err
                except Exception as ex:
                    load_result.run_result = False
                    err = "\nFailed to restore snapshot on " + resource.name + \
                          ". Unexpected error: " + str(ex)
                    message += err
            else:
                load_result.run_result = False
                err = resource.name + " did not pass health check. Snapshot will not be restored.\n" + \
                        "Health check error is: " + health_check_result
                message +=  err
        load_result.message = message
        return load_result


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

        env_dir = ""
        try:
            env_dir = self.config_files_root + '/Snapshots/' + snapshot_name.strip()
            if not self.storage_mgr.dir_exist(env_dir):
                self.storage_mgr.create_dir(env_dir, write_to_output=True)
        except QualiError as e:
            self.sandbox.report_error("Save snapshot failed. " + str(e),
                                      write_to_output_window=write_to_output,raise_error=True)

        root_resources = self.sandbox.get_root_vm_resources()
        """:type : list[ResourceBase]"""
        pool = ThreadPool(len(root_resources))
        lock = Lock()
        async_results = [pool.apply_async(self._run_asynch_save,
                                          (resource, env_dir, config_type, lock, ignore_models))
                         for resource in root_resources]

        pool.close()
        pool.join()
        for async_result in async_results:
            res = async_result.get()
            """:type : load_result_struct"""
            if not res.run_result:
                err = "Failed to save configuration on device " + res.resource_name
                self.sandbox.report_error(err, write_to_output_window=write_to_output, raise_error=False)
                self.sandbox.report_error(res.message, raise_error=False)

            elif res.message != '':
                self.sandbox.report_info(res.resource_name + "\n" + res.message)

    # ----------------------------------
    # ----------------------------------
    def _run_asynch_save(self, resource, snapshot_dir, config_type, lock, ignore_models=None):
        message = ""
        save_result = load_result_struct(resource.name)

        with lock:
            save_config_for_device = self._is_load_config_to_device(resource, ignore_models=ignore_models)
        if save_config_for_device:
            try:
                message +='\nSaving configuration for device: ' + resource.name
                if resource.has_command('orchestration_save'):
                    config_path = snapshot_dir.replace('\\', '/')
                    saved_artifact_info= resource.orchestration_save(self.sandbox.id, config_path, config_type)
                    if saved_artifact_info != "":
                        dest_name = resource.name + '_' + resource.model +'_artifact.txt'
                        dest_name = dest_name.replace(' ','-')
                        with lock:
                            self.storage_mgr.save_artifact_info(saved_artifact_info, config_path, dest_name, write_to_output=False)
                else:
                    file_name = resource.save_network_config(self.sandbox.id, snapshot_dir, config_type)
                    #rename file on the storage server
                    file_path = snapshot_dir + '/' + file_name
                    to_name = resource.name + '_' + resource.model + '.cfg'
                    with lock:
                        self.storage_mgr.rename_file(file_path, to_name)

            except QualiError as qe:
                save_result.run_result = False
                err = "\nFailed to save snapshot for " + resource.name + ". " + str(qe)
                message += err
            except Exception as ex:
                save_result.run_result = False
                err = "\nFailed to save snapshot for " + resource.name + \
                      ". Unexpected error: " + str(ex)
                message += err

        save_result.message = message
        return save_result




    # ----------------------------------
    # delete file name on storage
    # ----------------------------------
    def delete_src_file(self,fileName):

        env_dir = self.config_files_root + '/Snapshots/' + fileName
        env_dir = env_dir.replace(' ', '_')
        self.storage_mgr.delete(env_dir)



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
    def _get_concrete_config_file_path(self, root_path, resource, config_stage, write_to_output=False):
        """
        Get the path to a concrete config file. If there is only a template for the config file,
        create a temp concrete config file, and send its path
        :param str root_path:  The root dir on the tftp where the config files reside
        :param ResourceBase resource:  The resource the file will be created for
        :rtype: str
        """

        config_file_mgr = ConfigFileManager(self.sandbox)
        #TODO - set the pool dictionary only once during the init of the class
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
        config_path = config_path.replace(' ', '_')
        # Look for a template config file
        tmp_template_config_file = tempfile.NamedTemporaryFile(delete=False)
        tftp_template_config_path = root_path + resource.alias + '_' + resource.model + '.tm'
        tftp_template_config_path = tftp_template_config_path.replace(' ', '_')
        #try:
        #look for a concrete config file
        try:
            self.storage_mgr.download(config_path, tmp_template_config_file.name)
            tmp_template_config_file.close()
            os.unlink(tmp_template_config_file.name)
        #if no concrete file, look for a template file
        except:
            try:
                self.storage_mgr.download(tftp_template_config_path, tmp_template_config_file.name)
            except:
                #look for a generic config file for the model
                tftp_template_config_path = root_path + resource.model + '.tm'
                tftp_template_config_path = tftp_template_config_path.replace(' ', '_')
                self.storage_mgr.download(tftp_template_config_path, tmp_template_config_file.name)
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
            self.storage_mgr.upload(concrete_file_path, tmp_concrete_config_file.name)
            tmp_concrete_config_file.close()
            os.unlink(tmp_concrete_config_file.name)
            # Set the path to the new concrete file
            config_path = concrete_file_path

        return config_path


    # ----------------------------------
    # delete file name on storage
    # ----------------------------------
    def delete_src_file(self,fileName):

        env_dir = self.config_files_root + '/Snapshots/' + fileName
        env_dir = env_dir.replace(' ', '_')
        self.storage_mgr.delete(env_dir)

