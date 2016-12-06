# coding=utf-8
import paramiko

from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
from abc import ABCMeta
from abc import abstractmethod
import tftpy
import ftplib
import subprocess
import json
import tempfile


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
        elif self.storage_resource.model.lower() == 'generic sftp server':
            return SFTPClient(self.sandbox,self.storage_resource)


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

class TFTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        super(TFTPClient,self).__init__(sandbox, storage_resource)
        self.username = storage_resource.get_attribute("Storage username")
        self.password = storage_resource.get_attribute("Storage password")
        self.tftp_psexe = storage_resource.get_attribute('TFTP psexec')
        self.tftp_root_dir = storage_resource.get_attribute('TFTP Root')
        #self.tftp_root_dir = self.configs_root

        self.tftp_client = tftpy.TftpClient(self.address, self.port)

    # ----------------------------------
    # ----------------------------------
    def get_configs_root(self):
        if self.configs_root != "":
            path = 'tftp://' + self.address + "/" + self.configs_root
            return path

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

            head,tail = os.path.split(dir_name)

            new_config_path = self.tftp_root_dir +'\\'+ head
            new_config_path = new_config_path.replace('/', "\\")

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
                     '-h',
                 ] + command_array

            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)
            #print ' psexec result for dir: ' + str(rv).replace('\r\n', '\n')

            list = str(rv).split()
            #print list
            matching = [s for s in list if tail in s]

            for word in matching:

                if word == tail:
                   return True

            return False

        except:
            return False

               #return os.path.isdir(dir_name)

    # ----------------------------------
    # ----------------------------------
    def _remove_header(self, path):
        path = path.replace('tftp://' + self.address + "/", '')
        path = path.replace(' ', '_')
        return path

    # ----------------------------------
    # ----------------------------------
    def create_dir(self,env_dir,write_to_output=True):

        """
        Create new directory on the tftp
        :param env_dir:  The path directory to create

        """
        try:
            win_path = self._remove_header(env_dir)
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

        #   self.sandbox.report_info('Creating new folder: ' +  new_config_path, write_to_output)
            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)
            #print ' psexec result for mkdir: ' + str(rv).replace('\r\n', '\n')

            self.create_src_file_on_tftp(env_dir,write_to_output)

        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------
    def create_src_file_on_tftp(self,win_path,write_to_output=True):
        #creating new file

        #src
        tmp_file = "C:\\tmp.txt"

        #destination
        snapshot_resource_name = "Snapshot_"+self.sandbox.id
        head,tail = os.path.split(win_path)
        path = head + '/' + snapshot_resource_name +".txt"
        path = self.convert_path_to_storage(path)

        try:
            with open(tmp_file, 'w+') as outfile:
                outfile.write("1")

            self.upload(path,tmp_file)
            os.remove(tmp_file)


        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                err = 'create Src file failed '
                self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------
    def save_artifact_info(self,saved_artifact_info,env_dir,dest_name,write_to_output=True):

        tmpfile = 'data.json'

        win_path = self._remove_header(env_dir)

        new_config_path = win_path + '/' + dest_name
        new_config_path = self.convert_path_to_storage(new_config_path)

        try:
            with open(tmpfile, 'w+') as outfile:
                json.dump(saved_artifact_info, outfile)

            self.upload(new_config_path,tmpfile)

            os.remove(tmpfile)
        except:
            err = 'saved artifact info failed '
            self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------
    def download_artifact_info(self,env_dir,dest_name,write_to_output=True):

        tmpfile = 'data.json'

        win_path = self._remove_header(env_dir)
        head, tail = os.path.split(win_path)

        new_config_path = head + '/' + dest_name
        new_config_path = self.convert_path_to_storage(new_config_path)

        try:
            # Reading data back
            with open(tmpfile, 'w+') as outfile:
                self.download(new_config_path,tmpfile)
                data = json.load(outfile)

            os.remove(tmpfile)
            return data

        except QualiError as qe:
            err = "Failed to download artifact configuration for device" + str(qe)
            return None
        except:
            err = 'download artifact info failed '
           # self.sandbox.report_error(err, write_to_output_window=write_to_output)
            return None

    # ----------------------------------
    # ----------------------------------
    def convert_path_to_storage(self,path):
        path = path.replace("\\","/")
        return path


class FTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        super(FTPClient,self).__init__(sandbox, storage_resource)
        try:
            self.username = storage_resource.get_attribute("Storage username")
            self.password = storage_resource.get_attribute("Storage password")
            #self.ftp = ftplib.FTP(self.address, self.username, self.password)
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.address,self.port)
            self.ftp.login(self.username,self.password)
        except Exception as e:
            self.sandbox.report_error("Failed to connect to the FTP server . Error is: " + str(e), raise_error=True)

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
        try:
            source = self._remove_header(source)
            self.ftp.retrbinary("RETR " + source ,open(destination, 'wb').write)
        except Exception as e:
            self.sandbox.report_error("Failed to download file " + source + " to " + destination +
                                      " from  the FTP server. Error is: " + str(e), raise_error=True)


    # ----------------------------------
    # ----------------------------------
    def upload(self, destination, source):
        """
        Upload file to the ftp server
        :param str source:  The path to the file on the ftp server
        :param str destination:  destination file name
        """
        try:
            file_idx=destination.rfind('/')
            destination_dir = destination[:(file_idx-len(destination))]
            destination_dir = self._remove_header(destination_dir)
            self.ftp.cwd(destination_dir)
            destination_file =destination[file_idx+1:]
            myfile = open(source, 'r')
            self.ftp.storlines('STOR ' + destination_file, myfile)
            myfile.close()
        except Exception as e:
            self.sandbox.report_error("Failed to upload file " + myfile + " to " + destination_file +
                                      " on  the FTP server. Error is: " + str(e), raise_error=True)


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
        #path = path.replace('ftp://' + self.username + ':' + self.password + '@' + self.address +"/",'')
        path = path.replace('ftp://' + self.username + ':' + self.password + '@' + self.address ,'')
        path = path.replace(' ', '_')
        return path

    # -----------------------------------
    # -----------------------------------

    def create_dir(self,env_dir, write_to_output=True):
        try:
            dir_name = self._remove_header(env_dir)
            self.ftp.mkd(dir_name)
        except Exception as e:
            self.sandbox.report_error("Failed to create dir " + dir_name +
                                      " on  the FTP server. Error is: " + str(e), write_to_output_window=False, raise_error=True)
    # -----------------------------------
    # -----------------------------------
    def rename_file(self, file_path, new_name):
        try:
            file_path = self._remove_header(file_path)
            new_name = self._remove_header(new_name)
            #self.ftp.rename(from_name,new_name)
            file_idx=file_path.rfind('/')
            destination_dir = file_path[:(file_idx-len(file_path))]
            destination_dir = self._remove_header(destination_dir)

            pwd = self.ftp.pwd()
            if pwd != destination_dir:
                self.ftp.cwd(destination_dir)
            from_name = file_path[file_idx+1:]
            self.ftp.rename(from_name, new_name)
        except Exception as e:
            self.sandbox.report_error("Failed to rename file " + from_name + " to " + new_name +
                                      ". Error is: " + str(e), write_to_output_window=False, raise_error=True)


class SFTPClient(StorageClient):
    def __init__(self, sandbox, storage_resource):
        super(SFTPClient, self).__init__(sandbox, storage_resource)
        self.username = storage_resource.get_attribute("Storage username")
        self.password = storage_resource.get_attribute("Storage password")

    def _remove_header(self, path):
        path = path.replace('sftp://' + self.address + "/", '')
        path = path.replace(' ', '_')
        return path

    def download(self, source, destination):
        transport = paramiko.Transport((self.address, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(source, destination)
        sftp.close()
        transport.close()

    def create_dir(self, env_dir, write_to_output=True):
        transport = paramiko.Transport((self.address, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.mkdir(env_dir)
        sftp.close()
        transport.close()

    def rename_file(self, file_path, new_name):
        transport = paramiko.Transport((self.address, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.rename(file_path, new_name)
        sftp.close()
        transport.close()

    def get_configs_root(self):
        if self.configs_root:
            return 'sftp://' + self.username + ':' + self.password + '@' + self.address + "/" + self.configs_root

    def dir_exist(self, dir_name):
        transport = paramiko.Transport((self.address, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            sftp.lstat(dir_name)
            rv = True
        except:
            rv = False
        sftp.close()
        transport.close()
        return rv

    def upload(self, destination, source):
        transport = paramiko.Transport((self.address, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(source, destination)
        sftp.close()
        transport.close()

    # a = SFTPClient(None, None)
    # print a.dir_exist('a')
    # print a.dir_exist('b')
    # print a.dir_exist('c')
    # a.upload('/tmp/vmdet2.txt', r'c:\temp\vmdet.txt')
    # a.download('/tmp/vmdet2.txt', r'c:\temp\vmdet4.txt')
    # a.rename_file('b2', 'b')
    # a.create_dir('d')
    # self.address = '192.168.41.66'
    # self.port = 22
    # self.username = 'quali'
    # self.password = 'quali1234'

