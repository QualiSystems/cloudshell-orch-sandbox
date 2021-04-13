import os
import json


def get_reservation_context_details_dict():
    """
    Get the reservation details dictionary for this execution
    These details are automatically passed to the driver by CloudShell
    :rtype: dict[str,str]
    """
    return _get_quali_env_variable_object('reservationContext')


def get_reservation_context_details():
    """
    Get the reservation details for this execution
    These details are automatically passed to the driver by CloudShell

    :rtype: ReservationContextDetails
    """
    res_dict = _get_quali_env_variable_object('reservationContext')
    env_params = EnvironmentParameters(get_global_inputs(),
                                       get_resource_requirement_inputs(),
                                       get_resource_additional_info_inputs())
    res_details = ReservationContextDetails(res_dict['environmentName'],
                                            res_dict['domain'],
                                            res_dict['description'],
                                            env_params,
                                            res_dict['ownerUser'],
                                            res_dict['ownerPass'],
                                            res_dict['id'],
                                            res_dict['environmentPath'],
                                            get_permitted_users(),
                                            res_dict['runningUser'])
    return res_details


def get_connectivity_context_details():
    """
    Get the connectivity details dictionary for this execution
    :rtype: ConnectivityContextDetails
    """
    con_dict = _get_quali_env_variable_object('qualiConnectivityContext')
    return ConnectivityContextDetails(con_dict['serverAddress'],
                                      con_dict['tsAPIPort'],
                                      con_dict['adminUser'],
                                      con_dict['adminPass'],
                                      con_dict.get("tsAPIScheme", "http"))


def get_lifecycle_context_details():
    lifecycle_dict = _get_quali_env_variable_object('reservationLifecycleContext')
    return ReservationLifecycleContext(lifecycle_dict['reservationId'],
                                       lifecycle_dict['savedSandboxName'],
                                       lifecycle_dict['savedSandboxDescription'],
                                       lifecycle_dict['currentUserName'])

def _get_quali_env_variable_object(name):
    json_string = os.environ[name]
    json_object = json.loads(json_string)
    return json_object


def get_global_inputs():
    """
    Get the global inputs dictionary for the current reservation
    :rtype: dict[str,str]
    """
    reservationParams = get_reservation_context_details_dict()['parameters']
    return _covert_to_python_dictionary(reservationParams['globalInputs'])

def get_permitted_users():
    """
    Get the list of permitted users for the current reservation
    :rtype: List[UserDetails]
    """
    reservation_permitted_users = get_reservation_context_details_dict()['permittedUsers']
    return _covert_to_permitted_users_list(reservation_permitted_users)


def _covert_to_permitted_users_list(permitted_users):
    permitted_users_data = []
    for user in permitted_users:
        username = user['userName']
        email = user['email']
        permitted_users_data.append(UserDetails(username, email))
    return permitted_users_data



def get_resource_requirement_inputs():
    """
    Get the resource requirements inputs dictionary
    :rtype: ResourceInputs
    """
    reservationParams = get_reservation_context_details_dict()['parameters']
    return _covert_to_resource_inputs_dictionary(
        reservationParams['resourceRequirements'])


def get_resource_additional_info_inputs():
    """
    Get the resource additional inputs inputs dictionary
    :rtype: ResourceInputs
    """
    reservationParams = get_reservation_context_details_dict()['parameters']
    return _covert_to_resource_inputs_dictionary(
        reservationParams['resourceAdditionalInfo'])


def _covert_to_python_dictionary(parameters):
    inputsDictionary = {}
    for param in parameters:
        inputsDictionary[param['parameterName']] = param['value']
    return inputsDictionary


def _covert_to_resource_inputs_dictionary(parameters):
    inputsDictionary = ResourceInputs()
    for param in parameters:
        resource_name = param['resourceName']
        value = param['value']
        param_name = param['parameterName']
        possible_values = param.get('possibleValues', None)
        data = ResourceInputData(resource_name, param_name, value,
                                 possible_values)
        inputsDictionary[resource_name] = data
    return inputsDictionary


class ResourceInputs:
    def __init__(self):
        self._dictionary = {}
        """:type : dict[str, dict[str, ResourceInputData]]"""

    def __getitem__(self, resource_name):
        """:rtype: dict[str, dict[str, ResourceInputData]]"""
        return self._dictionary[resource_name]

    def __setitem__(self, resource_name, resource_input_data):
        if resource_name not in self._dictionary.keys():
            self._dictionary[resource_name] = {}
        self._dictionary[resource_name][resource_input_data.param_name] \
            = resource_input_data

    def __iter__(self):
        return self._dictionary.items()

    def iteritems(self):
        return self.__iter__()


class ReservationLifecycleContext:
    def __init__(self, reservation_id, saved_sandbox_name, saved_sandbox_description, currentUserName):
        self.reservation_id = reservation_id
        """:type : str"""
        self.saved_sandbox_name = saved_sandbox_name
        """:type : str"""
        self.saved_sandbox_description = saved_sandbox_description
        """:type : str"""
        self.currentUserName = currentUserName
        """:type : str"""


class ResourceInputData:
    def __init__(self, resource_name, param_name, value, possible_values):
        self.resource_name = resource_name
        """:type : str"""
        self.value = value
        """:type : str"""
        self.possible_values = possible_values
        """:type : list[str]"""
        self.param_name = param_name
        """:type : str"""


class ConnectivityContextDetails:
    def __init__(self, server_address, cloudshell_api_port,
                 admin_user, admin_pass, tsAPIScheme):
        self.server_address = server_address
        """:type : str"""
        self.cloudshell_api_port = cloudshell_api_port
        """:type : str"""
        self.admin_user = admin_user
        """:type : str"""
        self.admin_pass = admin_pass
        """:type : str"""
        self.tsAPIScheme = tsAPIScheme
        """:type : str"""


class EnvironmentParameters:
    def __init__(self, global_inputs, resource_requirements,
                 resource_additional_info):
        self.global_inputs = global_inputs
        """:type : dict[str,str]"""
        self.resource_requirements = resource_requirements
        """:type : ResourceInputs"""
        self.resource_additional_info = resource_additional_info
        """:type : ResourceInputs"""


class ReservationContextDetails:
    def __init__(self, environment_name, domain, description,
                 parameters, owner_user, owner_password,
                 reservation_id, environment_path, permitted_users, running_user):
        self.environment_name = environment_name
        """:type : str"""
        self.domain = domain
        """:type : str"""
        self.description = description
        """:type : str"""
        self.parameters = parameters
        """:type : EnvironmentParameters"""
        self.owner_user = owner_user
        """:type : str"""
        self.owner_password = owner_password
        """:type : str"""
        self.id = reservation_id
        """:type : str"""
        self.environment_path = environment_path
        """:type : str"""
        self.permitted_users = permitted_users
        """:type : list[UserDetails]"""
        self.running_user = running_user
        """:type : str"""


class UserDetails:
    def __init__(self, user_name, email):
        self.user_name = user_name
        """:type : str"""
        self.email = email
        """:type : str"""
