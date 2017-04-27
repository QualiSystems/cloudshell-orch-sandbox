from cloudshell.sandbox.orchestration.sandbox_manager import SandboxManager
from cloudshell.sandbox.orchestration.default_setup_orchestrator import DefaultSetupWorkflow


def conf_func1(sandbox):
    """
    :param SandboxManager sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="conf_func1 :-)")
    for glob in sandbox.Globals:
        sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                    message=glob + ": " + sandbox.Globals[glob])


def func(sandbox, apps):
    """
    :param SandboxManager sandbox:
    :return:
    """
    quali_server_ip = sandbox.Components.apps['quali server'].address

    for app in apps:
        sandbox.apps_configuration.set_config_param(app_DTO=app,
                                                    key='build_id',
                                                    value=sandbox.Globals['buid_id'])

        sandbox.apps_configuration.set_config_param(app_DTO=app,
                                                    key='server_address',
                                                    value=quali_server_ip)

    sandbox.apps_configuration.apply_apps_configurations(apps)


def func2(sandbox, resources):
    for resource in resources:  ## for ReservationAppResource in list{ReservationAppResource}
        sandbox.api.ExecuteCommand(sandbox.reservation_id, resource.FullName, 'Resource')


sandbox = SandboxManager()

DefaultSetupWorkflow.extend(sandbox, enable_configuration=False)

sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something started :-)")

demo_apps = sandbox.Components.get_apps_by_name_contains('demo')

sandbox.workflow.add_configuration_process(func, demo_apps, ['step name'])

# vcenter = sandbox.Components.Resources['vcenter']
# sandbox.workflow.add_configuration_process(func2, vcenter, ['step name'])

# databases = sandbox.Components.by_model('databases')

##databases is an object of components
# sandbox.workflow.on_configuration_ended(func, databases, ['this is a step'])

# sandbox.workflow.add_provisioning_process(conf_func1, ['step1', 'step2'], ['resource1', 'resource2'])

sandbox.execute()

sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something ended :-)")
