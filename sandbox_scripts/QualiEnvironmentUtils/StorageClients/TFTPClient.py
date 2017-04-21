# coding=utf-8
import subprocess
from StorageClient import *
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
import tempfile
import pip

try:
    import tftpy
    imported_tftpy = True
except:
    try:
        pip.main(["install","tftpy"])
        import tftpy
    except:
        imported_tftpy = False


class TFTPClient(StorageClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox, storage_resource):
        super(TFTPClient,self).__init__(sandbox, storage_resource)
        if imported_tftpy == False:
            self.sandbox.report_error('tftpy lib was not installed', write_to_output_window=True)

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
    def save_artifact_info(self,saved_artifact_info,env_dir,dest_name,write_to_output=False):

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        win_path = self._remove_header(env_dir)
        new_config_path = win_path + '/' + dest_name
        new_config_path = new_config_path.replace("\\","/")

        try:

            with open(tmp_file, 'w+') as outfile:
                json.dump(saved_artifact_info,outfile)

            self.upload(new_config_path,tmp_file)
            tmp_file.close()
            os.unlink(tmp_file.name)

        except:
            err = 'saved artifact info failed'
            self.sandbox.report_error(err, write_to_output_window=write_to_output)

    # ----------------------------------
    # ----------------------------------

    def download_artifact_info(self,root_folder,dest_name,write_to_output=False):

        data = None
        new_config_path = root_folder + '/' + dest_name
        new_config_path = new_config_path.replace("\\","/")

        try:
            # Reading data backm
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tftpy.log.propagate = False
            tftpy.log.addHandler(logging.NullHandler())

            self.tftp_client.download(str(new_config_path),tmp_file)
            with open(tmp_file,'r') as outfile:
                data = json.load(outfile)

            tmp_file.close()
            os.unlink(tmp_file.name)
        except:
            err = 'failed to download artifact info file: ' + new_config_path
            self.sandbox.report_error(err, raise_error=False, write_to_output_window=write_to_output)

        return data

