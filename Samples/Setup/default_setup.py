from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

sandbox = Sandbox()

DefaultSetupWorkflow().register(sandbox)

sandbox.execute_setup()

