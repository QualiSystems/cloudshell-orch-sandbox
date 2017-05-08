import datetime
import json

#from cloudshell.networking.apply_connectivity.apply_connectivity_operation import apply_connectivity_changes
#from cloudshell.networking.apply_connectivity.models.connectivity_result import ConnectivitySuccessResponse
from cloudshell.shell.core.interfaces.save_restore import OrchestrationSaveResult, OrchestrationSavedArtifact, \
    OrchestrationSavedArtifactInfo, OrchestrationRestoreRules
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext
from cloudshell.shell.core.context_utils import get_resource_name,get_attribute_by_name
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

class DummyRouterDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.health_status = 'passed'
        self.version = 1.0
        self.filename = ''
        self.load_firmware_will_fail = False
        self.resource_name = ''
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self.resource_name = str(get_resource_name(context)).strip()

        self.filename = self.resource_name + '_Catalyst_3850.cfg'
        pass

    # <editor-fold desc="Networking Standard Commands">
    def restore(self, context, cancellation_context, path, configuration_type, restore_method, vrf_management_name):
        """
        Restores a configuration file
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str path: The path to the configuration file, including the configuration file name.
        :param str restore_method: Determines whether the restore should append or override the current configuration.
        :param str configuration_type: Specify whether the file should update the startup or running config.
        :param str vrf_management_name: Optional. Virtual routing and Forwarding management name
        """
        return "Restoring " + self.resource_name + ': ' + str(path) + ' ' + str(configuration_type) + ' ' + str(restore_method) +\
               ' ' + str(vrf_management_name)

    def save(self, context, cancellation_context, folder_path, configuration_type, vrf_management_name):
        """
        Creates a configuration file and saves it to the provided destination
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str configuration_type: Specify whether the file should update the startup or running config. Value can one
        :param str folder_path: The path to the folder in which the configuration file will be saved.
        :param str vrf_management_name: Optional. Virtual routing and Forwarding management name
        :return The configuration file name.
        :rtype: str
        """
        return self.filename

    def load_firmware(self, context, cancellation_context, path, vrf_management_name):
        """
        Upload and updates firmware on the resource
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str path: path to tftp server where firmware file is stored
        :param str vrf_management_name: Optional. Virtual routing and Forwarding management name
        """
        if self.load_firmware_will_fail:
            #raise Exception('Failed to load firmware on ' + self.resource_name)
            raise CloudShellAPIError(1,'Failed to load firmware on ' + self.resource_name,'')
        pass

    def run_custom_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """
        pass

    def run_custom_config_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device in configuration mode
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """
        pass

    def shutdown(self, context, cancellation_context):
        """
        Sends a graceful shutdown to the device
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        """
        pass

    # </editor-fold>

    # <editor-fold desc="Orchestration Save and Restore Standard">
    def orchestration_save(self, context, cancellation_context, mode, custom_params):
        """
        Saves the Shell state and returns a description of the saved artifacts and information
        This command is intended for API use only by sandbox orchestration scripts to implement
        a save and restore workflow
        :param ResourceCommandContext context: the context object containing resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str mode: Snapshot save mode, can be one of two values 'shallow' (default) or 'deep'
        :param str custom_params: Set of custom parameters for the save operation
        :return: SavedResults serialized as JSON
        :rtype: OrchestrationSaveResult
        """

        # See below an example implementation, here we use jsonpickle for serialization,
        # to use this sample, you'll need to add jsonpickle to your requirements.txt file
        # The JSON schema is defined at: https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/saved_artifact_info.schema.json
        # You can find more information and examples examples in the spec document at https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/save%20%26%20restore%20standard.md
        '''
        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.

        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.
        identifier = created_date.strftime('%y_%m_%d %H_%M_%S_%f')

        orchestration_saved_artifact = OrchestrationSavedArtifact('REPLACE_WITH_ARTIFACT_TYPE', identifier)

        saved_artifacts_info = OrchestrationSavedArtifactInfo(
            resource_name="some_resource",
            created_date=created_date,
            restore_rules=OrchestrationRestoreRules(requires_same_resource=True),
            saved_artifact=orchestration_saved_artifact)

        return OrchestrationSaveResult(saved_artifacts_info)
        '''
        pass

    def orchestration_restore(self, context, cancellation_context, saved_artifact_info, custom_params):
        """
        Restores a saved artifact previously saved by this Shell driver using the orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str saved_artifact_info: A JSON string representing the state to restore including saved artifacts and info
        :param str custom_params: Set of custom parameters for the restore operation
        :return: None
        """
        '''
        # The saved_details JSON will be defined according to the JSON Schema and is the same object returned via the
        # orchestration save function.
        # Example input:
        # {
        #     "saved_artifact": {
        #      "artifact_type": "REPLACE_WITH_ARTIFACT_TYPE",
        #      "identifier": "16_08_09 11_21_35_657000"
        #     },
        #     "resource_name": "some_resource",
        #     "restore_rules": {
        #      "requires_same_resource": true
        #     },
        #     "created_date": "2016-08-09T11:21:35.657000"
        #    }

        # The example code below just parses and prints the saved artifact identifier
        saved_details_object = json.loads(saved_details)
        return saved_details_object[u'saved_artifact'][u'identifier']
        '''
        pass

    # </editor-fold>

    # <editor-fold desc="Connectivity Provider Interface (Optional)">

    '''
    # The ApplyConnectivityChanges function is intended to be used for using switches as connectivity providers
    # for other devices. If the Switch shell is intended to be used a DUT only there is no need to implement it

    def ApplyConnectivityChanges(self, context, request):
        """
        Configures VLANs on multiple ports or port-channels
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON object with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the switch
        :rtype: str
        """

        return apply_connectivity_changes(request=request,
                                          add_vlan_action=lambda x: ConnectivitySuccessResponse(x,'Success'),
                                          remove_vlan_action=lambda x: ConnectivitySuccessResponse(x,'Success'))



    '''

    # </editor-fold>

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information
        # Add sub resources details
        sub_resources = [ AutoLoadResource(model ='Generic Chassis',name= 'Chassis 1', relative_address='1'),
        AutoLoadResource(model='Generic Module',name= 'Module 1',relative_address= '1/1'),
        AutoLoadResource(model='Generic Port',name= 'Port 1', relative_address='1/1/1'),
        AutoLoadResource(model='Generic Port', name='Port 2', relative_address='1/1/2'),
        AutoLoadResource(model='Generic Power Port', name='Power Port', relative_address='1/PP1')]


        attributes = [ AutoLoadAttribute(relative_address='', attribute_name='Location', attribute_value='Santa Clara Lab'),
                      AutoLoadAttribute('', 'Model', 'Catalyst 3850'),
                      AutoLoadAttribute('', 'Vendor', 'Cisco'),
                      AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
                      AutoLoadAttribute('1', 'Model', 'WS-X4232-GB-RJ'),
                      AutoLoadAttribute('1/1', 'Model', 'WS-X4233-GB-EJ'),
                      AutoLoadAttribute('1/1', 'Serial Number', 'RVE056702UD'),
                      AutoLoadAttribute('1/1/1', 'MAC Address', 'fe80::e10c:f055:f7f1:bb7t16'),
                      AutoLoadAttribute('1/1/1', 'IPv4 Address', '192.168.10.7'),
                      AutoLoadAttribute('1/1/2', 'MAC Address', 'te67::e40c:g755:f55y:gh7w36'),
                      AutoLoadAttribute('1/1/2', 'IPv4 Address', '192.168.10.9'),
                      AutoLoadAttribute('1/PP1', 'Model', 'WS-X4232-GB-RJ'),
                      AutoLoadAttribute('1/PP1', 'Port Description', 'Power'),
                      AutoLoadAttribute('1/PP1', 'Serial Number', 'RVE056702UD')]

        return AutoLoadDetails(sub_resources,attributes)



    # </editor-fold>

    # <editor-fold desc="Health Check">

    def health_check(self,context):
        """
        Checks if the device is up and connectable
        :return: str: Success or fail message
        """
        return 'Health check on resource ' + self.resource_name + ' ' + self.health_status + '.'

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def set_health_status(self,status):
        """
        Set the health status passed/failed
        """
        if status == 'passed' or status == 'failed':
            self.health_status = status
        else:
            #raise Exception('Invalid status. Permitted values passed/fail')
            raise CloudShellAPIError(1,'Invalid status. Permitted values passed/fail','')

    def set_firmware_data(self,version, will_fail):
        """
        Set the firmware version and success
        :param str version : the firmware version
        :param str will_fail : the firmware sucsess
        """
        self.version = version
        if will_fail.lower() == 'true':
            self.load_firmware_will_fail = True
        else:
            self.load_firmware_will_fail = False

    def set_saved_file_name(self, filename):
        """
        Set the firmware version
        :param str version : the firmware version
        """
        self.filename = filename

    def get_version(self):
        """
        Return firmware version
        :return: str: version
        """
        return self.version
