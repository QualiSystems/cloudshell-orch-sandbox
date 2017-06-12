@echo off
Path = %Path%;C:\Python27
echo %Path%
python.exe -m pip install qpm --no-cache-dir --upgrade
copy version.txt SandboxOrchestrationPackage/version.txt /Y
python.exe -m qpm pack --package_name SandboxOrchestration
