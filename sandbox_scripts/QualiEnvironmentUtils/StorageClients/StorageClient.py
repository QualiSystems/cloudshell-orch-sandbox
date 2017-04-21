# coding=utf-8
from abc import ABCMeta
from abc import abstractmethod

class StorageClient(object):
    __metaclass__ = ABCMeta

    def __init__(self, sandbox, storage_resource):
        self.sandbox = sandbox
        self.address = storage_resource.address
        self.port = int(storage_resource.get_attribute('Storage Port'))
        self.configs_root = storage_resource.get_attribute("Storage Network configs Path")
        #self.tftp_map_drive = storage_server_resource.get_attribute("TFTP Drive")
        if self.configs_root == "":
            self.sandbox.report_error("Failed to find the network's storage server path", raise_error=True,
                                          write_to_output_window=False)
    @abstractmethod
    def get_configs_root(self):
       raise NotImplementedError('subclasses must override get_configs_root()!')

    @abstractmethod
    def download(self, source, destination):
       raise NotImplementedError('subclasses must override download()!')

    @abstractmethod
    def upload(self, destination, source):
        raise NotImplementedError('subclasses must override upload()!')

    @abstractmethod
    def dir_exist(self, dir_name):
        raise NotImplementedError('subclasses must override dir_exist()!')


    @abstractmethod
    def _remove_header(self, path):
        raise NotImplementedError('subclasses must override _remove_header()!')

    @abstractmethod
    def create_dir(self,env_dir, write_to_output=True):
        raise NotImplementedError('subclasses must override create_dir()!')

    @abstractmethod
    def rename_file(self, file_path, new_name):
        raise NotImplementedError('subclasses must override rename_file()!')

    @abstractmethod
    def delete(self, file_path):
        raise NotImplementedError('subclasses must override delete()!')
    @abstractmethod
    def create_src_file_on_storage(self,win_path,write_to_output=True):
        raise NotImplementedError('subclasses must override create_src_file_on_tftp()!')
    @abstractmethod
    def save_artifact_info(self,saved_artifact_info,env_dir,dest_name,write_to_output=True):
        raise NotImplementedError('subclasses must override save_artifact_info()!')
    @abstractmethod
    def download_artifact_info(self,root_folder,dest_name,write_to_output=True):
        raise NotImplementedError('subclasses must override download_artifact_info()!')
