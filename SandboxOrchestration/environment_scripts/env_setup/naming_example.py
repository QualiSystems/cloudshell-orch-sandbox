from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.default_setup_orchestrator import DefaultSetupWorkflow

sandbox = Sandbox()

DefaultSetupWorkflow.extend(sandbox,
                            enable_configuration=True,
                            enable_connectivity=True,
                            enable_provisioning=True)

#get sandbox id
reservation_details = sandbox.automation_api.GetReservationDetails(sandbox.reservation_id)

#get all apps in sandbox
all_apps = sandbox.components.Apps

#get global parameter from sandbox
build_id_from_global_input = sandbox.globals['build_id']

#provisioning
sandbox.workflow.add_provisioning_process()
sandbox.workflow.on_provisioning_ended()

#connectivity
sandbox.workflow.add_connectivity_process()
sandbox.workflow.on_connectivity_ended()

#configuration
sandbox.workflow.add_configuration_process()
sandbox.workflow.on_configuration_ended()

sandbox.execute()

