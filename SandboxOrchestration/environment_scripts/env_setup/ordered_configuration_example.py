from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.default_setup_orchestrator import DefaultSetupWorkflow


def main():
    sandbox = Sandbox()
    DefaultSetupWorkflow.extend(sandbox, enable_configuration=False)  ##Disable OOTB configuration
    sandbox.workflow.add_configuration_process(function=configure_apps,
                                               resources=sandbox.components.Apps)
    sandbox.execute()


def configure_apps(sandbox, apps):
    """
    :param Sandbox sandbox:
    :return:
    """
    ##Configure databases
    databases = sandbox.components.get_apps_by_name_contains('Database')
    for app in databases:
        build_id = sandbox.globals['build_id']
        sandbox.apps_configuration.set_config_param(deployed_app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.apps_configuration.apply_apps_configurations(databases)

    ##Configure web servers
    address = sandbox.components.Resources['Application-server'].FullAddress

    web_servers = sandbox.components.get_apps_by_name_contains('Web Server')
    for app in web_servers:
        build_id = sandbox.globals['build_id']
        sandbox.apps_configuration.set_config_param(deployed_app=app,
                                                    key='server',
                                                    value=address)

    sandbox.apps_configuration.apply_apps_configurations(apps)


main()
