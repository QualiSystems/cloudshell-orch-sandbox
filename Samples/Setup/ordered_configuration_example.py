from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow


def main():
    sandbox = Sandbox()
    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                           message='Starting to execute the cool stuff!')

    DefaultSetupWorkflow().register(sandbox, enable_configuration=False)  # Disable OOTB configuration
    sandbox.workflow.add_to_configuration(function=configure_apps,
                                          components=sandbox.components.apps)
    sandbox.execute_setup()


def configure_apps(sandbox, apps):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                           message='configure_apps started')
    ##Configure databases
    databases = sandbox.components.get_apps_by_name_contains('Database')

    build_id = sandbox.global_inputs['build_id']

    for app in databases:
        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                               message='Configuring App: ' + type(app).__name__)

        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                           message='Configuring Apps... ')

    sandbox.apps_configuration.apply_apps_configurations(databases)

    ##Configure web servers
    address = sandbox.components.resources['Application-server'].FullAddress

    web_servers = sandbox.components.get_apps_by_name_contains('Web Server')

    for app in web_servers:
        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='server',
                                                    value=address)

        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.apps_configuration.apply_apps_configurations(web_servers)



main()
