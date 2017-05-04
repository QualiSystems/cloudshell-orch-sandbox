import os
import time

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.default_setup_orchestrator import DefaultSetupWorkflow


def conf_func1(sandbox):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="conf_func1 :-)")
    for glob in sandbox.globals:
        sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                    message=glob + ": " + sandbox.globals[glob])


def func(sandbox, apps, steps):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="steps: " + str(steps) + " ,apps: " + str(apps))

    # quali_server_ip = sandbox.components.Resources['quali server'].FullAddress

    for app in apps:
        build_id = sandbox.globals['build_id']
        sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                    message="Using global inputs: " + build_id)

        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='build_id',
                                                    value=build_id)

        sandbox.apps_configuration.set_config_param(app=app,
                                                    key='server_address',
                                                    value='address')

    sandbox.apps_configuration.apply_apps_configurations(apps)


def func2(sandbox, resources):
    for resource in resources:  ## for ReservationAppResource in list{ReservationAppResource}
        sandbox.api.ExecuteCommand(sandbox.reservation_id, resource.FullName, 'Resource')


sandbox = Sandbox()

DefaultSetupWorkflow.extend(sandbox, enable_configuration=False)


sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something started :-)")

demo_apps = sandbox.components.get_apps_by_name('demo')

sandbox.workflow.add_configuration_process(func, demo_apps, ['step name'])

sandbox.execute()

sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something ended :-)")
