# coding=utf-8
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
from abc import ABCMeta
from abc import abstractmethod
import tftpy
import ftplib

class StorageManager(object):
    def __init__(self, sandbox, storage_resource):
        """
        Check if there is an ip pool
        :param SandboxBase sandbox:  The sandbox the config file mgr will work with
        :param ResourceBase storage_resource:  The storage resource in the sandbox
        """
        self.sandbox = sandbox
        self.storage_resource = storage_resource

    def get_client(self):
        if self.storage_resource.model.lower() == 'generic tftp server':
            return TFTPClient(self.sandbox,self.storage_resource)
        elif self.storage_resource.model.lower() == 'generic ftp server':
            return FTPClient(self.sandbox,self.storage_resource)


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


class TFTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        super(TFTPClient,self).__init__(sandbox, storage_resource)
        self.tftp_client = tftpy.TftpClient(self.address, self.port)

    # ----------------------------------
    # ----------------------------------
    def get_configs_root(self):
        if self.configs_root != "":
            return 'tftp://' + self.address + "/" + self.configs_root

    # ----------------------------------
    # ----------------------------------
    def download(self, source, destination):
        """
        Download file from the tftp server
        :param str source:  The path to the file on the tftp server
        :param str destination:  destination file name
        """
        source = self._remove_header(source)
        self.tftp_client.download(str(unicode(source)), str(unicode(destination)))

    # ----------------------------------
    # ----------------------------------
    def upload(self, destination, source):
        """
        Upload file to the tftp server
        :param str source:  The path to the file on the tftp server
        :param str destination:  destination file name
        """
        destination = self._remove_header(destination)
        self.tftp_client.upload(str(unicode(destination)), str(source))

    # ----------------------------------
    # ----------------------------------
    def dir_exist(self, dir_name):
        return os.path.isdir(dir_name)

    # ----------------------------------
    # ----------------------------------
    def _remove_header(self, path):
        path = path.replace('tftp://' + self.address + "/", '')
        path = path.replace(' ', '_')
        return path


class FTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        super(FTPClient,self).__init__(sandbox, storage_resource)
        self.username = storage_resource.get_attribute("Storage username")
        self.password = storage_resource.get_attribute("Storage password")
        #self.ftp = ftplib.FTP(self.address, self.username, self.password)
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.address,self.port)
        self.ftp.login(self.username,self.password)

    # ----------------------------------
    # ----------------------------------
    def __exit__(self, exc_type, exc_value, traceback):
        self.ftp.quit()

    # ----------------------------------
    # ----------------------------------
    def get_configs_root(self):
        if self.configs_root != "":
            return 'ftp://' + self.username + ':' + self.password + '@' + self.address +\
                                             "/" + self.configs_root

    # ----------------------------------
    # ----------------------------------
    def download(self, source, destination):
        """
        Download file from the ftp server
        :param str source:  The path to the file on the ftp server
        :param str destination:  destination file name
        """
        source = self._remove_header(source)
        self.ftp.retrbinary("RETR " + source ,open(destination, 'wb').write)


    # ----------------------------------
    # ----------------------------------
    def upload(self, destination, source):
        """
        Upload file to the ftp server
        :param str source:  The path to the file on the ftp server
        :param str destination:  destination file name
        """
        file_idx=destination.rfind('/')
        destination_dir = destination[:(file_idx-len(destination))]
        destination_dir = self._remove_header(destination_dir)
        self.ftp.cwd(destination_dir)
        destination_file =destination[file_idx+1:]
        myfile = open(source, 'r')
        self.ftp.storlines('STOR ' + destination_file, myfile)
        myfile.close()


    # ----------------------------------
    # ----------------------------------
    def dir_exist(self, dir_name):
        try:
            dir_name = self._remove_header(dir_name)
            self.ftp.cwd(dir_name)
            return True
        except:
            return False

    # ----------------------------------
    # ----------------------------------
    def _remove_header(self, path):
        path = path.replace('ftp://' + self.username + ':' + self.password + '@' + self.address +"/",'')
        path = path.replace(' ', '_')
        return path