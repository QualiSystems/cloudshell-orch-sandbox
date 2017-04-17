# coding=utf-8
import ftplib
import tempfile

from StorageClient import *
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *


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
            destination_file = destination[file_idx+1:]
            #destination_dir = destination_dir.replace('//','/')
            self.ftp.cwd(destination_dir)
            myfile = open(source, 'r')
            self.ftp.storlines('STOR ' + destination_file, myfile)
            myfile.close()
            self.sandbox.report_info("Successfully uploaded " + source + " to " + destination_file)
        except Exception as e:
            self.sandbox.report_error("Failed to upload file " + source + " to " + destination_file +
                                      " on  the FTP server. Error is: " + str(e), raise_error=True)
            print "Failed to upload file " + source + " to " + destination_file + " on  the FTP server. Error is: " + str(e)


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
        # Jim: need the line with '/' added to replace - it was set to the other line!
        path = path.replace('ftp://' + self.username + ':' + self.password + '@' + self.address +"/",'')
        #path = path.replace('ftp://' + self.username + ':' + self.password + '@' + self.address,'')
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
            self.create_src_file_on_storage(env_dir, write_to_output)
        except Exception as e:
            self.sandbox.report_error("Failed to create dir " + dir_name +
                                      " on  the FTP server. Error is: " + str(e), write_to_output_window=False, raise_error=True)


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

    def download_artifact_info(self, root_folder, dest_name, write_to_output=False):

        data = None
        new_config_path = root_folder + '/' + dest_name

        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.download(str(new_config_path), tmp_file)
            with open(tmp_file, 'r') as outfile:
                data = json.load(outfile)

            tmp_file.close()
            os.unlink(tmp_file.name)

        except:
            err = 'failed to download artifact info file: ' + new_config_path
            self.sandbox.report_error(err, raise_error=False, write_to_output_window=write_to_output)

        return data