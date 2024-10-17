# Scope
This module is designed to upgrade the JunOS on MX series routers with dual REs and redundancy features enabled.

# Prerequisites
In addition to repository prerequisites, this upgrader requires:
* Independent IP connectivity to both REs

# How to Use

## Clone the Repository
Create a clone of the repo on your server or VM.

## Amend Input Parameters

Amend the input files; TEST_PARAMS.json and USER_PARAMS.json in:

`junos_upgrader/src/junos_upgrader/upgraders/dual_re_upgrader/inputs` for your environment.

## Amend Redundancy Config Files

Amend the config files; activate_redundancy.txt and deactivate_redundancy.txt in:

`junos_upgrader/src/junos_upgrader/upgraders/dual_re_upgrader/inputs` for your environment.

These files are used to deactivate redundancy features before the upgrade starts,
and re-activate the redundancy features when the upgrade has completed.

## Run the Upgrader

The upgrader can be run with the following flags:

* no flags         - attempts to run the upgrader to completion but stops if there are any pre-check errors
* --dryrun or -d   - runs the upgrader pre-checks only
* --force or -f    - attempts to run the upgrader to completion despite any errors in the prechecks
* --debug or -g    - attempts to run the upgrader to completion with added debug output - for development only
         
# Upgrader Steps
This upgrader completes the following steps:

* Saves the pre-upgrade config
* Verifies no chassis alarms
* Verifies re0 is master
* Verifies re0 memory utilization is within limits
* Verifies re0 CPU utilization is within limits
* Verifies protocol replication is complete for all configured protocols
* Verifies PIC status is OK for all PICs
* Verifies current/running JunOS on re0 
* Verifies re0 model
* Verifies proposed JunOS package is available on re0
* Verifies number of SSD on re0
* Verifies minimum number of ISIS adjacencies
* Creates backups of re0 and re1 config files
* Saves chassis hardware info
* Saves subscriber info
* Saves ISIS adjacency info
* Saves BGP summary
* Saves interface state
* Saves LDP adjacency info
* Saves protocol replication info
* Saves BFD session info
* Saves PIC info
* Saves chassis alarms
* Saves L2 circuit info
* Saves BGP route summary
* Verifies re1 status
* Verifies re1 memory utilization is within limits
* Verifies re1 CPU utilization is within limits
* Verifies current/running JunOS on re1
* Verifies re1 model
* Verifies proposed JunOS package is available on re1
* Verifies number of SSD on re1
* Verifies all pre-checks have passed - proceeds if ok, stops and reports errors if not
* If pre-checks are ok:
* Deactivates redundancy features
* Creates rescue config on re1
* Installs new JunOS on re1 backup partition
* Reboots re1
* Installs new JunOS on re1 primary partition
* Reboots re1
* Verifies new JunOS is on both partitions on re1
* Validates new JunOS on re1
* Verifies new JunOS is running on re1
* Switches RE mastership to re1
* Verifies re1 is master
* Creates rescue config on re0
* Installs new JunOS on re0 backup partition
* Reboots re0
* Installs new JunOS on re0 primary partition
* Reboots re0
* Verifies new JunOS is on both partitions on re0
* Validates new JunOS on re0
* Verifies new JunOS is running on re0
* Switches RE mastership to re0
* Verifies re0 is master
* Re-activates redundancy features
* Verifies redundancy features are working
* Verifies no chassis alarms
* Verifies minimum number of ISIS adjacencies
* Saves chassis hardware info
* Saves subscriber 
* Saves ISIS adjacency info
* Saves BGP neighbor info
* Saves interface state info
* Saves LDP adjacency info
* Saves protocol replication state info
* Saves BFD session info
* Saves PIC status info
* Saves cahssis alarm info
* Saves L2 circuit info
* Saves BGP route summary
* Saves post-upgarde config
* Compares pre-and-post config and displays any differences
* Compares pre-and-post state info and displays any differences
