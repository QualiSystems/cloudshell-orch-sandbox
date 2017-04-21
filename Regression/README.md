
## Overview
The regression repository contains packages of blueprints that can be imported into .DO and used for regression tests
A dummy router driver was created to simulate the behavior of a network device
The infra package contains infrastructure resources used by the orchestration e.g FTP resource,vCenter...
Other packages contain different use cases for the orchestration and there is a description in blueprint's description

### Dummy router
This drivers is used for simulating a network device. On top of the standard functionality offered by a networking device driver, the following methods were added to influence on the expected behavior of the driver:
-	Set health status
    Sets the returned health status
    -	Status - The health status passed/ failed
-   Set firmware data
    Sets firmware version and success status
    -	Version – Version the driver will return in get version
    -	Will load fail? - Will load firmware fail true/false
-	Set saved file name
    Sets the name of the saved file
    -	Filename - The name of the saved file.
-	Get version
    Return firmware version

### FTP resource
In the topologies offered for the regression tests, we are using Quali’s FTP server. A resource named ‘FTP’ was created and it’s holding the ip address, username and password to Quali’s FTP.
The configuration and images files are located under folder Cloudshell\configs
