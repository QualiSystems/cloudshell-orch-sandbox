# coding=utf-8
# __author__ = 'ayelet.a'
import sys
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import *
from cloudshell.api.common_cloudshell_api import *
from QualiUtils import *

import datetime
import json


class ResourceBase(object):
    def __init__(self, resource_name, resource_alias=''):
        if resource_name != "":
            self.api_session = helpers.get_api_session()
            self.details = self.api_session.GetResourceDetails(resource_name)
            self.name = self.details.Name
            self.address = self.details.Address
            self.commands = self.api_session.GetResourceCommands(resource_name).Commands

            self.connected_commands = self.api_session.GetResourceConnectedCommands(resource_name).Commands

            self.attributes = self.details.ResourceAttributes
            # If there is an attribute named 'model' take its value (exist in shells), otherwise take the family's model
            if self.attribute_exist('Model'):
                self.model = self.get_attribute('Model')
            else:
                self.model = self.details.ResourceModelName

            self.alias = resource_alias
            #self.standard_version = self._get_standard_version()



    # -----------------------------------------
    # -----------------------------------------
    def has_command(self, command_name):
        for command in self.commands:
            if command_name == command.Name:
                return True
        return False

    # -----------------------------------------
    # -----------------------------------------
    def attribute_exist(self, attribute_name):
        attribute_name = attribute_name.lower()
        for attribute in self.attributes:
            if attribute.Name.lower() == attribute_name:
                return True
        return False


    # -----------------------------------------
    # -----------------------------------------
    def get_attribute(self, attribute_name):
        attribute_name = attribute_name.lower()
        for attribute in self.attributes:
            if attribute.Name.lower() == attribute_name:
                return attribute.Value
        raise QualiError(self.name, "Attribute: " + attribute_name + " not found")

    # -----------------------------------------
    # -----------------------------------------
    def set_attribute_value(self, attribute_name, attribute_value):
        try:
            self.api_session.SetAttributeValue(resourceFullPath=self.name, attributeName=attribute_name,
                                               attributeValue=attribute_value)
        except CloudShellAPIError as error:
            raise QualiError(self.name, "Attribute: " + attribute_name + " not found. " + error.message)

    # -----------------------------------------
    # implement the command to get the neighbors and their ports
    # will return a dictionary of device's name and its port
    # -----------------------------------------
    def get_neighbors(self, reservation_id):
        """
        Launch the get_neighbors command on the device
        :param str reservation_id:  Reservation id.
        """
        # Run executeCommand with the getNeighbors command and its params (ConfigPath,RestoreMethod)
        try:
            self.execute_command(reservation_id, 'get_neighbors', printOutput=True)
        except QualiError as error:
            raise QualiError(self.name, "Failed to update neighbors: " + error.message)
        except:
            raise QualiError(self.name, "Failed to update neighbors. Unexpected error:" + str(sys.exc_info()[0]))

    # ----------------------------------
    # ----------------------------------
    '''
    def _get_standard_version(self,reservation_id):
        """
        Run the get standard details command on all the devices
        :param str reservation_id:  Reservation id.
        """
        if self.has_command('get_standard_version'):
            try:
                return self.execute_command(reservation_id, 'get_standard_version', printOutput=False).Output()

            except QualiError as qe:
                err = "Failed to get the standard version for device: " + self.name + ". " + str(qe)
                return err
        else:
            if self.model.lower().find('cisco ios-xr')>=0 or self.model.lower().find('cisco ios ')>=0 or self.model.lower().find('cisco nxos')>=0:
                return '3'
            elif self.model.lower().find('ericsson')>=0 or self.model.lower().find('gigavue-os')>=0:
                return '4'
        return -1
    '''
    # ----------------------------------
    # ----------------------------------
    def health_check(self,reservation_id):
        """
        Run the healthCheck command on all the devices
        :param str reservation_id:  Reservation id.
        """
        if self.has_command('health_check'):
            try:
                # Return a detailed description in case of a failure
                out = self.execute_command(reservation_id, 'health_check', printOutput=False)#.Output()
                if out.Output.find(' passed') == -1:
                    err = "Health check did not pass for device " + self.name + ". " + out
                    return err

            except QualiError as qe:
                err = "Health check did not pass for device " + self.name + ". " + str(qe)
                return err
        return ""



    # -----------------------------------------
    # -----------------------------------------
    def load_config(self, reservation_id,config_path,artifact_info = None):
        """
        Load config from a configuration file on the device
        :param str reservation_id:  Reservation id.
        :param config_path:  The path to the config file
        :param config_type:  StartUp or Running
        :param restore_method:  Optional. Restore method. Can be Append or Override.
        """
        # Run executeCommand with the restore command and its params (ConfigPath,RestoreMethod)

        try:
            is_snapshot = True
            if(artifact_info == None):
                artifact_info = self.create_artifact_info(config_path)
                is_snapshot = False
                json_str = json.dumps(artifact_info)
            else:
                json_str = artifact_info

            if self.is_app():
                if is_snapshot:

                    for command in self.connected_commands:
                        if 'orchestration_restore' == command.Name:
                            tag = command.Tag

                            self.execute_connected_command(reservation_id, 'orchestration_restore',tag,
                                commandInputs=[json_str],
                                printOutput=True)

            else:

                if self.has_command('orchestration_restore'):

                    command_inputs = [InputNameValue('saved_details', json_str)]

                    if self.attribute_exist('VRF Management Name'):
                        vrf_name = self.get_attribute('VRF Management Name')
                        command_inputs.append(InputNameValue('vrf_management_name', str(vrf_name)))

                    self.execute_command(reservation_id, 'orchestration_restore',
                                     commandInputs=command_inputs,
                                     printOutput=True)

        except QualiError as qerror:
            raise QualiError(self.name, "Failed to load configuration: " + qerror.message)
        except:
            raise QualiError(self.name, "Failed to load configuration. Unexpected error:" + str(sys.exc_info()[0]))

    # -----------------------------------------
    # -----------------------------------------
    def save_config(self, reservation_id, config_path, config_type):
        """
        Save config from the device
        :param str reservation_id:  Reservation id.
        :param config_path:  The path where to save the config file
        :param config_type:  StartUp or Running
        """
        # Run executeCommand with the restore command and its params (ConfigPath,RestoreMethod)
        try:

            data = {
                'folder_path': str(config_path)
            }
            json_str = json.dumps(data)
            config_name = None

            if self.is_app():

                for command in self.connected_commands:
                    if 'orchestration_save' == command.Name:
                        tag = command.Tag

                        config_name = self.execute_connected_command(reservation_id, 'orchestration_save',tag,
                                               commandInputs=['shallow',''],
                                               printOutput=False)



            else:
                if self.has_command('orchestration_save'):

                    config_name = self.execute_command(reservation_id, 'orchestration_save',
                                               commandInputs=[InputNameValue('custom_params',json_str),
                                                              InputNameValue('mode','shallow')],
                                               printOutput=False)



            if config_name:
                return config_name.Output
            else:
                return ""

            # check the output is the created file name

        except QualiError as qerror:
            raise QualiError(self.name, "Failed to save configuration: " + qerror.message)
        except:
            raise QualiError(self.name, "Failed to save configuration. Unexpected error:" + str(sys.exc_info()[0]))

    # -----------------------------------------
    # -----------------------------------------
    # noinspection PyPep8Naming,PyDefaultArgument
    def execute_command(self, reservation_id, commandName, commandInputs=[], printOutput=False):
        """
        Executes a command
        :param str reservation_id:  Reservation id.
        :param str commandName:  Command Name - Specify the name of the command.
        :param list[InputNameValue] commandInputs:  Command Inputs - Specify a matrix of input names and values
        required for executing the command.
        :param bool printOutput:  Print Output - Defines whether to print the command output
         in the Sandbox command output window.
        :rtype: CommandExecutionCompletedResultInfo
        """
        # check the command exists on the device
        if self.commands.__sizeof__() > 0:
            # Run executeCommand with the restore command and its params (ConfigPath,RestoreMethod)
            try:
                return self.api_session.ExecuteCommand(reservation_id, self.name, 'Resource', commandName,
                                                       commandInputs, printOutput)
            except CloudShellAPIError as error:
                raise QualiError(self.name, error.message)
        else:
            raise QualiError(self.name, 'No commands were found')

    # -----------------------------------------
    # -----------------------------------------
    # noinspection PyPep8Naming,PyDefaultArgument
    def execute_connected_command(self, reservation_id, commandName,tag,commandInputs=[], printOutput=False):
        """
        Executes a command
        :param str reservation_id:  Reservation id.
        :param str commandName:  Command Name - Specify the name of the command.
        :param list[InputNameValue] commandInputs:  Command Inputs - Specify a matrix of input names and values
        required for executing the command.
        :param bool printOutput:  Print Output - Defines whether to print the command output
         in the Sandbox command output window.
        :rtype: CommandExecutionCompletedResultInfo
        """
        # check the command exists on the device
        if self.connected_commands.__sizeof__() > 0:
            # Run executeCommand with the restore command and its params (ConfigPath,RestoreMethod)
            try:
               return self.api_session.ExecuteResourceConnectedCommand(reservation_id,self.name,commandName=commandName,commandTag=tag,parameterValues = commandInputs)

            except CloudShellAPIError as error:
                raise QualiError(self.name, error.message)
        else:
            raise QualiError(self.name, 'No commands were found')


    # -----------------------------------------
    # -----------------------------------------
    def set_address(self, address):
        self.api_session.UpdateResourceAddress(resourceFullPath=self.name, resourceAddress=address)


    # -----------------------------------------
    # -----------------------------------------
    def load_firmware(self, reservation_id, image_path):
        """
        Load firmware from image file on the device
        :param str reservation_id:  Reservation id.
        :param str image_path:  The path to the firmware file
        """
        # Run executeCommand with the update_firmware command and its params (ConfigPath,RestoreMethod)
        try:
            command_inputs = [InputNameValue('path', str(image_path))]
            if self.attribute_exist('VRF Management Name'):
                vrf_name = self.get_attribute('VRF Management Name')
                command_inputs.append(InputNameValue('vrf_management_name', str(vrf_name)))
            self.execute_command(reservation_id, 'load_firmware',
                                 commandInputs=command_inputs,
                                 printOutput=True)
        except QualiError as qerror:
            raise QualiError(self.name, "Failed to load firmware: " + qerror.message)
        except:
            raise QualiError(self.name, "Failed to load firmware. Unexpected error:" + str(sys.exc_info()[0]))

    # -----------------------------------------
    # -----------------------------------------
    def set_live_status(self,live_status_name, additional_info=''):
        self.api_session.SetResourceLiveStatus(self.name,live_status_name, additional_info)

    # -----------------------------------------
    # -----------------------------------------
    def get_live_status(self):
        self.api_session.GetResourceLiveStatus(self.name)

    # -----------------------------------------
    # -----------------------------------------
    def print_commands (self):

        print "Resource commands:" + self.commands
	# -----------------------------------------
    # -----------------------------------------

    def create_artifact_info(self,config_path):

        created_date = str(datetime.datetime.utcnow())

        saved_artifacts_info = {
            "saved_artifacts_info": {
                "saved_artifact": {
                    "artifact_type": "tftp",
                    "identifier": config_path
                },
                "resource_name": self.name,
                "restore_rules": {
                    "requires_same_resource": True,
                },
                "created_date": created_date
            }
        }

        return saved_artifacts_info

    # -----------------------------------------
    # -----------------------------------------
    def is_app(self):

        if hasattr(self.details.VmDetails, "UID"):
            return True
        else:
            return False





