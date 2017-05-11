from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow

sandbox = Sandbox()

DefaultTeardownWorkflow().register(sandbox)

sandbox.execute_teardown()
