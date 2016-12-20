# coding=utf-8
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
from abc import ABCMeta
from abc import abstractmethod
import ftplib
import subprocess
import json
import tempfile
import logging
try:
    import tftpy
    imported_tftpy = True
except Exception as e:
    imported_tftpy = False
	

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
    def download_artifact_info(self,env_dir,dest_name,write_to_output=True):
        raise NotImplementedError('subclasses must override download_artifact_info()!')

class TFTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        if imported_tftpy == False:
            self.sandbox.report_error('TFTPY lib was not installed', write_to_output_window=True)
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

        tftpy.log.propagate = False
        tftpy.log.addHandler(logging.NullHandler())

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

        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=write_to_output)

        self.create_src_file_on_tftp(env_dir,write_to_output)

    #-----------------------------------
    #-----------------------------------
    def delete(self, file_path):
        """
		Delete file from the tftp server
		:param str file_path:  The path to the file on the ftp server
		"""
        try:
            win_path = self._remove_header(file_path)
            new_config_path = self.tftp_root_dir + '\\' + win_path
            new_config_path = new_config_path.replace('/', "\\")

            self.tftp_psexe = self.tftp_psexe.replace('/', '\\')
            pspath = self.tftp_psexe + '\psexec.exe'
            user = self.username
            password = self.password

            command_array = ['cmd', '/c', 'del ', new_config_path]

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

            #   self.sandbox.report_info('delete file: ' +  new_config_path, write_to_output)
            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)

        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=True)

    # ----------------------------------
    # ----------------------------------
    def rename_file(self, file_path, new_name):
        """
        Rename file from the ftp server
        :param str file_path:  The path to the file on the ftp server
        """
        try:
            win_path = self._remove_header(file_path)
            new_config_path = self.tftp_root_dir + '\\' + win_path
            new_config_path = new_config_path.replace('/', "\\")

            self.tftp_psexe = self.tftp_psexe.replace('/', '\\')
            pspath = self.tftp_psexe + '\psexec.exe'
            user = self.username
            password = self.password

            command_array = ['cmd', '/c', 'ren ', new_config_path,new_name]

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

            #   self.sandbox.report_info('rename file: ' +  new_config_path, write_to_output)
            rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)


        except Exception as e:
            if hasattr(e, 'output'):
                ou = str(e.output)
            else:
                ou = 'no output'
                err = 'psexec failed: ' + str(e).replace('\r\n', '\n') + ': ' + ou.replace('\r\n', '\n')
                self.sandbox.report_error(err, write_to_output_window=True)

    # ----------------------------------
    # ----------------------------------
    def create_src_file_on_storage(self,win_path,write_to_output=True):
        #creating new file on tftp with the sandbox id name to indicate that this topology was saved as snapshot

       #Src
        #tmp_file = "C:\\tmp.txt"
        tmp_file = "C:\\tmp" + self.sandbox.id + ".txt"
        src_path = tmp_file.replace("\\","/")
        #destination
        snapshot_source_name = "Snapshot_"+self.sandbox.id
        head,tail = os.path.split(win_path)
        path = head + '/' + snapshot_source_name +".txt"
        path = path.replace("\\","/")

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

        #tmpfile = "data.json"
        tmpfile = "data" + self.sandbox.id + ".json"
        win_path = self._remove_header(env_dir)
        new_config_path = win_path + '/' + dest_name
        new_config_path = new_config_path.replace("\\","/")

        try:

            with open(tmpfile, 'w+') as outfile:
                json.dump(saved_artifact_info,outfile)

            self.upload(new_config_path,tmpfile)
            os.remove(tmpfile)

        except:
            err = 'saved artifact info failed '
            self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------

    def download_artifact_info(self,env_dir,dest_name,write_to_output=True):

       #tmpfile = "data.json"
        tmpfile = "data" + self.sandbox.id + ".json"
        data = None

        win_path = self._remove_header(env_dir)
        head, tail = os.path.split(win_path)

        new_config_path = head + '/' + dest_name
        new_config_path = new_config_path.replace("\\","/")

        try:
            # Reading data backm

            tftpy.log.propagate = False
            tftpy.log.addHandler(logging.NullHandler())

            self.tftp_client.download(str(new_config_path),tmpfile)
            #self.download(new_config_path, tmpfile)
            with open(tmpfile,'r') as outfile:
                data = json.load(outfile)
            #os.remove(tmpfile)
        except:
            #if os.path.isfile(tmpfile):
             #   os.remove(tmpfile)
            err = 'download artifact info failed '
           # self.sandbox.report_error(err, write_to_output_window=write_to_output)

        return data



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
    def __del__(self):
        try:
            self.ftp.quit()
        except:
            pass

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
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
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
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
            file_idx=destination.rfind('/')
            destination_dir = destination[:(file_idx-len(destination))]
            destination_dir = self._remove_header(destination_dir)
            #destination_dir = destination_dir.replace('//','/')
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
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
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
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
            dir_name = self._remove_header(env_dir)
            self.ftp.mkd(dir_name)

        except Exception as e:
            self.sandbox.report_error("Failed to create dir " + dir_name +
                                      " on  the FTP server. Error is: " + str(e), write_to_output_window=False, raise_error=True)

        self.create_src_file_on_tftp(env_dir, write_to_output)
    # -----------------------------------
    # -----------------------------------
    def create_src_file_on_storage(self, env_dir, write_to_output=True):

        try:
            snapshot_source_name = "Snapshot_" + self.sandbox.id
            head, tail = os.path.split(env_dir)
            path = head + '/' + snapshot_source_name + ".txt"

            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tf = file(tmp_file.name, 'wb+')
            tf.write('1')
            tf.flush()
            tf.close()

            self.upload(path, tmp_file.name)
            tmp_file.close()
            os.unlink(tmp_file.name)

        except Exception as e:
            self.sandbox.report_error("Failed to create file " + snapshot_source_name +
                                      " on  the FTP server. Error is: " + str(e), write_to_output_window=False,
                                      raise_error=True)

    # -----------------------------------
    # -----------------------------------
    def rename_file(self, file_path, new_name):
        try:
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
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


    # ----------------------------------
    # ----------------------------------
    def delete(self, file_path):
        """
        Delete file from the ftp server
        :param str file_path:  The path to the file on the ftp server
        """
        try:
            self.ftp.connect(self.address, self.port)
            self.ftp.login(self.username, self.password)
            file_path = self._remove_header(file_path)
            file_idx=file_path.rfind('/')
            destination_dir = file_path[:(file_idx-len(file_path))]
            destination_dir = self._remove_header(destination_dir)

            pwd = self.ftp.pwd()
            if pwd != destination_dir:
                self.ftp.cwd(destination_dir)
            file_name = file_path[file_idx+1:]
            self.ftp.delete(file_name)
        except Exception as e:
            self.sandbox.report_error("Failed to delete file " + file_path +
                                      ". Error is: " + str(e), write_to_output_window=False, raise_error=True)


    # ----------------------------------
    # ----------------------------------
    def save_artifact_info(self, saved_artifact_info, file_path, dest_name, write_to_output=True):

        try:
            file_path = self._remove_header(file_path)
            new_config_path = file_path + '/' + dest_name

            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tf = file(tmp_file.name, 'wb+')
            json.dump(saved_artifact_info, tf)
            tf.flush()
            tf.close()
            self.upload(new_config_path, tmp_file.name)
            tmp_file.close()
            os.unlink(tmp_file.name)

        except:
            err = 'saved artifact info failed '
            self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------

    def download_artifact_info(self, file_path, dest_name, write_to_output=True):

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        data = None

        file_path = self._remove_header(file_path)
        head, tail = os.path.split(file_path)
        new_config_path = head + '/' + dest_name

        try:
            self.download(str(new_config_path), tmp_file)
            with open(tmp_file, 'r') as outfile:
                data = json.load(outfile)

        except:
            err = 'download artifact info failed '

        return data