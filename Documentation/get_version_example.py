# This file demonstrates implementation of get_version for Ericsson's IPOS/SEOS devices.

from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import *
import re


def main():
    api_session = helpers.get_api_session()
    resource_details = helpers.get_resource_context_details()
    reservation_id = helpers.get_reservation_context_details().id
    # Run custom command on the device requesting the version
    command_inputs = [InputNameValue('custom_command', str('show version'))]
    cmd_out = api_session.ExecuteCommand(reservation_id, resource_details.name, 'Resource', 'run_custom_command',
                                         commandInputs=command_inputs).Output
    # Clean unwanted text, leaving only the version itself
    match = re.search('(Ericsson IPOS Version|SmartEdge OS Version).+',cmd_out)
    version=match.group(0)
    version = version.replace('Ericsson IPOS Version ','')
    version = version.replace('SmartEdge OS Version ','')
    print str(version)


main()