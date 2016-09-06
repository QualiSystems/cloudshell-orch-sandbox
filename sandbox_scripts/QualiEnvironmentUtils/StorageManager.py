# coding=utf-8
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
from abc import ABCMeta
from abc import abstractmethod
import tftpy
import ftplib
import subprocess

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
        self.username = storage_resource.get_attribute("Storage username")
        self.password = storage_resource.get_attribute("Storage password")
        self.tftp_psexe = storage_resource.get_attribute('TFTP psexec')
        self.tftp_root_dir = storage_resource.get_attribute('TFTP Root')

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


        try:
            dir_name = self._remove_header(dir_name)

            new_config_path = self.tftp_root_dir +'\\'+ dir_name
            new_config_path = new_config_path.replace('/', '\\')
            #new_config_path = self.tftp_root_dir + "\\" + win_path + "\Snapshots\\"

            command_array = ['cmd', '/c', 'dir', new_config_path]
            interactive = True

            self.tftp_psexe = self.tftp_psexe.replace('/', '\\')
            pspath = self.tftp_psexe + '\psexec.exe'
            user = self.username
            password = self.password

            ia = [
                     pspath,
                     '\\\\' + self.address,
                     '/accepteula',
                     '-u',
                     user,
                     '-p',
                     password,
                     '-h'
                 ] + (['-i', '0'] if interactive else []) + command_array

            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)
            print ' psexec result: ' + str(rv).replace('\r\n', '\n')

            list = str(rv).split()
            matching = [s for s in list if self.sandbox.Blueprint_name in s]
            for word in matching:
                if word == self.sandbox.Blueprint_name:
                    return True

        except Exception as e:
            if hasattr(e, 'output'):
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=True)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=True)




                #return os.path.isdir(dir_name)

    # ----------------------------------
    # ----------------------------------
    def _remove_header(self, path):
        path = path.replace('tftp://' + self.address + "/", '')
        path = path.replace(' ', '_')
        return path

    # ----------------------------------
    # ----------------------------------
    def save_config(self, config_type,env_dir, ignore_models=None, write_to_output=True):
        """
        Load the configuration from the devices to the tftp
        :param str snapshot_name:  The name of the snapshot
        :param str config_type:  StartUp or Running
        :param list[str] ignore_models: Optional. Models that should be ignored and not load config on the device
        :param bool write_to_output: Optional. should messages be sent to the command output.
        """

        '''Create directory'''
        try:
            win_path = self._remove_header(env_dir)
            #win_path=self.tftp_server_destination_path.replace('/',"\\")
            new_config_path = self.tftp_root_dir+'\\'+ win_path
            new_config_path = new_config_path.replace('/',"\\")

            self.tftp_psexe = self.tftp_psexe.replace('/','\\')
            pspath = self.tftp_psexe +'\psexec.exe'
            user = self.username
            password = self.password

            command_array = ['cmd', '/c', 'mkdir', new_config_path]

            interactive = True

            ia = [
                     pspath,
                     '\\\\' + self.address,
                     '/accepteula',
                     '-u',
                     user,
                     '-p',
                     password,
                     '-h'
                 ] + (['-i', '0'] if interactive else []) + command_array


            self.sandbox.report_info('Creating new folder: ' +  new_config_path, write_to_output)
            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)
            print ' psexec result: ' + str(rv).replace('\r\n', '\n')

        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=write_to_output)

        '''Call To Save command in resource'''
        config_path =  env_dir.replace('\\','/')

        root_resources = self.sandbox.get_root_resources()
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

    # -----------------------------------
    # -----------------------------------

    def save_config(self, config_type, env_dir, ignore_models=None, write_to_output=True):

        ''''Create dir'''

