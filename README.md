## junos_upgrader

### Description

junos_upgrader is:

* An application for upgrading the JunOS operating system on Juniper routers and switches
* A framework, designed to be modular and extensible, to enable users to easily develop their own upgrade code
* Extends the Juniper PyEZ Python library 

junos_upgrader has 3 main parts:

* RPC Caller module - a repository of methods, based on cli commands, that call the equivalent PyEz RPCs.
* RPC Processor module - a repository of methods that call methods from the RPC Caller module and process the RPC call responses as required.
* Upgraders - a set of upgraders for different purposes, e.g. dual RE device processor, single RE device processor etc. Each upgrader runs a series of RPC Processor methods to achieve the required upgrade steps for the device being upgraded.

### How to use junos_upgrader

* Clone the repo
* Pick an existing Upgrader module that matches your requirements or develop a new Upgrader
* Populate the input files as appropriate
* Run the upgrader from CLI - "python3 upgrader_name"

Each upgrader should include the following flags:

* --dryrun or -d   - runs the upgrader pre-checks only
* --force or -f    - runs the full upgrader despite any errors in the prechecks
* --debug or -g    - runs the upgrader with added debug output - for development only

### Contributing

Contributors can add functionality to the application: 
* RPC calls can be added to the RPC Caller module.
* RPC response processors can be added to the RPC Processor module.
* If a new Upgrader is required it can be added to the 'upgraders' folder.
* Additions must closely follow the structure and style of existing code.

To contribute, please follow normal Git work flow best practices, i.e. fork the repo, create your own dev branch, add you code, commit, issue a pull request

### Tests

All code should have appropriate unit tests in the 'tests' folder.

### Prerequisites
* See requirements.txt

### Author and License

andsouth44@gmail.com

junos_upgrader is released under the [MIT License] (License.txt)

