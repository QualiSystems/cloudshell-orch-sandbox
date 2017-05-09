from cloudshell.workflow.orchestration.default_setup_orchestrator import DefaultSetupWorkflow
from cloudshell.workflow.orchestration.sandbox import Sandbox


def load_firmware_sequential(sandbox, components):
    """
    :param Sandbox sandbox:
    :param components:
    :return:
    """
    for component in components:
        sandbox.automation_api.ExecuteCommand(reservationId=sandbox.id,
                                              targetName=component.Name,
                                              targetType='Resource',
                                              commandName='return_simple_string')


sandbox = Sandbox()
DefaultSetupWorkflow().register(sandbox)

nxso_switches = sandbox.components.get_resources_by_model('Generic Chassis Model')
sandbox.workflow.add_to_provisioning(function=load_firmware_sequential,
                                     components=nxso_switches)

sandbox.execute()
