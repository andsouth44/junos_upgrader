# junos_upgrader

## Description

junos_upgrader is a modular and extensible application/framework for upgrading the JunOS operating system on Juniper routers and switches

junos_upgrader has 3 main parts:

* rpc_caller module - a module containing a set of methods that run RPCs on the device. Each methods' name is based on the equivalent CLI command.
* rpc_processor module - a module containing a set of methods that call methods from the `rpc_caller` module and process the RPC call responses as required.
* upgraders - a folder containing a set of "upgraders" for different use cases. Initially, `junos_upgrader` has one `upgrader` (an upgrader for dual RE MX devices) but further `upgraders` will be added or contributed. Each `upgrader` calls a set of methods from the `rpc_processor` module to carry out the steps appropriate for the device being upgraded.

rpc_processor methods are formed by calling one or more methods from rpc_caller.
upgraders are formed by calling one or more methods from rpc_procesor.

# Prerequisites
A server or VM running Python>=3.6 with NETCONF connectivity to the device(s) being upgraded.

## How to Use
Please see the README file for each upgrader

## How to Develop your own Upgrader
* Create a new folder and file structure inside the `upgraders` folder by copying, re-naming and pasting the `upgrader_template` folder.
* Rename the upgrader_template file to `your_use_case_upgrader.py`.
* Add the method calls required for your use case to `your_use_case_upgrader.py`. Use the methods available in `rpc_processor.py` OR add your own new methods to `rpc_processor.py` if the appropriate methods are not available.
* If you have to add new methods to `rpc_processor.py`, those new methods can use methods available in `rpc_caller.py` OR you can add your own new methods to `rpc_caller.py` if the appropriate methods are not available.
* Add a test module with tests to the `tests` folder

## Contributing

To contribute, please follow https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project

## Author and License

andsouth44@gmail.com

junos_upgrader is released under the [MIT License] (License.txt)

