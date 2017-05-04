from cloudshell.sandbox.orchestration.sandbox_manager import SandboxManager
from cloudshell.sandbox.orchestration.default_setup_orchestrator import DefaultSetupWorkflow


def main():
    sandbox = SandboxManager()
    DefaultSetupWorkflow.extend(sandbox, enable_configuration=False)  ##Disable OOTB configuration
    sandbox.workflow.add_configuration_process(function=configure_apps,
                                               resources=sandbox.components.Apps,
                                               steps=['Configuration'])
    sandbox.execute()


def configure_apps(sandbox, apps):
    """
    :param SandboxManager sandbox:
    :return:
    """
    ##Configure databases
    databases = sandbox.components.get_apps_by_name('Database')
    for app in databases:
        build_id = sandbox.globals['build_id']
        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='build_id',
                                                    value=build_id)

    sandbox.apps_configuration.apply_apps_configurations(databases)

    ##Configure web servers
    address = sandbox.components.Resources['Application-server'].FullAddress
    web_servers = sandbox.components.get_apps_by_name('Web Server')
    for app in web_servers:
        build_id = sandbox.globals['build_id']
        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='server',
                                                    value=address)

    sandbox.apps_configuration.apply_apps_configurations(apps)


main()
