"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import json
from pathlib import Path
import sys
import os
from lxml import etree
import logging


class TestUtils:
    class MockArgs:
        def __init__(self):
            self.debug = False
            self.dryrun = False
            self.force = False

    class MockConfig:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self, *args, **kwargs):
            return TestUtils.MockConfig()

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def load(self, *args, **kwargs):
            pass

        @staticmethod
        def commit(*args, **kwargs):
            return True

        def lock(self, *args, **kwargs):
            pass

        def unlock(self, *args, **kwargs):
            pass

        def rescue(self, *args, **kwargs):
            return True

        def __repr__(self):
            pass

    class MockEtreeResponse:
        def __init__(self, text):
            self.text = text

    class ShowConfigMockerSuccess:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        load2 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        config_files_to_be_returned = [load1, load2]
        config_idx = 0

        @classmethod
        def get_config(cls):
            config_files = cls.config_files_to_be_returned[cls.config_idx]
            cls.config_idx += 1
            return config_files

    class ShowConfigMockerWarnings:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        load2 = mock_file_load('rpc_responses/get_configuration_in_set_format_post_upgrade.xml')
        config_files_to_be_returned = [load1, load2]
        config_idx = 0

        @classmethod
        def get_config(cls):
            config_files = cls.config_files_to_be_returned[cls.config_idx]
            cls.config_idx += 1
            return config_files

    class ShowSubscribersMockerSuccess:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        first_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        second_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        subscribers_files_to_be_returned = [first_load, second_load]
        subscribers_idx = 0

        @classmethod
        def get_subscribers(cls):
            subscribers_files = cls.subscribers_files_to_be_returned[cls.subscribers_idx]
            cls.subscribers_idx += 1
            return subscribers_files

    class ShowSubscribersMockerWarnings:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        first_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        second_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml_post_upgrade.xml')
        subscribers_files_to_be_returned = [first_load, second_load]
        subscribers_idx = 0

        @classmethod
        def get_subscribers(cls):
            subscribers_files = cls.subscribers_files_to_be_returned[cls.subscribers_idx]
            cls.subscribers_idx += 1
            return subscribers_files

    class ShowJunosVersion:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_software_information_old.xml')
        load2 = mock_file_load('rpc_responses/get_software_information_old.xml')
        load3 = mock_file_load('rpc_responses/get_software_information_new.xml')
        load4 = mock_file_load('rpc_responses/get_software_information_new.xml')

        junos_version_to_be_returned = [load1, load2, load3, load4]
        version_idx = 0

        @classmethod
        def get_version(cls):
            version_files = cls.junos_version_to_be_returned[cls.version_idx]
            cls.version_idx += 1
            return version_files

    @staticmethod
    def create_mock_inputs_json_and_test_params_json():
        with open(Path(sys.path[0]).joinpath('inputs', 'USER_INPUTS.json')) as inputs:
            with open(Path(sys.path[0]).joinpath('inputs', 'TEST_PARAMS.json')) as test_params:
                return json.load(inputs), json.load(test_params)

    @staticmethod
    def create_mock_logger(cwd, logfile):
        cwd = os.path.dirname(os.path.abspath(__file__))
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(f'{cwd}/logs/{logfile}', mode='w')
        return formatter, file_handler, logger

    @staticmethod
    def do_nothing(*args, **kwargs):
        return

    @staticmethod
    def return_success(*args, **kwargs) -> bool:
        return True

    @staticmethod
    def set_device_connected(dev) -> None:
        dev.connected = True

    @staticmethod
    def load_test_file(file_name) -> dict:
        with open(Path(sys.path[0]).joinpath('resources', file_name)) as f:
            return json.load(f)

    @staticmethod
    def load_test_file_as_etree(file_name) -> etree.ElementTree:
        return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

    @staticmethod
    def load_test_file_as_element(file_name) -> etree.Element:
        """
        Some RPCs return a lxml.etree._Element instead of a lxml.etree.elementTree.
        An lxml.etree._Element is the root element of a lxml.etree.elementTree.
        This method returns the root element from a xml file.
        """
        element_tree = etree.parse(Path(sys.path[0]).joinpath('resources', file_name))
        return element_tree.getroot()

    @staticmethod
    def get_re_files(*args, **kwargs):
        return TestUtils.load_test_file('rpc_responses/get_re_files.json')

    @staticmethod
    def get_device_info_success(*args, **kwargs):
        if args[1].tag == 'get-chassis-inventory':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_hardware_as_xml.xml')
        if args[1].tag == 'get-configuration':
            return TestUtils.ShowConfigMockerSuccess.get_config()
        elif args[1].tag == 'get-route-engine-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info.xml')
        elif args[1].tag == 'get-alarm-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_alarm_information_none_as_xml.xml')
        elif args[1].tag == 'get-bgp-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bgp_peers_by_group.xml')
        elif args[1].tag == 'get-routing-task-replication-state':
            return TestUtils.load_test_file_as_element('rpc_responses/get_protocol_replication_state.xml')
        elif args[1].tag == 'get-pic-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_pic_info_as_xml.xml')
        elif args[1].tag == 'get-software-information':
            return TestUtils.ShowJunosVersion.get_version()
        elif args[1].tag == 'get-vmhost-version-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_vmhost_version.xml')
        elif args[1].tag == 'get-isis-adjacency-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_isis_adjacency_information.xml')
        elif args[1].tag == 'get-interface-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_interface_info_terse_as_xml.xml')
        elif args[1].tag == 'get-subscribers':
            return TestUtils.ShowSubscribersMockerSuccess.get_subscribers()
        elif args[1].tag == 'get-l2ckt-connection-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_l2_circuit_info_as_xml.xml')
        elif args[1].tag == 'get-ldp-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_ldp_session_info_as_xml.xml')
        elif args[1].tag == 'get-route-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_route_summary_as_xml.xml')
        elif args[1].tag == 'get-bfd-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bfd_session_info_as_xml.xml')
        elif args[1].tag == 'file-copy':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_configuration_in_set_format.xml')
        elif args[1].tag == 'request-vmhost-package-add':
            return TestUtils.do_nothing()
        elif args[1].tag == 'request-vmhost-reboot':
            return TestUtils.do_nothing()
        elif args[1].tag == 'request-vmhost-snapshot':
            return TestUtils.MockEtreeResponse('Software snapshot done')
        elif args[1].tag == 'request-vmhost-package-validate' and args[1].attrib == {'format': 'text'}:
            return TestUtils.load_test_file_as_etree('rpc_responses/request_vmhost_package_validate.xml')
        elif args[1].tag == 'request-chassis-routing-engine-switch':
            return TestUtils.load_test_file_as_etree('rpc_responses/request_re_switchover.xml')
        else:
            assert False

    @staticmethod
    def get_device_info_warnings(*args, **kwargs):
        if args[1].tag == 'get-chassis-inventory':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_hardware_as_xml.xml')
        if args[1].tag == 'get-configuration':
            return TestUtils.ShowConfigMockerWarnings.get_config()
        elif args[1].tag == 'get-route-engine-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info.xml')
        elif args[1].tag == 'get-alarm-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_alarm_information_none_as_xml.xml')
        elif args[1].tag == 'get-bgp-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bgp_peers_by_group.xml')
        elif args[1].tag == 'get-routing-task-replication-state':
            return TestUtils.load_test_file_as_element('rpc_responses/get_protocol_replication_state.xml')
        elif args[1].tag == 'get-pic-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_pic_info_as_xml.xml')
        elif args[1].tag == 'get-software-information':
            return TestUtils.ShowJunosVersion.get_version()
        elif args[1].tag == 'get-vmhost-version-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_vmhost_version.xml')
        elif args[1].tag == 'get-isis-adjacency-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_isis_adjacency_information.xml')
        elif args[1].tag == 'get-interface-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_interface_info_terse_as_xml.xml')
        elif args[1].tag == 'get-subscribers':
            return TestUtils.ShowSubscribersMockerWarnings.get_subscribers()
        elif args[1].tag == 'get-l2ckt-connection-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_l2_circuit_info_as_xml.xml')
        elif args[1].tag == 'get-ldp-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_ldp_session_info_as_xml.xml')
        elif args[1].tag == 'get-route-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_route_summary_as_xml.xml')
        elif args[1].tag == 'get-bfd-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bfd_session_info_as_xml.xml')
        elif args[1].tag == 'file-copy':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_configuration_in_set_format.xml')
        elif args[1].tag == 'request-vmhost-package-add':
            return TestUtils.do_nothing()
        elif args[1].tag == 'request-vmhost-reboot':
            return TestUtils.do_nothing()
        elif args[1].tag == 'request-vmhost-snapshot':
            return TestUtils.MockEtreeResponse('Software snapshot done')
        elif args[1].tag == 'request-vmhost-package-validate' and args[1].attrib == {'format': 'text'}:
            return TestUtils.load_test_file_as_etree('rpc_responses/request_vmhost_package_validate.xml')
        elif args[1].tag == 'request-chassis-routing-engine-switch':
            return TestUtils.load_test_file_as_etree('rpc_responses/request_re_switchover.xml')
        else:
            assert False