from cloudshell.api.cloudshell_api import ReservedResourceInfo

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.default_setup_orchestrator import DefaultSetupWorkflow


def main():
    sandbox = Sandbox()
    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='Starting to execute the cool stuff!')

    DefaultSetupWorkflow.extend(sandbox, enable_configuration=False)  # Disable OOTB configuration
    sandbox.workflow.add_to_configuration(function=configure_apps,
                                          components=sandbox.components.apps)
    sandbox.execute()


def get_deployed_apps_by_name_contains(sandbox, name):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='get_deployed_apps_by_name_contains')

    resources = sandbox.automation_api.GetReservationDetails(sandbox.reservation_id).ReservationDescription.Resources

    results = []
    for resource in resources:
        print "type: " + str(type(resource).__name__)
        if type(resource) is ReservedResourceInfo:
            if name in resource.Name:
                results.append(resource)
        else:
            if name in resource:
                results.append(resource)
    return results


def configure_apps(sandbox, apps):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='configure_apps started')
    ##Configure databases
    databases = get_deployed_apps_by_name_contains(sandbox, 'Database')

    for app in databases:
        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                               message='Configuring App: ' + type(app).__name__)

        build_id = sandbox.globals['build_id']

        sandbox.apps_configuration.set_config_param(deployed_app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='Configuring Apps... ')

    sandbox.apps_configuration.apply_apps_configurations(databases)

    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='Im here 1 ')

    ##Configure web servers
    address = sandbox.components.resources['Application-server'].FullAddress

    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='Im here 2 ' + address)

    web_servers = get_deployed_apps_by_name_contains(sandbox, 'Web Server')

    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                           message='Im here 3 ' + address)

    for app in web_servers:
        build_id = sandbox.globals['build_id']
        sandbox.apps_configuration.set_config_param(deployed_app=app,
                                                    key='server',
                                                    value=address)

        sandbox.apps_configuration.set_config_param(deployed_app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.apps_configuration.apply_apps_configurations(apps)



main()
