# cloudshell-orch-sandbox

[![Coverage Status](https://coveralls.io/repos/github/QualiSystemsLab/cloudshell-orch-sandbox/badge.svg?branch=develop)](https://coveralls.io/github/QualiSystemsLab/cloudshell-orch-sandbox?branch=develop) [![Build Status](https://travis-ci.org/QualiSystemsLab/cloudshell-orch-sandbox.svg?branch=develop)](https://travis-ci.org/QualiSystemsLab/cloudshell-orch-sandbox)

Package for sandbox orchestration script functions

## Overview
The orchestration package should bring an out-of-the-box solution for our customer’s common use cases:
-	Setting up the sandbox upon reservation
-	Tearing down a sandbox
-	Save a snapshot of a sandbox

### Setup
During the setup process the script will iterate over the resources and prepare them for the reservation.
-	For each networking device:
    -	Power up
    -   Perform health check (if exists)
    -	Load firmware (optional)
    -	Load configuration (optional)
    -	Re-run health check (if exists)
-	VMs (when represented by Apps Deployment)
    -	Deploy apps
    -	Power on VM
-	Activate all routes and connectors

### Teardown
During the teardown process the script will wipe the configuration from the networking devices and delete VMs bringing them back into “ready for use” state.
-	For each networking device:
    -	Perform health check (if exists)
    -	Load firmware (optional)
    -	Load configuration (optiona)
    -	Re-run health check (if exists)
-	VMs
    -	Delete/Power off VM
-	Disconnect routes and connectors

### Snapshot
The user can save a snapshot of the sandbox. In the background, the script will save the sandbox as a new blueprint, and
the current configuration of the devices and VMs will be saved for future use (reserving this saved blueprint will
restore the configuration on the resources and the VM snapshots).
-	Save the sandbox as a blueprint, add to blueprint category "Snapshots"
-	Save all the configuration files of the devices on the storage server (e.g. FTP server)
-   REQUIRES
    a) root folder "Snapshots" created in Resource Manager
    b) Create a blueprint category "Snapshots"
    c) On ftp storage, create ftproot/CloudShell/Snapshots
