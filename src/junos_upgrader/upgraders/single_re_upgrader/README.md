# Scope
This module is designed to upgrade the JunOS on Juniper routers and switches with a single routing engine.

# How to Use

## Clone the Repository
Create a clone of the repo on your server or VM.

## Amend Input Parameters

Amend the input files; TEST_PARAMS.json and USER_PARAMS.json in:

`junos_upgrader/src/junos_upgrader/upgraders/single_re_upgrader/inputs` for your environment.


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
* Verifies re memory utilization is within limits
* Verifies re CPU utilization is within limits
* Verifies PIC status is OK for all PICs
* Verifies current/running JunOS on re
* Verifies re0 model
* Verifies proposed JunOS package is available on re0
* Verifies number of SSD on re0
* Verifies minimum number of ISIS adjacencies
* Creates backup of re config file
* Saves chassis hardware info
* Saves subscriber info
* Saves ISIS adjacency info
* Saves BGP summary
* Saves interface state
* Saves LDP adjacency info
* Saves BFD session info
* Saves PIC info
* Saves chassis alarms
* Saves L2 circuit info
* Saves BGP route summary
* Verifies all pre-checks have passed - proceeds if ok, stops and reports errors if not
* If pre-checks are ok:
* Deactivates redundancy features
* Creates rescue config on re
* Installs new JunOS on re backup partition
* Reboots re
* Installs new JunOS on re primary partition
* Reboots re
* Verifies new JunOS is on both partitions on re
* Validates new JunOS on re
* Verifies new JunOS is running on re
* Verifies no chassis alarms
* Verifies minimum number of ISIS adjacencies
* Saves chassis hardware info
* Saves subscriber 
* Saves ISIS adjacency info
* Saves BGP neighbor info
* Saves interface state info
* Saves LDP adjacency info
* Saves BFD session info
* Saves PIC status info
* Saves chassis alarm info
* Saves L2 circuit info
* Saves BGP route summary
* Saves post-upgarde config
* Compares pre-and-post config and displays any differences
* Compares pre-and-post state info and displays any differences
