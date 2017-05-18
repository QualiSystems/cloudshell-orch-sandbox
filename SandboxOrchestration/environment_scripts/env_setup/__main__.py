from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow


def by_name(sandbox, services):
    for service in services:
        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                               message='by_name : ' + service.ServiceName)


def by_alias(sandbox, services):
    for service in services:
        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                               message='by_alias : ' + service.Alias)


sandbox = Sandbox()

DefaultSetupWorkflow().register(sandbox, enable_connectivity=False, enable_configuration=False)

alias = sandbox.components.get_services_by_alias('VLAN Auto')

name = sandbox.components.get_services_by_name('VLAN Auto')

sandbox.workflow.on_provisioning_ended(by_name, name)

sandbox.workflow.on_provisioning_ended(by_alias, alias)

sandbox.execute_setup()
