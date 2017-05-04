from cloudshell.sandbox.orchestration.sandbox_manager import SandboxManager
from cloudshell.sandbox.orchestration.default_setup_orchestrator import DefaultSetupWorkflow

sandbox = SandboxManager()

DefaultSetupWorkflow.extend(sandbox)

sandbox.execute()

