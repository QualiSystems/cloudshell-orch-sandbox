@echo off
python -m pip install qpm --no-cache-dir --upgrade
copy version.txt cloudshell-orch-sandbox/version.txt
python -m qpm pack --package_name SandboxOrchestration
