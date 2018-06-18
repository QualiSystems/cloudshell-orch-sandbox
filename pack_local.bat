@echo off
python -m pip install qpm --no-cache-dir --upgrade
copy version.txt SandboxOrchestrationPackage/version.txt /Y
xcopy .\cloudshell-orch-core\* SandboxOrchestration\environment_scripts\env_setup\ /y /s
xcopy .\cloudshell-orch-core\* SandboxOrchestration\environment_scripts\env_teardown\ /y /s
xcopy .\cloudshell-orch-core\* SandboxOrchestration\environment_scripts\env_restore\ /y /s
xcopy .\cloudshell-orch-core\* SandboxOrchestration\environment_scripts\env_save\ /y /s
python -m qpm pack --package_name SandboxOrchestration
