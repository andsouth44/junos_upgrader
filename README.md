## junos_upgrader

### Description

junos_upgrader is:

* An application for upgrading the JunOS operating system on Juniper routers and switches
* A framework, designed to be modular and extensible, to enable users to easily develop their own upgrade code
* Extends the Juniper PyEZ Python library 

junos_upgrader has 3 main parts:

* RPC Caller module - a repository of methods to call PyEZ RPCs.
* RPC Processor module - a repository of methods that call RPCs from the RPC Caller module and process the RPC call responses as required.
* Upgraders - a set of upgraders for different purposes, e.g. dual RE device processor, single RE device processor etc. Each upgrader runs a series of RPC Processor calls to achieve the required upgrade steps for the device being upgraded.

### How to use junos_upgrader

* Clone the repo
* Develop a new Upgrader module or pick an existing Upgrader module that matches your requirements
* Populate the input file
* Run the upgrader from CLI - "python3 upgrader_name"

Each upgrader should include the following flags:

* --dryrun or -d   - runs the upgrader pre-checks only
* --force or -f    - runs the full upgrader despite any errors in the prechecks
* --debug or -g    - runs the upgrader with added debug output - for development only

### Contributing

Contributors can add functionality to the application: 
* If RPC calls are missing they can be added to the RPC Caller module.
* If different processing of an RPC response is required it can be added to the RPC Processor module.
* If a new Upgrader is required it can be added to the 'upgraders' folder.
* All additions must closely follow the structure and style of existing code.

To contribute, please follow normal Git work flow best practices, i.e. fork the repo, create your own dev branch, add you code, commit, issue a pull request

### Tests

All code should have appropriate unit tests in the 'tests' folder.

### Prerequisites
* See requirements.txt

### Author and License

andsouth44@gmail.com

junos_upgrader is released under the [MIT License] (License.txt)

